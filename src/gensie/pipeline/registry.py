from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator

from gensie.agent import PipelineInfo
from gensie.pipeline.specs import PipelineSpec


class PipelineRegistry:
    def __init__(self) -> None:
        self._specs: OrderedDict[str, PipelineSpec] = OrderedDict()

    def register(self, spec: PipelineSpec) -> PipelineSpec:
        if spec.name in self._specs:
            raise ValueError(f"pipeline already registered: {spec.name}")
        self._specs[spec.name] = spec
        return spec

    def get(self, name: str) -> PipelineSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"unknown pipeline: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self._specs)

    def pipeline_infos(self) -> list[PipelineInfo]:
        return [
            PipelineInfo(name=spec.name, description=spec.description)
            for spec in self._specs.values()
        ]

    def __contains__(self, name: object) -> bool:
        return name in self._specs

    def __iter__(self) -> Iterator[PipelineSpec]:
        return iter(self._specs.values())

    def __len__(self) -> int:
        return len(self._specs)
