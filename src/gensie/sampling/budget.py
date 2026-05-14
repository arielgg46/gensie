from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Any, Sequence

from gensie.config import env_bool, env_float, env_int, env_optional_int


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class TrialBudgetConfig:
    """Per-task cap for how many self-consistency samples to draw."""

    max_trials: int = 12
    min_trials: int = 1
    dynamic_trials: bool = True
    token_budget: int = 32000
    token_budget_ratio: float = 0.85
    time_budget_s: float = 60.0
    time_budget_ratio: float = 0.85
    completion_token_safety_factor: float = 1.5
    time_safety_factor: float = 1.15
    chars_per_token: float = 4.0
    inter_trial_delay_s: float = 0.0


@dataclass(frozen=True)
class TrialBudgetEstimate:
    allowed_trials: int
    prompt_tokens_per_trial: int
    completion_tokens_per_trial: int
    seconds_per_trial: float
    allowed_by_tokens: int
    allowed_by_time: int
    token_budget_effective: int
    time_budget_effective_s: float


class TrialBudgetPlanner:
    """Estimate a per-task self-consistency sample count from observed usage."""

    def __init__(self, config: TrialBudgetConfig | None = None):
        self.config = config or TrialBudgetConfig()

    def estimate_tokens_from_text(self, text: str) -> int:
        chars_per_token = max(self.config.chars_per_token, 1.0)
        return max(1, math.ceil(len(text) / chars_per_token))

    def estimate_prompt_tokens(
        self,
        *,
        messages: Sequence[JsonDict],
        response_format: JsonDict,
    ) -> int:
        text = json.dumps(
            {"messages": messages, "response_format": response_format},
            ensure_ascii=False,
            sort_keys=True,
        )
        return self.estimate_tokens_from_text(text)

    def estimate(
        self,
        *,
        prompt_tokens: int | None,
        prompt_token_fallback: int,
        completion_token_samples: Sequence[int],
        trial_duration_samples_s: Sequence[float],
    ) -> TrialBudgetEstimate:
        cfg = self.config
        max_trials = max(cfg.max_trials, 1)
        min_trials = max(1, min(cfg.min_trials, max_trials))

        prompt_per_trial = max(prompt_tokens or prompt_token_fallback, 1)
        if completion_token_samples:
            completion_base = max(completion_token_samples)
        else:
            completion_base = max(1, math.ceil(prompt_per_trial * 0.15))
        completion_per_trial = max(
            1, math.ceil(completion_base * cfg.completion_token_safety_factor)
        )

        if trial_duration_samples_s:
            duration_base = max(trial_duration_samples_s)
        else:
            duration_base = 0.0
        duration_base = max(duration_base, cfg.inter_trial_delay_s)
        seconds_per_trial = max(0.001, duration_base * cfg.time_safety_factor)

        token_budget_effective = max(
            1, math.floor(cfg.token_budget * cfg.token_budget_ratio)
        )
        time_budget_effective_s = max(0.001, cfg.time_budget_s * cfg.time_budget_ratio)

        tokens_per_trial = prompt_per_trial + completion_per_trial
        allowed_by_tokens = max(1, token_budget_effective // tokens_per_trial)
        allowed_by_time = max(1, math.floor(time_budget_effective_s / seconds_per_trial))

        if cfg.dynamic_trials:
            allowed = min(max_trials, allowed_by_tokens, allowed_by_time)
            allowed = max(min_trials, allowed)
            allowed = min(allowed, max_trials)
        else:
            allowed = max_trials

        return TrialBudgetEstimate(
            allowed_trials=allowed,
            prompt_tokens_per_trial=prompt_per_trial,
            completion_tokens_per_trial=completion_per_trial,
            seconds_per_trial=seconds_per_trial,
            allowed_by_tokens=allowed_by_tokens,
            allowed_by_time=allowed_by_time,
            token_budget_effective=token_budget_effective,
            time_budget_effective_s=time_budget_effective_s,
        )


def build_trial_budget_config_from_env() -> TrialBudgetConfig:
    legacy_trials = env_optional_int("GENSIE_SC_TRIALS")
    default_max_trials = (
        legacy_trials if legacy_trials is not None else TrialBudgetConfig().max_trials
    )
    max_trials = env_int("GENSIE_SC_MAX_TRIALS", default_max_trials, minimum=1)
    min_trials = min(env_int("GENSIE_SC_MIN_TRIALS", 1, minimum=1), max_trials)
    return TrialBudgetConfig(
        max_trials=max_trials,
        min_trials=min_trials,
        dynamic_trials=env_bool("GENSIE_SC_DYNAMIC_TRIALS", True),
        token_budget=env_int("GENSIE_SC_TOKEN_BUDGET", 32000, minimum=1),
        token_budget_ratio=env_float(
            "GENSIE_SC_TOKEN_BUDGET_RATIO", 0.85, minimum=0.0
        ),
        time_budget_s=env_float("GENSIE_SC_TIME_BUDGET_S", 60.0, minimum=0.001),
        time_budget_ratio=env_float(
            "GENSIE_SC_TIME_BUDGET_RATIO", 0.85, minimum=0.0
        ),
        completion_token_safety_factor=env_float(
            "GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR", 1.5, minimum=1.0
        ),
        time_safety_factor=env_float(
            "GENSIE_SC_TIME_SAFETY_FACTOR", 1.15, minimum=1.0
        ),
        chars_per_token=env_float("GENSIE_SC_CHARS_PER_TOKEN", 4.0, minimum=1.0),
        inter_trial_delay_s=_openai_request_delay_s(),
    )


def _openai_request_delay_s() -> float:
    raw = os.getenv("OPENAI_REQUEST_DELAY_S")
    if raw is None:
        return 0.0
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0
