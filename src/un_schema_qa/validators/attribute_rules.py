"""Attribute-rule dependency metadata validation."""

from __future__ import annotations

from un_schema_qa.models import AttributeRuleSpec, Finding, Severity

from .base import ValidationContext, finding

_RULE_TYPES = {"calculation", "constraint", "validation"}
_TRIGGERS = {"insert", "update", "delete"}


class AttributeRuleValidator:
    name: str = "attribute_rules"
    required_inputs: tuple[str, ...] = ("attribute_rules", "target_datasets")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[str] = set()
        for rule in context.project.attribute_rules:
            key = rule.name.casefold()
            if key in seen:
                findings.append(
                    finding(
                        "ATTR_RULE_DUPLICATE",
                        Severity.ERROR,
                        self.name,
                        f"Attribute rule name {rule.name!r} is duplicated.",
                        "Use a unique name for each declared rule.",
                        dataset=rule.dataset,
                        location=rule.location,
                    )
                )
            seen.add(key)
            findings.extend(self._rule(context, rule))
        return findings

    def _rule(self, context: ValidationContext, rule: AttributeRuleSpec) -> list[Finding]:
        findings: list[Finding] = []
        dataset = context.project.target_dataset(rule.dataset)
        if dataset is None:
            findings.append(
                finding(
                    "ATTR_RULE_DATASET_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Attribute rule {rule.name!r} references unknown dataset {rule.dataset!r}.",
                    "Correct the dataset name or add its target schema.",
                    dataset=rule.dataset,
                    location=rule.location,
                )
            )
        else:
            mapped_fields = {
                field_mapping.target_field.casefold()
                for mapping in context.project.mappings
                if mapping.enabled and mapping.target_dataset.casefold() == dataset.name.casefold()
                for field_mapping in mapping.field_mappings
            }
            for field_name in rule.required_fields:
                if dataset.field(field_name) is None:
                    findings.append(
                        finding(
                            "ATTR_RULE_FIELD_UNKNOWN",
                            Severity.ERROR,
                            self.name,
                            f"Rule {rule.name!r} requires unknown field {field_name!r}.",
                            "Correct the dependency or add the target field.",
                            dataset=dataset.name,
                            field=field_name,
                            location=rule.location,
                        )
                    )
                elif field_name.casefold() not in mapped_fields:
                    findings.append(
                        finding(
                            "ATTR_RULE_INPUT_UNMAPPED",
                            Severity.WARNING,
                            self.name,
                            f"Required rule input {field_name!r} is not populated by an "
                            "enabled mapping.",
                            "Map the field, provide a target default, or document readiness.",
                            dataset=dataset.name,
                            field=field_name,
                            location=rule.location,
                        )
                    )
        for domain_name in rule.domain_dependencies:
            if context.project.target_domain(domain_name) is None:
                findings.append(
                    finding(
                        "ATTR_RULE_DOMAIN_UNKNOWN",
                        Severity.ERROR,
                        self.name,
                        f"Rule {rule.name!r} depends on unknown domain {domain_name!r}.",
                        "Add the target domain definition or correct the dependency.",
                        dataset=rule.dataset,
                        location=rule.location,
                        details={"domain": domain_name},
                    )
                )
        if rule.rule_type.casefold() not in _RULE_TYPES:
            findings.append(
                finding(
                    "ATTR_RULE_TYPE_UNSUPPORTED",
                    Severity.ERROR,
                    self.name,
                    f"Rule {rule.name!r} uses unsupported type {rule.rule_type!r}.",
                    "Use calculation, constraint, or validation metadata.",
                    dataset=rule.dataset,
                    location=rule.location,
                )
            )
        invalid_triggers = sorted(
            {event for event in rule.triggering_events if event.casefold() not in _TRIGGERS},
            key=str.casefold,
        )
        if invalid_triggers:
            findings.append(
                finding(
                    "ATTR_RULE_TRIGGER_INVALID",
                    Severity.ERROR,
                    self.name,
                    f"Rule {rule.name!r} uses unsupported trigger(s): "
                    f"{', '.join(invalid_triggers)}.",
                    "Use insert, update, or delete trigger metadata.",
                    dataset=rule.dataset,
                    location=rule.location,
                )
            )
        if not rule.expression:
            findings.append(
                finding(
                    "ATTR_RULE_EXPRESSION_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"Rule {rule.name!r} has no expression for readiness review.",
                    "Provide the expression text; the toolkit records but does not execute it.",
                    dataset=rule.dataset,
                    location=rule.location,
                )
            )
        return findings
