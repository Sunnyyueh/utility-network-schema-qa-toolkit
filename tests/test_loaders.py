import json
from pathlib import Path

from un_schema_qa.config import load_config
from un_schema_qa.loaders import load_project_data


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_minimal_mixed_format_project(tmp_path: Path) -> None:
    write(
        tmp_path / "source.csv",
        "dataset,geometry_type,record_count,field,data_type,nullable,domain\n"
        "LegacyLine,Polyline,10,Material,String,false,SourceMaterial\n"
        "LegacyLine,Polyline,10,Diameter,Double,true,\n",
    )
    write(
        tmp_path / "target.json",
        json.dumps(
            [
                {
                    "dataset": "WaterLine",
                    "geometry_type": "Polyline",
                    "field": "material",
                    "data_type": "Text",
                    "required": True,
                    "domain": "TargetMaterial",
                },
                {
                    "dataset": "WaterLine",
                    "geometry_type": "Polyline",
                    "field": "diameter",
                    "data_type": "Double",
                },
            ]
        ),
    )
    write(
        tmp_path / "mapping.yml",
        """
- mapping_id: water-main
  source_dataset: LegacyLine
  target_dataset: WaterLine
  source_field: Material
  target_field: material
  definition_query: lifecycle_status = 'Active'
  purpose: Load active mains
  asset_group: Main
  asset_type: Distribution
  rationale: Network role identifies distribution mains.
  network_role: Distribution
- mapping_id: water-main
  source_dataset: LegacyLine
  target_dataset: WaterLine
  source_field: Diameter
  target_field: diameter
""",
    )
    write(
        tmp_path / "project.yml",
        """
project:
  name: mixed-demo
  profile: water
inputs:
  source_schema: source.csv
  target_schema: target.json
  mappings: mapping.yml
""",
    )

    project = load_project_data(load_config(tmp_path / "project.yml"))

    assert project.name == "mixed-demo"
    assert project.source_dataset("legacyline").record_count == 10  # type: ignore[union-attr]
    assert project.target_dataset("waterline").field("MATERIAL").required is True  # type: ignore[union-attr]
    assert len(project.mappings) == 1
    assert len(project.mappings[0].field_mappings) == 2
    assert project.mappings[0].engineering_context.network_role == "Distribution"  # type: ignore[union-attr]
    assert project.mappings[0].location is not None


def test_load_optional_domain_asset_and_issue_inventories(tmp_path: Path) -> None:
    write(
        tmp_path / "source.csv",
        "dataset,field,data_type\nLegacyLine,Material,text\n",
    )
    write(
        tmp_path / "target.csv",
        "dataset,field,data_type,domain\nWaterLine,material,text,TargetMaterial\n",
    )
    write(
        tmp_path / "mapping.csv",
        "mapping_id,source_dataset,target_dataset,source_field,target_field\n"
        "main,LegacyLine,WaterLine,Material,material\n",
    )
    write(
        tmp_path / "domains.csv",
        "domain,code,description\nTargetMaterial,DI,Ductile Iron\nTargetMaterial,PVC,PVC\n",
    )
    write(
        tmp_path / "assets.csv",
        "dataset,asset_group,asset_type,asset_group_code,asset_type_code,categories\n"
        "WaterLine,Main,Distribution,1,2,Distribution;Pipe\n",
    )
    write(
        tmp_path / "dirty.csv",
        "dataset,error_code,global_id,message\nWaterLine,25,{ABC},Invalid geometry\n",
    )
    write(
        tmp_path / "engineering.yml",
        """
rules:
  - rule_id: distribution-main
    conditions:
      - field: network_role
        operator: equals
        value: distribution
    target_asset_group: Main
    target_asset_type: Distribution
    explanation: Distribution role supports the selected target type.
""",
    )
    write(
        tmp_path / "project.yml",
        """
project:
  name: complete-demo
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mapping.csv
  target_domains: domains.csv
  asset_types: assets.csv
  dirty_areas: dirty.csv
  engineering_rules: engineering.yml
""",
    )

    project = load_project_data(load_config(tmp_path / "project.yml"))

    assert project.target_domain("targetmaterial").value("di").description == "Ductile Iron"  # type: ignore[union-attr]
    assert project.asset_type("waterline", "main", "distribution") is not None
    assert project.asset_types[0].categories == ("Distribution", "Pipe")
    assert project.dirty_areas[0].error_code == "25"
    assert project.engineering_rules[0].rule_id == "distribution-main"
