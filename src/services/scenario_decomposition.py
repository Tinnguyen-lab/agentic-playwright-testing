"""Deterministic scenario decomposition from approved requirement fields.

This deliberately does not ask an LLM to invent branches.  The main flow and
each explicitly documented alternative flow become independently traceable
scenario inputs for test design.
"""
from __future__ import annotations

from pydantic import BaseModel

from src.models.requirement import StructuredRequirement


class Scenario(BaseModel):
    id: str
    title: str
    flow: list[str]
    expected_result: str = ""


def decompose(requirement: StructuredRequirement) -> list[Scenario]:
    main = requirement.main_flow or [requirement.action]
    scenarios = [Scenario(id="SC-01", title="Luồng chính", flow=main,
                          expected_result=requirement.expected_outcome or "")]
    for index, alternative in enumerate(requirement.alternative_flows, start=2):
        scenarios.append(Scenario(id=f"SC-{index:02d}", title=f"Luồng thay thế {index - 1}",
                                  flow=[alternative], expected_result=""))
    return scenarios
