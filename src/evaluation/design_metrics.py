"""Metric cấu trúc cho Test Design: coverage requirement, trace completeness, đa dạng loại.

Không cần ground truth LLM — đo từ chính TestDesignResult (sanity/quality signal cho RQ).
"""
from __future__ import annotations

from src.models.test_case import TestDesignResult


def coverage_report(results: list[TestDesignResult], approved_requirement_ids: list[str]) -> dict:
    covered = {r.source_requirement_id for r in results if r.test_cases}
    all_case_ids = {tc.id for r in results for tc in r.test_cases}
    traced = {link.to_id for r in results for link in r.trace_links}
    types = sorted({tc.type.value for r in results for tc in r.test_cases})
    approved = set(approved_requirement_ids)

    return {
        "requirement_coverage": len(covered & approved) / len(approved) if approved else 0.0,
        "n_test_cases": sum(len(r.test_cases) for r in results),
        "trace_completeness": len(all_case_ids & traced) / len(all_case_ids) if all_case_ids else 1.0,
        "types_covered": types,
        "uncovered_requirements": sorted(approved - covered),
    }
