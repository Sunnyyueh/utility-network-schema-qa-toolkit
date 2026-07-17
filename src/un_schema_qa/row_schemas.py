"""Logical columns accepted by canonical row converters."""

from __future__ import annotations

SCHEMA_COLUMNS = {
    "dataset": {"dataset", "dataset_name", "feature_class", "class_name", "source"},
    "geometry_type": {"geometry_type", "geometry", "shape_type"},
    "record_count": {"record_count", "feature_count", "count"},
    "field": {"field", "field_name", "name"},
    "data_type": {"data_type", "field_type", "type"},
    "nullable": {"nullable", "is_nullable", "allow_null"},
    "required": {"required", "is_required"},
    "length": {"length", "field_length"},
    "default": {"default", "default_value"},
    "domain": {"domain", "domain_name"},
    "alias": {"alias", "field_alias"},
    "subtype_field": {"subtype_field"},
    "asset_group_field": {"asset_group_field"},
    "asset_type_field": {"asset_type_field"},
}

MAPPING_COLUMNS = {
    "mapping_id": {"mapping_id", "mapping", "id"},
    "source_dataset": {"source_dataset", "source", "source_class"},
    "target_dataset": {"target_dataset", "target", "target_class"},
    "source_field": {"source_field", "sourcefield"},
    "target_field": {"target_field", "targetfield"},
    "expression": {"expression", "transform"},
    "lookup": {"lookup", "lookup_sheet"},
    "default": {"default", "lookup_default"},
    "definition_query": {"definition_query", "source_definition_query", "filter"},
    "purpose": {"purpose", "filter_purpose"},
    "expected_count": {"expected_count", "anticipated_count"},
    "selected_count": {"selected_count", "filtered_count"},
    "loaded_count": {"loaded_count", "target_loaded_count"},
    "asset_group": {"asset_group", "target_asset_group"},
    "asset_type": {"asset_type", "target_asset_type"},
    "rationale": {"rationale", "classification_rationale"},
    "enabled": {"enabled", "is_enabled"},
    "network_role": {"network_role", "facility_function"},
    "flow_regime": {"flow_regime", "operating_mode"},
    "material": {"material"},
    "lining": {"lining"},
    "coating": {"coating"},
    "nominal_diameter": {"nominal_diameter", "diameter"},
    "width": {"width"},
    "height": {"height"},
    "capacity": {"capacity"},
    "pressure_class": {"pressure_class", "pressure_rating"},
    "slope": {"slope"},
    "upstream_invert": {"upstream_invert", "from_invert"},
    "downstream_invert": {"downstream_invert", "to_invert"},
    "flow_direction": {"flow_direction"},
    "installation_method": {"installation_method"},
    "installation_date": {"installation_date", "install_date"},
    "lifecycle_status": {"lifecycle_status", "status"},
}

DOMAIN_COLUMNS = {
    "domain": {"domain", "domain_name", "name"},
    "code": {"code", "coded_value", "value"},
    "description": {"description", "label", "name"},
    "target_code": {"target_code", "mapped_code", "crosswalk_value"},
    "field_type": {"field_type", "data_type"},
}

ASSET_COLUMNS = {
    "dataset": {"dataset", "target", "feature_class"},
    "asset_group": {"asset_group", "asset_group_name", "subtype"},
    "asset_type": {"asset_type", "asset_type_name"},
    "asset_group_code": {"asset_group_code", "subtype_code"},
    "asset_type_code": {"asset_type_code"},
    "categories": {"categories", "network_categories"},
    "terminals": {"terminals", "terminal_configuration"},
}

DATA_REFERENCE_COLUMNS = {
    "source": {"source", "source_dataset"},
    "target": {"target", "target_dataset"},
    "mapping_workbook": {"mapping_workbook", "mappingworkbook"},
    "enabled": {"enabled"},
    "maintain_attachments": {"maintain_attachments", "maintainattachments"},
    "preserve_global_ids": {"preserve_global_ids", "preserveglobalids"},
    "definition_query": {"definition_query", "source_definition_query"},
    "mapping_id": {"mapping_id"},
}

ATTRIBUTE_RULE_COLUMNS = {
    "name": {"name", "rule_name"},
    "dataset": {"dataset", "target_dataset"},
    "rule_type": {"rule_type", "type"},
    "triggering_events": {"triggering_events", "events"},
    "required_fields": {"required_fields", "field_dependencies"},
    "domain_dependencies": {"domain_dependencies", "domains"},
    "expression": {"expression", "script_expression"},
}

NETWORK_RULE_COLUMNS = {
    "rule_type": {"rule_type", "type"},
    "from_dataset": {"from_dataset", "from_class"},
    "from_asset_group": {"from_asset_group"},
    "from_asset_type": {"from_asset_type"},
    "to_dataset": {"to_dataset", "to_class"},
    "to_asset_group": {"to_asset_group"},
    "to_asset_type": {"to_asset_type"},
    "from_terminal": {"from_terminal"},
    "to_terminal": {"to_terminal"},
}

TERMINAL_COLUMNS = {
    "dataset": {"dataset"},
    "asset_group": {"asset_group"},
    "asset_type": {"asset_type"},
    "terminal": {"terminal", "terminal_name"},
    "direction": {"direction"},
}

DIRTY_AREA_COLUMNS = {
    "dataset": {"dataset", "source_name"},
    "error_code": {"error_code", "errorcode"},
    "global_id": {"global_id", "globalid"},
    "object_id": {"object_id", "objectid"},
    "message": {"message", "error_message"},
    "severity": {"severity"},
    "remediation_category": {"remediation_category", "category"},
}
