"""Declared Utility Network rule and terminal validation."""

from __future__ import annotations

from un_schema_qa.models import Finding, NetworkRuleSpec, Severity

from .base import ValidationContext, finding

_RULE_TYPES = {"connectivity", "containment", "structural_attachment"}


class NetworkRuleValidator:
    name: str = "network_rules"
    required_inputs: tuple[str, ...] = ("network_rules", "asset_types")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[tuple[str, ...]] = set()
        for rule in context.project.network_rules:
            key = self._key(rule)
            duplicate = key in seen
            if duplicate:
                findings.append(
                    finding(
                        "NETWORK_RULE_DUPLICATE",
                        Severity.ERROR,
                        self.name,
                        "Duplicate network rule declaration.",
                        "Remove the duplicate rule row.",
                        dataset=rule.from_dataset,
                        location=rule.location,
                    )
                )
            if rule.rule_type.casefold() == "connectivity":
                reverse_key = (
                    rule.rule_type.casefold(),
                    *self._to_endpoint(rule),
                    *self._from_endpoint(rule),
                )
                if not duplicate and reverse_key in seen:
                    findings.append(
                        finding(
                            "NETWORK_RULE_REVERSE_DUPLICATE",
                            Severity.WARNING,
                            self.name,
                            "Connectivity rule repeats an existing endpoint pair in reverse.",
                            "Keep one reviewed direction unless both directions are intentional.",
                            dataset=rule.from_dataset,
                            location=rule.location,
                        )
                    )
            seen.add(key)
            findings.extend(self._rule(context, rule))
        findings.extend(self._coverage(context))
        return findings

    @staticmethod
    def _from_endpoint(rule: NetworkRuleSpec) -> tuple[str, ...]:
        return (
            rule.from_dataset.casefold(),
            rule.from_asset_group.casefold(),
            rule.from_asset_type.casefold(),
            (rule.from_terminal or "").casefold(),
        )

    @staticmethod
    def _to_endpoint(rule: NetworkRuleSpec) -> tuple[str, ...]:
        return (
            rule.to_dataset.casefold(),
            rule.to_asset_group.casefold(),
            rule.to_asset_type.casefold(),
            (rule.to_terminal or "").casefold(),
        )

    def _key(self, rule: NetworkRuleSpec) -> tuple[str, ...]:
        return (
            rule.rule_type.casefold(),
            *self._from_endpoint(rule),
            *self._to_endpoint(rule),
        )

    def _rule(self, context: ValidationContext, rule: NetworkRuleSpec) -> list[Finding]:
        findings: list[Finding] = []
        if rule.rule_type.casefold() not in _RULE_TYPES:
            findings.append(
                finding(
                    "NETWORK_RULE_TYPE_UNSUPPORTED",
                    Severity.ERROR,
                    self.name,
                    f"Unsupported network rule type {rule.rule_type!r}.",
                    "Use connectivity, containment, or structural_attachment.",
                    dataset=rule.from_dataset,
                    location=rule.location,
                )
            )
        if self._from_endpoint(rule) == self._to_endpoint(rule):
            findings.append(
                finding(
                    "NETWORK_RULE_SELF_REFERENCE",
                    Severity.ERROR,
                    self.name,
                    "Network rule connects an asset classification to itself.",
                    "Correct one endpoint or document the intended distinct terminal relation.",
                    dataset=rule.from_dataset,
                    location=rule.location,
                )
            )
        endpoints = (
            (
                "from",
                rule.from_dataset,
                rule.from_asset_group,
                rule.from_asset_type,
                rule.from_terminal,
            ),
            (
                "to",
                rule.to_dataset,
                rule.to_asset_group,
                rule.to_asset_type,
                rule.to_terminal,
            ),
        )
        for label, dataset, asset_group, asset_type, terminal in endpoints:
            asset = context.project.asset_type(dataset, asset_group, asset_type)
            if asset is None:
                findings.append(
                    finding(
                        "NETWORK_RULE_ASSET_UNKNOWN",
                        Severity.ERROR,
                        self.name,
                        f"{label.title()} endpoint {dataset} / {asset_group} / "
                        f"{asset_type} is not in the asset inventory.",
                        "Correct the endpoint or add the reviewed asset inventory row.",
                        dataset=dataset,
                        location=rule.location,
                    )
                )
            if terminal and not self._terminal_exists(
                context, dataset, asset_group, asset_type, terminal
            ):
                findings.append(
                    finding(
                        "NETWORK_RULE_TERMINAL_UNKNOWN",
                        Severity.ERROR,
                        self.name,
                        f"{label.title()} terminal {terminal!r} is not declared for "
                        f"{dataset} / {asset_group} / {asset_type}.",
                        "Correct the terminal or add it to the terminal inventory.",
                        dataset=dataset,
                        location=rule.location,
                        details={"terminal": terminal},
                    )
                )
        return findings

    @staticmethod
    def _terminal_exists(
        context: ValidationContext,
        dataset: str,
        asset_group: str,
        asset_type: str,
        terminal: str,
    ) -> bool:
        key = tuple(value.casefold() for value in (dataset, asset_group, asset_type, terminal))
        if any(
            tuple(
                value.casefold()
                for value in (
                    item.dataset,
                    item.asset_group,
                    item.asset_type,
                    item.terminal,
                )
            )
            == key
            for item in context.project.terminals
        ):
            return True
        asset = context.project.asset_type(dataset, asset_group, asset_type)
        return bool(
            asset and terminal.casefold() in {value.casefold() for value in asset.terminals}
        )

    def _coverage(self, context: ValidationContext) -> list[Finding]:
        if not context.project.network_rules:
            return []
        covered = {
            endpoint[:3]
            for rule in context.project.network_rules
            for endpoint in (self._from_endpoint(rule), self._to_endpoint(rule))
        }
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            if not mapping.asset_group or not mapping.asset_type:
                continue
            key = (
                mapping.target_dataset.casefold(),
                mapping.asset_group.casefold(),
                mapping.asset_type.casefold(),
            )
            if key not in covered:
                findings.append(
                    finding(
                        "NETWORK_RULE_MAPPING_UNCOVERED",
                        Severity.WARNING,
                        self.name,
                        f"Mapped classification {mapping.asset_group!r} / "
                        f"{mapping.asset_type!r} does not appear in any network rule.",
                        "Confirm that rule coverage is complete or document the exception.",
                        dataset=mapping.target_dataset,
                        mapping_id=mapping.mapping_id,
                        location=mapping.location,
                    )
                )
        return findings
