import os
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict
from openai import OpenAI
from gensie.agent import GenSIEAgent, Participant, ParticipantInfo, PipelineInfo
from gensie.task import Task
from gensie.tracing import trace_step
from dotenv import load_dotenv
from logging import getLogger

load_dotenv()
logger = getLogger("gensie")


class BasicAgent(GenSIEAgent):
    """
    Reference implementation using OpenAI Structured Outputs.
    Configurable via environment variables:
    - OPENAI_BASE_URL: (Optional) Custom endpoint for local LLMs.
    - OPENAI_API_KEY: (Required) Your API key.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        """
        Executes the extraction using OpenAI's response_format for strict schema compliance.
        """
        prompt = task.get_input_prompt()
        messages = [
            {
                "role": "system",
                "content": "You are a precise data extraction agent.",
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "schema": task.target_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            # Call OpenAI with the task's JSON schema
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=str(e),
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
            raise

        # Parse the structured JSON response
        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            # Fallback for unexpected API errors
            return {"error": f"Failed to parse model response: {str(e)}"}
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}


class OfficialParticipant(Participant):
    """
    Standard entry point for the competition.
    Participants can configure up to 3 pipelines here.
    """

    def __init__(self):
        # Default pipeline using the reference BasicAgent
        self.pipelines = {
            "baseline": BasicAgent(),
            # "pipeline2": MyCustomAgent(arg1, arg2...),
            # "pipeline3": AnotherAgent(...),
        }

    def get_info(self) -> ParticipantInfo:
        return ParticipantInfo(
            team_name="GenSIE Baseline Team",
            institution="Official",
            pipelines=[
                PipelineInfo(
                    name="baseline",
                    description="Standard OpenAI agent using structured outputs.",
                ),
                # Add descriptions for your other pipelines here:
                # PipelineInfo(name="pipeline2", description="My advanced RAG agent"),
            ],
        )

    def get_agent(self, pipeline_name: str) -> GenSIEAgent:
        if pipeline_name not in self.pipelines:
            # Fallback to default if pipeline not found, or raise error
            return self.pipelines["baseline"]
        return self.pipelines[pipeline_name]
