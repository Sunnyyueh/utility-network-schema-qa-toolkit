from un_schema_qa.models import (
    AttributeRuleSpec,
    DatasetSchema,
    DomainSpec,
    FieldMapping,
    FieldSchema,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import AttributeRuleValidator, ValidationContext


def rule(**updates: object) -> AttributeRuleSpec:
    values = {
        "name": "Set material label",
        "dataset": "WaterLine",
        "rule_type": "calculation",
        "triggering_events": ("insert", "update"),
        "required_fields": ("material",),
        "domain_dependencies": ("Material",),
        "expression": "return $feature.material",
    }
    values.update(updates)
    return AttributeRuleSpec.model_validate(values)


def project(
    *rules: AttributeRuleSpec, mapped_fields: tuple[str, ...] = ("material",)
) -> ProjectData:
    return ProjectData(
        name="attribute-rules",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(
                    FieldSchema(name="material", data_type="text", domain="Material"),
                    FieldSchema(name="diameter", data_type="double"),
                ),
            ),
        ),
        target_domains=(DomainSpec(name="Material"),),
        mappings=(
            MappingPair(
                mapping_id="water-main",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
                field_mappings=tuple(
                    FieldMapping(source_field=name, target_field=name) for name in mapped_fields
                ),
            ),
        ),
        attribute_rules=rules,
    )


def codes(data: ProjectData) -> set[str]:
    return {
        item.code for item in AttributeRuleValidator().validate(ValidationContext(project=data))
    }


def test_attribute_rule_reports_unknown_dataset_and_fields() -> None:
    unknown_dataset = rule(dataset="MissingDataset")
    unknown_field = rule(required_fields=("missing",))

    assert "ATTR_RULE_DATASET_UNKNOWN" in codes(project(unknown_dataset))
    assert "ATTR_RULE_FIELD_UNKNOWN" in codes(project(unknown_field))


def test_attribute_rule_reports_unmapped_required_input() -> None:
    assert "ATTR_RULE_INPUT_UNMAPPED" in codes(
        project(rule(required_fields=("diameter",)), mapped_fields=("material",))
    )


def test_attribute_rule_reports_unknown_domain_dependency() -> None:
    assert "ATTR_RULE_DOMAIN_UNKNOWN" in codes(
        project(rule(domain_dependencies=("MissingDomain",)))
    )


def test_attribute_rule_reports_invalid_type_trigger_and_missing_expression() -> None:
    invalid = rule(
        rule_type="automatic",
        triggering_events=("insert", "publish"),
        expression=None,
    )

    assert {
        "ATTR_RULE_TYPE_UNSUPPORTED",
        "ATTR_RULE_TRIGGER_INVALID",
        "ATTR_RULE_EXPRESSION_MISSING",
    } <= codes(project(invalid))


def test_attribute_rule_reports_duplicate_names() -> None:
    first = rule()

    assert "ATTR_RULE_DUPLICATE" in codes(project(first, first.model_copy()))


def test_attribute_rule_accepts_ready_metadata() -> None:
    assert AttributeRuleValidator().validate(ValidationContext(project=project(rule()))) == []
