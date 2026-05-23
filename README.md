# GenSIE Submission

This repository contains the GenSIE extraction system submitted for evaluation.
It exposes a FastAPI service compatible with the official GenSIE submission
interface and calls an OpenAI-compatible inference server supplied at runtime.

## Submitted Pipelines

The participant service exposes these pipelines:

- `mixed-extractors-self-consistency-rag`
- `enriched-schema-rag`
- `enriched-inline-reasoning-rag`

`mixed-extractors-self-consistency-rag` runs four RAG-backed extraction trials,
alternating enriched inline reasoning and enriched schema prompting, then
aggregates the outputs with schema-aware heuristic self-consistency.

`enriched-schema-rag` uses a Spanish enriched extraction prompt with a Pydantic
schema representation and retrieved few-shot examples.

`enriched-inline-reasoning-rag` uses top-level reasoning/value wrappers with a
reasoned Pydantic schema prompt and retrieved few-shot examples.

## Runtime Requirements

- Python 3.13+
- Docker, for containerized evaluation
- CPU-only local execution
- OpenAI-compatible chat-completions endpoint

The system uses local FSP RAG resources included in the repository:

- `src/gensie/fsp/resources/cases/`
- `data/fsp_index/`

No internet access is required at inference time apart from the configured
OpenAI-compatible inference endpoint.

## Environment Variables

The official evaluator provides the inference endpoint through:

```bash
OPENAI_BASE_URL="http://HOST:PORT/v1"
OPENAI_API_KEY="..."
```

The participant class defaults to:

```bash
PARTICIPANT_PATH="gensie.baseline.OfficialParticipant"
```

For a local provider available at `10.6.125.216:8080`, use:

```bash
OPENAI_BASE_URL="http://10.6.125.216:8080/v1"
OPENAI_API_KEY="sk-dummy"
```

Optional local throttling can be controlled with:

```bash
OPENAI_REQUEST_DELAY_S="0"
```

## Run Locally

Install dependencies:

```bash
uv sync --group dev
```

Start the service:

```bash
uv run gensie serve --host 0.0.0.0 --port 8000
```

Inspect the exposed participant metadata:

```bash
curl http://localhost:8000/info
```

## Run With Docker

Build the image:

```bash
docker build -t gensie-submission .
```

Run the service:

```powershell
docker run --rm -p 8000:8000 `
  -e OPENAI_BASE_URL="http://10.6.125.216:8080/v1" `
  -e OPENAI_API_KEY="sk-dummy" `
  -e PARTICIPANT_PATH="gensie.baseline.OfficialParticipant" `
  gensie-submission serve --host 0.0.0.0 --port 8000
```

The provided `docker-compose.yml` can also be used during development:

```bash
docker compose up --build
```

## Local Evaluation

Run a small local check against a running service:

```bash
uv run gensie eval --data data/mini --url http://localhost:8000 --pipeline mixed-extractors-self-consistency-rag --model llama3.1-8b --limit 1 --auto-output-paths
```

Other submitted pipelines can be checked by changing `--pipeline`:

```bash
uv run gensie eval --data data/mini --url http://localhost:8000 --pipeline enriched-schema-rag --model llama3.1-8b --limit 1 --auto-output-paths
uv run gensie eval --data data/mini --url http://localhost:8000 --pipeline enriched-inline-reasoning-rag --model llama3.1-8b --limit 1 --auto-output-paths
```

Detailed traces and retrieval diagnostics are written under `local-results/`
when `--auto-output-paths` is enabled.

## Submission Notes

The container must be evaluated with the model name passed by the evaluator in
the `/run` request. The service forwards that model name to the configured
inference endpoint and returns a JSON object matching the task schema.

The repository is licensed under the MIT License.
