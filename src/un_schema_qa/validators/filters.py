"""Definition Query documentation and partition validation."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from un_schema_qa.filters import FilterAnalysis, analyze_filter, possible_overlap
from un_schema_qa.models import Finding, MappingPair, Severity

from .base import ValidationContext, finding


class FilterValidator:
    name: str = "filters"
    required_inputs: tuple[str, ...] = ("mappings", "source_datasets")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        enabled = tuple(mapping for mapping in context.project.mappings if mapping.enabled)
        grouped: dict[str, list[MappingPair]] = defaultdict(list)
        analyses: dict[str, FilterAnalysis] = {}
        for mapping in enabled:
            grouped[mapping.source_dataset.casefold()].append(mapping)
            findings.extend(self._mapping(context, mapping))
            if mapping.definition_query:
                analyses[mapping.mapping_id.casefold()] = analyze_filter(mapping.definition_query)

        for mappings in grouped.values():
            if len(mappings) > 1:
                for mapping in mappings:
                    if not mapping.definition_query:
                        findings.append(
                            finding(
                                "FILTER_REQUIRED_FOR_PARTITION",
                                Severity.ERROR,
                                self.name,
                                f"Mapping {mapping.mapping_id!r} shares source "
                                f"{mapping.source_dataset!r} but has no filter.",
                                "Define a documented source-side filter for every partition.",
                                dataset=mapping.source_dataset,
                                mapping_id=mapping.mapping_id,
                                location=mapping.location,
                            )
                        )
                findings.extend(self._overlaps(mappings, analyses))
        return findings

    def _mapping(self, context: ValidationContext, mapping: MappingPair) -> list[Finding]:
        if not mapping.definition_query:
            return []
        findings: list[Finding] = []
        analysis = analyze_filter(mapping.definition_query)
        if analysis.errors:
            findings.append(
                finding(
                    "FILTER_SYNTAX_INVALID",
                    Severity.ERROR,
                    self.name,
                    f"Filter for mapping {mapping.mapping_id!r} is invalid: "
                    f"{'; '.join(analysis.errors)}",
                    "Correct the filter using the documented SQL-style subset.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                    details={"errors": list(analysis.errors)},
                )
            )
        source = context.project.source_dataset(mapping.source_dataset)
        if source:
            for identifier in analysis.identifiers:
                if source.field(identifier) is None:
                    findings.append(
                        finding(
                            "FILTER_FIELD_UNKNOWN",
                            Severity.ERROR,
                            self.name,
                            f"Filter references unknown source field {identifier!r}.",
                            "Correct the field name or add it to the source schema export.",
                            dataset=source.name,
                            field=identifier,
                            mapping_id=mapping.mapping_id,
                            location=mapping.location,
                        )
                    )
        if not mapping.purpose:
            findings.append(
                finding(
                    "FILTER_PURPOSE_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"Filter for mapping {mapping.mapping_id!r} has no documented purpose.",
                    "Describe the intended asset population and record scope.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if mapping.expected_count is None:
            findings.append(
                finding(
                    "FILTER_EXPECTED_COUNT_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"Filter for mapping {mapping.mapping_id!r} has no expected count.",
                    "Record an expected selection count or reviewed scope baseline.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if mapping.selected_count == 0:
            findings.append(
                finding(
                    "FILTER_EMPTY_SELECTION",
                    Severity.ERROR,
                    self.name,
                    f"Filter for mapping {mapping.mapping_id!r} selected no records.",
                    "Review the query, field values, and intended source population.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if (
            mapping.expected_count is not None
            and mapping.selected_count is not None
            and mapping.expected_count != mapping.selected_count
        ):
            findings.append(
                finding(
                    "FILTER_EXPECTED_SELECTED_MISMATCH",
                    Severity.WARNING,
                    self.name,
                    f"Expected {mapping.expected_count} records but selected "
                    f"{mapping.selected_count} for mapping {mapping.mapping_id!r}.",
                    "Review the expected baseline and filter result before loading.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if (
            mapping.selected_count is not None
            and mapping.loaded_count is not None
            and mapping.selected_count != mapping.loaded_count
        ):
            findings.append(
                finding(
                    "FILTER_SELECTED_LOADED_MISMATCH",
                    Severity.ERROR,
                    self.name,
                    f"Selected {mapping.selected_count} records but loaded "
                    f"{mapping.loaded_count} for mapping {mapping.mapping_id!r}.",
                    "Reconcile rejected, duplicated, or missing records in the load results.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        return findings

    def _overlaps(
        self, mappings: list[MappingPair], analyses: dict[str, FilterAnalysis]
    ) -> list[Finding]:
        findings: list[Finding] = []
        for left, right in combinations(mappings, 2):
            left_analysis = analyses.get(left.mapping_id.casefold())
            right_analysis = analyses.get(right.mapping_id.casefold())
            if not isinstance(left_analysis, FilterAnalysis) or not isinstance(
                right_analysis, FilterAnalysis
            ):
                continue
            if possible_overlap(left_analysis, right_analysis) is True:
                findings.append(
                    finding(
                        "FILTER_POSSIBLE_OVERLAP",
                        Severity.WARNING,
                        self.name,
                        f"Filters for mappings {left.mapping_id!r} and "
                        f"{right.mapping_id!r} may select the same source records.",
                        "Make partition predicates mutually exclusive or document "
                        "intentional reuse.",
                        dataset=left.source_dataset,
                        mapping_id=left.mapping_id,
                        location=left.location,
                        details={"other_mapping_id": right.mapping_id},
                    )
                )
        return findings
