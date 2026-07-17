"""Asset group/type inventory and engineering-rationale validation."""

from __future__ import annotations

from un_schema_qa.models import Finding, MappingPair, Severity
from un_schema_qa.rules import evaluate_engineering_rules

from .base import ValidationContext, finding


class AssetClassificationValidator:
    name = "asset_classification"
    required_inputs = ("mappings", "asset_types")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            findings.extend(self._mapping(context, mapping))
        return findings

    def _mapping(self, context: ValidationContext, mapping: MappingPair) -> list[Finding]:
        findings: list[Finding] = []
        if bool(mapping.asset_group) != bool(mapping.asset_type):
            findings.append(
                finding(
                    "ASSET_CLASSIFICATION_INCOMPLETE",
                    Severity.ERROR,
                    self.name,
                    f"Mapping {mapping.mapping_id!r} provides only part of its target "
                    "asset classification.",
                    "Provide both target asset group and target asset type.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if mapping.asset_group and mapping.asset_type:
            if (
                context.project.asset_type(
                    mapping.target_dataset, mapping.asset_group, mapping.asset_type
                )
                is None
            ):
                findings.append(
                    finding(
                        "ASSET_TYPE_UNKNOWN",
                        Severity.ERROR,
                        self.name,
                        f"Target classification {mapping.asset_group!r} / "
                        f"{mapping.asset_type!r} is not in the asset inventory.",
                        "Correct the classification or add the reviewed target inventory row.",
                        dataset=mapping.target_dataset,
                        mapping_id=mapping.mapping_id,
                        location=mapping.location,
                    )
                )
            if not mapping.rationale:
                findings.append(
                    finding(
                        "ASSET_RATIONALE_MISSING",
                        Severity.WARNING,
                        self.name,
                        f"Mapping {mapping.mapping_id!r} has no classification rationale.",
                        "Document the engineering attributes supporting the selected type.",
                        dataset=mapping.target_dataset,
                        mapping_id=mapping.mapping_id,
                        location=mapping.location,
                    )
                )
        if context.project.engineering_rules:
            findings.extend(self._rules(context, mapping))
        return findings

    def _rules(self, context: ValidationContext, mapping: MappingPair) -> list[Finding]:
        if mapping.engineering_context is None:
            return [
                finding(
                    "ASSET_ENGINEERING_CONTEXT_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"Mapping {mapping.mapping_id!r} has no engineering context for rules.",
                    "Provide relevant facility, hydraulic, geometry, material, and lifecycle data.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            ]
        evaluation = evaluate_engineering_rules(
            mapping.engineering_context, context.project.engineering_rules
        )
        details = {
            "matched_rules": [rule.rule_id for rule in evaluation.matches],
            "explanations": list(evaluation.explanations),
            "missing_attributes": list(evaluation.missing_attributes),
        }
        if evaluation.status == "no_match":
            return [
                finding(
                    "ASSET_RULE_NO_MATCH",
                    Severity.WARNING,
                    self.name,
                    f"No engineering rule matched mapping {mapping.mapping_id!r}.",
                    "Review missing attributes and document the classification manually.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                    details=details,
                )
            ]
        findings: list[Finding] = []
        if evaluation.status == "conflicting_matches":
            findings.append(
                finding(
                    "ASSET_RULE_CONFLICT",
                    Severity.ERROR,
                    self.name,
                    f"Engineering rules suggest conflicting targets for mapping "
                    f"{mapping.mapping_id!r}.",
                    "Resolve rule precedence or obtain engineering review before loading.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                    details={
                        **details,
                        "conflicting_targets": list(evaluation.conflicting_targets),
                    },
                )
            )
        else:
            findings.append(
                finding(
                    "ASSET_RULE_MATCH",
                    Severity.INFO,
                    self.name,
                    f"Engineering rules produced {len(evaluation.matches)} explained "
                    f"match(es) for mapping {mapping.mapping_id!r}.",
                    "Retain the rationale and complete engineering review as required.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                    details=details,
                )
            )
        selected = (
            (mapping.asset_group.casefold(), mapping.asset_type.casefold())
            if mapping.asset_group and mapping.asset_type
            else None
        )
        matched_targets = {
            (rule.target_asset_group.casefold(), rule.target_asset_type.casefold())
            for rule in evaluation.matches
        }
        if selected is not None and selected not in matched_targets:
            findings.append(
                finding(
                    "ASSET_RULE_DISAGREEMENT",
                    Severity.WARNING,
                    self.name,
                    f"Selected asset classification for mapping {mapping.mapping_id!r} "
                    "differs from every matched engineering rule.",
                    "Document the exception or revise the mapping/rule with engineering review.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                    details=details,
                )
            )
        return findings
