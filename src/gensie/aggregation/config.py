from __future__ import annotations

import os
from dataclasses import dataclass

from gensie.config import env_bool, env_float, env_int


@dataclass(frozen=True)
class SelfConsistencyConfig:
    """Tunable knobs for schema-aware self-consistency."""

    scalar_string_threshold: float = 0.78
    array_string_threshold: float = 0.78
    object_item_threshold: float = 0.62
    null_wins_ties: bool = False
    simple_item_support_floor: int = 2
    object_item_support_floor: int = 2
    support_ratios: tuple[float, ...] = (0.40, 0.50, 0.60)
    include_greedy_array_candidate: bool = True
    include_threshold_array_candidates: bool = True
    include_original_array_candidates: bool = False
    optional_property_support_ratio: float = 0.50
    intra_trial_dedupe_threshold: float = 0.96
    use_identity_clustering: bool = True
    identity_min_score: float = 8.0
    identity_min_margin: float = 3.0
    identity_string_threshold: float = 0.62
    array_selector_mode: str = "recall_biased_mbr"
    recall_mbr_tolerance: float = 0.06


def build_self_consistency_config_from_env() -> SelfConsistencyConfig:
    return SelfConsistencyConfig(
        scalar_string_threshold=env_float(
            "GENSIE_SC_SCALAR_STRING_THRESHOLD", 0.78, minimum=0.0
        ),
        array_string_threshold=env_float(
            "GENSIE_SC_ARRAY_STRING_THRESHOLD", 0.78, minimum=0.0
        ),
        object_item_threshold=env_float(
            "GENSIE_SC_OBJECT_ITEM_THRESHOLD", 0.62, minimum=0.0
        ),
        simple_item_support_floor=env_int(
            "GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR", 2, minimum=1
        ),
        object_item_support_floor=env_int(
            "GENSIE_SC_OBJECT_ITEM_SUPPORT_FLOOR", 2, minimum=1
        ),
        optional_property_support_ratio=env_float(
            "GENSIE_SC_OPTIONAL_PROPERTY_SUPPORT_RATIO", 0.50, minimum=0.0
        ),
        intra_trial_dedupe_threshold=env_float(
            "GENSIE_SC_INTRA_TRIAL_DEDUPE_THRESHOLD", 0.96, minimum=0.0
        ),
        include_greedy_array_candidate=env_bool(
            "GENSIE_SC_INCLUDE_GREEDY_ARRAY_CANDIDATE", True
        ),
        include_threshold_array_candidates=env_bool(
            "GENSIE_SC_INCLUDE_THRESHOLD_ARRAY_CANDIDATES", True
        ),
        include_original_array_candidates=env_bool(
            "GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES", False
        ),
        use_identity_clustering=env_bool("GENSIE_SC_USE_IDENTITY_CLUSTERING", True),
        identity_min_score=env_float(
            "GENSIE_SC_IDENTITY_MIN_SCORE", 8.0, minimum=0.0
        ),
        identity_min_margin=env_float(
            "GENSIE_SC_IDENTITY_MIN_MARGIN", 3.0, minimum=0.0
        ),
        identity_string_threshold=env_float(
            "GENSIE_SC_IDENTITY_STRING_THRESHOLD", 0.62, minimum=0.0
        ),
        array_selector_mode=os.getenv("GENSIE_SC_ARRAY_SELECTOR", "recall_biased_mbr"),
        recall_mbr_tolerance=env_float(
            "GENSIE_SC_RECALL_MBR_TOLERANCE", 0.06, minimum=0.0
        ),
        null_wins_ties=env_bool("GENSIE_SC_NULL_WINS_TIES", False),
    )
