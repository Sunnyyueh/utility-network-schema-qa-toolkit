from un_schema_qa.engine import build_default_registry
from un_schema_qa.models import (
    DatasetSchema,
    DomainSpec,
    FieldMapping,
    FieldSchema,
    Finding,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import ValidationContext


def dataset(name: str, *fields: FieldSchema) -> DatasetSchema:
    return DatasetSchema(name=name, geometry_type="polyline", fields=fields)


def semantic_project(*field_mappings: FieldMapping) -> ProjectData:
    return project_with_fields(
        source_fields=(
            FieldSchema(name="status", data_type="text"),
            FieldSchema(name="owner", data_type="text", length=100),
            FieldSchema(name="elevation", data_type="double"),
        ),
        target_fields=(
            FieldSchema(name="lifecycle_status", data_type="text"),
            FieldSchema(name="owner", data_type="text", length=128),
            FieldSchema(name="elevation", data_type="double"),
        ),
        field_mappings=field_mappings,
    )


def project_with_fields(
    *,
    source_fields: tuple[FieldSchema, ...],
    target_fields: tuple[FieldSchema, ...],
    field_mappings: tuple[FieldMapping, ...],
    source_domains: tuple[DomainSpec, ...] = (),
    target_domains: tuple[DomainSpec, ...] = (),
) -> ProjectData:
    return ProjectData(
        name="field-semantics",
        source_datasets=(dataset("LegacyLine", *source_fields),),
        target_datasets=(dataset("WaterLine", *target_fields),),
        source_domains=source_domains,
        target_domains=target_domains,
        mappings=(
            MappingPair(
                mapping_id="semantic-main",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
                field_mappings=field_mappings,
            ),
        ),
    )


def semantic_codes(project: ProjectData) -> set[str]:
    return {item.code for item in semantic_findings(project)}


def semantic_findings(project: ProjectData) -> list[Finding]:
    validator = build_default_registry().get("field_semantics")
    assert validator is not None
    return validator.validate(ValidationContext(project=project))


def test_default_registry_contains_field_semantics_validator() -> None:
    validator = build_default_registry().get("field_semantics")

    assert validator is not None
    assert validator.required_inputs == (
        "mappings",
        "source_datasets",
        "target_datasets",
    )


def test_field_semantics_reports_unknown_role() -> None:
    project = semantic_project(
        FieldMapping(
            source_field="status",
            target_field="lifecycle_status",
            semantic_role="asset mood",
            field_rationale="Legacy description retained for review.",
        )
    )

    assert "FIELD_SEMANTIC_ROLE_UNKNOWN" in semantic_codes(project)


def test_field_semantics_normalizes_role_and_requires_rationale() -> None:
    project = semantic_project(
        FieldMapping(
            source_field="status",
            target_field="lifecycle_status",
            semantic_role="Lifecycle-Status",
        )
    )

    assert "FIELD_SEMANTIC_RATIONALE_MISSING" in semantic_codes(project)


def lifecycle_project(
    source_domain: str | None,
    target_domain: str | None,
) -> ProjectData:
    return project_with_fields(
        source_fields=(FieldSchema(name="status", data_type="text", domain=source_domain),),
        target_fields=(
            FieldSchema(
                name="lifecycle_status",
                data_type="text",
                domain=target_domain,
            ),
        ),
        field_mappings=(
            FieldMapping(
                source_field="status",
                target_field="lifecycle_status",
                semantic_role="lifecycle_status",
                field_rationale="Crosswalk legacy status codes to the target lifecycle.",
            ),
        ),
    )


def test_lifecycle_status_requires_source_and_target_domains() -> None:
    assert semantic_codes(lifecycle_project(None, None)) == {
        "FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING",
        "FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING",
    }


def test_lifecycle_status_reports_only_the_missing_domain_side() -> None:
    assert semantic_codes(lifecycle_project("LegacyLifecycle", None)) == {
        "FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING"
    }
    assert semantic_codes(lifecycle_project(None, "TargetLifecycle")) == {
        "FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING"
    }


def test_lifecycle_status_accepts_two_sided_domain_metadata() -> None:
    assert semantic_codes(lifecycle_project("LegacyLifecycle", "TargetLifecycle")) == set()


def owner_project(
    *,
    source_type: str = "text",
    target_type: str = "text",
    source_length: int | None = 100,
    target_length: int | None = 128,
    source_domain: str | None = None,
    target_domain: str | None = None,
    expression: str | None = None,
    field_rationale: str | None = "Normalize owner names for target stewardship.",
) -> ProjectData:
    return project_with_fields(
        source_fields=(
            FieldSchema(
                name="owner_name",
                data_type=source_type,
                length=source_length,
                domain=source_domain,
            ),
        ),
        target_fields=(
            FieldSchema(
                name="owner",
                data_type=target_type,
                length=target_length,
                domain=target_domain,
            ),
        ),
        field_mappings=(
            FieldMapping(
                source_field="owner_name",
                target_field="owner",
                semantic_role="owner",
                expression=expression,
                field_rationale=field_rationale,
            ),
        ),
    )


def test_owner_requires_text_source_and_target_fields() -> None:
    findings = semantic_findings(owner_project(source_type="integer", target_type="double"))
    invalid = [item for item in findings if item.code == "FIELD_OWNER_TYPE_INVALID"]

    assert len(invalid) == 2
    assert {item.details["side"] for item in invalid} == {"source", "target"}


def test_owner_reports_target_length_truncation_risk() -> None:
    assert "FIELD_OWNER_LENGTH_RISK" in semantic_codes(
        owner_project(source_length=100, target_length=50)
    )
    assert semantic_codes(owner_project(source_length=100, target_length=100)) == set()
    assert semantic_codes(owner_project(source_length=None, target_length=50)) == set()


def test_owner_requires_domains_on_both_sides_when_either_side_uses_one() -> None:
    assert semantic_codes(owner_project(source_domain="LegacyOwner")) == {
        "FIELD_OWNER_DOMAIN_ASYMMETRIC"
    }
    assert semantic_codes(owner_project(target_domain="TargetOwner")) == {
        "FIELD_OWNER_DOMAIN_ASYMMETRIC"
    }
    assert (
        semantic_codes(owner_project(source_domain="LegacyOwner", target_domain="TargetOwner"))
        == set()
    )


def test_owner_accepts_documented_expression_normalization() -> None:
    assert semantic_codes(owner_project(expression="UPPER(owner_name)")) == set()
