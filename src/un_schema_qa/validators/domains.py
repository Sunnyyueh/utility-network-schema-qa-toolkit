"""Coded-value domain and crosswalk validation."""

from __future__ import annotations

from un_schema_qa.models import DomainSpec, Finding, Severity

from .base import ValidationContext, finding


class DomainValidator:
    name = "domains"
    required_inputs = ("source_datasets", "target_datasets")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for scope, domains in (
            ("source", context.project.source_domains),
            ("target", context.project.target_domains),
        ):
            findings.extend(self._domain_definitions(scope, domains))
        findings.extend(self._field_domains(context))
        findings.extend(self._crosswalks(context))
        findings.extend(self._asset_codes(context))
        return findings

    def _domain_definitions(self, scope: str, domains: tuple[DomainSpec, ...]) -> list[Finding]:
        findings: list[Finding] = []
        seen_domains: set[str] = set()
        for domain in domains:
            domain_key = domain.name.casefold()
            if domain_key in seen_domains:
                findings.append(
                    finding(
                        "DOMAIN_DUPLICATE",
                        Severity.ERROR,
                        self.name,
                        f"Duplicate {scope} domain {domain.name!r}.",
                        "Keep one canonical definition for each domain.",
                        location=domain.location,
                        details={"domain": domain.name, "scope": scope},
                    )
                )
            seen_domains.add(domain_key)
            seen_codes: set[str] = set()
            descriptions: dict[str, str] = {}
            for value in domain.values:
                code_key = value.code.casefold()
                if code_key in seen_codes:
                    findings.append(
                        finding(
                            "DOMAIN_CODE_DUPLICATE",
                            Severity.ERROR,
                            self.name,
                            f"Domain {domain.name!r} repeats code {value.code!r}.",
                            "Keep one description and crosswalk target for each code.",
                            location=value.location,
                            details={"domain": domain.name, "code": value.code},
                        )
                    )
                seen_codes.add(code_key)
                description_key = value.description.casefold()
                existing = descriptions.get(description_key)
                if existing is not None and existing.casefold() != code_key:
                    findings.append(
                        finding(
                            "DOMAIN_DESCRIPTION_AMBIGUOUS",
                            Severity.WARNING,
                            self.name,
                            f"Domain {domain.name!r} uses description "
                            f"{value.description!r} for multiple codes.",
                            "Confirm whether the codes are distinct or consolidate them.",
                            location=value.location,
                            details={
                                "domain": domain.name,
                                "code": value.code,
                                "other_code": existing,
                            },
                        )
                    )
                descriptions.setdefault(description_key, value.code)
        return findings

    def _field_domains(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for scope, datasets in (
            ("source", context.project.source_datasets),
            ("target", context.project.target_datasets),
        ):
            lookup = (
                context.project.source_domain
                if scope == "source"
                else context.project.target_domain
            )
            for dataset in datasets:
                for schema_field in dataset.fields:
                    if not schema_field.domain:
                        continue
                    domain = lookup(schema_field.domain)
                    if domain is None:
                        findings.append(
                            finding(
                                "DOMAIN_MISSING",
                                Severity.ERROR,
                                self.name,
                                f"{scope.title()} field {schema_field.name!r} references "
                                f"unknown domain {schema_field.domain!r}.",
                                "Add the domain export or correct the field-domain reference.",
                                dataset=dataset.name,
                                field=schema_field.name,
                                location=schema_field.location,
                                details={"domain": schema_field.domain},
                            )
                        )
                    elif (
                        schema_field.default is not None
                        and domain.value(schema_field.default) is None
                    ):
                        findings.append(
                            finding(
                                "DOMAIN_DEFAULT_INVALID",
                                Severity.ERROR,
                                self.name,
                                f"Default {schema_field.default!r} is not a code in "
                                f"domain {domain.name!r}.",
                                "Use a coded value from the assigned domain.",
                                dataset=dataset.name,
                                field=schema_field.name,
                                location=schema_field.location,
                                details={"domain": domain.name},
                            )
                        )
        return findings

    def _crosswalks(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            source_dataset = context.project.source_dataset(mapping.source_dataset)
            target_dataset = context.project.target_dataset(mapping.target_dataset)
            if source_dataset is None or target_dataset is None:
                continue
            for field_mapping in mapping.field_mappings:
                if not field_mapping.source_field:
                    continue
                source_field = source_dataset.field(field_mapping.source_field)
                target_field = target_dataset.field(field_mapping.target_field)
                if (
                    source_field is None
                    or target_field is None
                    or not source_field.domain
                    or not target_field.domain
                ):
                    continue
                source_domain = context.project.source_domain(source_field.domain)
                target_domain = context.project.target_domain(target_field.domain)
                if source_domain is None or target_domain is None:
                    continue
                for value in source_domain.values:
                    if value.target_code:
                        if target_domain.value(value.target_code) is None:
                            findings.append(
                                finding(
                                    "DOMAIN_TARGET_CODE_UNKNOWN",
                                    Severity.ERROR,
                                    self.name,
                                    f"Source code {value.code!r} maps to unknown target "
                                    f"code {value.target_code!r}.",
                                    "Correct the crosswalk target or add the target code.",
                                    dataset=target_dataset.name,
                                    field=target_field.name,
                                    mapping_id=mapping.mapping_id,
                                    location=value.location,
                                    details={
                                        "source_domain": source_domain.name,
                                        "target_domain": target_domain.name,
                                    },
                                )
                            )
                    elif target_domain.value(value.code) is None:
                        findings.append(
                            finding(
                                "DOMAIN_VALUE_UNMAPPED",
                                Severity.ERROR,
                                self.name,
                                f"Source code {value.code!r} has no direct target value or "
                                "explicit crosswalk.",
                                "Add target_code to the source domain value or add a matching "
                                "target code.",
                                dataset=target_dataset.name,
                                field=target_field.name,
                                mapping_id=mapping.mapping_id,
                                location=value.location,
                                details={
                                    "source_domain": source_domain.name,
                                    "target_domain": target_domain.name,
                                },
                            )
                        )
        return findings

    def _asset_codes(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for asset in context.project.asset_types:
            dataset = context.project.target_dataset(asset.dataset)
            if dataset is None:
                continue
            checks = (
                (
                    dataset.asset_group_field,
                    asset.asset_group_code,
                    "DOMAIN_ASSET_GROUP_CODE_INVALID",
                ),
                (
                    dataset.asset_type_field,
                    asset.asset_type_code,
                    "DOMAIN_ASSET_TYPE_CODE_INVALID",
                ),
            )
            for field_name, code, finding_code in checks:
                schema_field = dataset.field(field_name) if field_name else None
                domain = (
                    context.project.target_domain(schema_field.domain)
                    if schema_field and schema_field.domain
                    else None
                )
                if code is not None and domain and domain.value(code) is None:
                    findings.append(
                        finding(
                            finding_code,
                            Severity.ERROR,
                            self.name,
                            f"Asset code {code!r} is not present in domain {domain.name!r}.",
                            "Correct the asset inventory code or target domain definition.",
                            dataset=dataset.name,
                            field=field_name,
                            location=asset.location,
                            details={"domain": domain.name, "code": code},
                        )
                    )
        return findings
