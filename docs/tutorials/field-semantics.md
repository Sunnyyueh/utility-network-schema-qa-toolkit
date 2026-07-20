# Field-Semantic Mapping Tutorial

This tutorial reviews three common Utility Network field mappings: lifecycle status, owner, and elevation. The project uses metadata exported from the real source and intended target schemas. It does not copy feature records, geometry, credentials, or a live Utility Network into the toolkit.

## 1. Export the schema metadata

Create a source schema inventory with the fields, normalized data types, lengths, and assigned domains that exist in the source system:

```csv
dataset,field,data_type,nullable,length,domain
LegacyWaterLine,status,text,false,32,LegacyLifecycle
LegacyWaterLine,owner_name,text,true,100,
LegacyWaterLine,elevation_ft,double,true,,
```

Create the corresponding target schema inventory from the intended Utility Network design:

```csv
dataset,field,data_type,nullable,required,length,domain
WaterLine,lifecycle_status,text,false,true,32,TargetLifecycle
WaterLine,owner,text,true,false,128,
WaterLine,elevation,double,true,false,,
```

These inventories describe fields; they contain no lifecycle, owner, or elevation values from individual assets.

## 2. Export lifecycle domains and the crosswalk

The source domain carries `target_code` values so the existing domain validator can review the lifecycle crosswalk:

```csv
domain,code,description,target_code,field_type
LegacyLifecycle,Active,Active,1,text
LegacyLifecycle,Inactive,Inactive,2,text
LegacyLifecycle,Abandoned,Abandoned,3,text
```

The target inventory lists the allowed Utility Network codes:

```csv
domain,code,description,field_type
TargetLifecycle,1,Active,text
TargetLifecycle,2,Inactive,text
TargetLifecycle,3,Abandoned,text
```

The `field_semantics` validator confirms that both lifecycle fields declare domains. The `domains` validator then verifies inventory presence and crosswalk coverage.

## 3. Declare the field mappings

Add one explicit `semantic_role` per field row. Use `field_rationale` to record the reason for the crosswalk, normalization, or conversion.

```csv
mapping_id,source_dataset,target_dataset,source_field,target_field,expression,semantic_role,source_unit,target_unit,source_vertical_datum,target_vertical_datum,field_rationale
water-main,LegacyWaterLine,WaterLine,status,lifecycle_status,,lifecycle_status,,,,,Crosswalk legacy status values to the target lifecycle domain
water-main,LegacyWaterLine,WaterLine,owner_name,owner,UPPER(owner_name),owner,,,,,Normalize owner names for stewardship review
water-main,LegacyWaterLine,WaterLine,elevation_ft,elevation,elevation_ft * 0.3048006096,elevation,us_survey_ft,m,NAVD88,NAVD88,Convert surveyed elevations from US survey feet to metres
```

The roles are explicit. The toolkit does not guess a role from `status`, `owner_name`, `elevation_ft`, or other field names.

## 4. Enable and run the checks

Reference the exported files from `project.yml` and enable the generic mapping, semantic, and domain validators:

```yaml
project:
  name: water-field-review
  profile: water
inputs:
  source_schema: data/source_schema.csv
  target_schema: data/target_schema.csv
  mappings: data/mappings.csv
  source_domains: data/source_domains.csv
  target_domains: data/target_domains.csv
validation:
  enabled: [schema, mapping, field_semantics, domains]
  fail_on: error
outputs:
  directory: reports
  formats: [json, csv, markdown, html]
```

Run the selected manifest checks:

```bash
un-schema-qa validate project.yml
```

During focused authoring, run only the semantic validator:

```bash
un-schema-qa validate project.yml --check field_semantics
```

The focused command does not replace the complete review. Run `mapping` and `domains` before accepting lifecycle crosswalk readiness.

## 5. Interpret the results

The three roles answer different metadata questions:

| Role | Review questions |
| --- | --- |
| `lifecycle_status` | Do source and target fields both declare coded-value domains so a crosswalk can be checked? |
| `owner` | Are both fields text, is the target long enough, and are domains used consistently? |
| `elevation` | Are fields numeric, units recognized, vertical datums declared, and required conversion/transformation expressions documented? |

Errors identify schema or conversion metadata that must be resolved. A missing `field_rationale` is a warning because the field may be structurally valid while still lacking an auditable decision record. Exact codes and default severities are listed in the [Finding Code Catalog](../finding-codes.md).

## 6. Understand the boundary

This is metadata-level QA. The toolkit does not:

- read feature records or compare individual values;
- execute SQL, lookup logic, or mapping expressions;
- validate the numerical result of a unit conversion;
- perform or verify a vertical coordinate operation;
- infer ownership, lifecycle state, or elevation quality from asset data; or
- replace target domains, Utility Network rules, data-load reconciliation, or engineering review.

Use record-level profiling and post-load QA alongside this toolkit when the migration reaches execution and acceptance testing.
