from pathlib import Path

from un_schema_qa import load_project, validate_project
from un_schema_qa.models import ProjectData


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_public_api_loads_and_validates_manifest(tmp_path: Path) -> None:
    write(tmp_path / "source.csv", "dataset,field,data_type\nLegacy,id,integer\n")
    write(tmp_path / "target.csv", "dataset,field,data_type\nTarget,id,integer\n")
    write(
        tmp_path / "mappings.csv",
        "mapping_id,source_dataset,target_dataset,source_field,target_field\n"
        "main,Legacy,Target,id,id\n",
    )
    write(
        tmp_path / "project.yml",
        """
project:
  name: api-demo
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mappings.csv
validation:
  enabled: [schema, mapping]
""",
    )

    project = load_project(tmp_path / "project.yml")
    result_from_path = validate_project(tmp_path / "project.yml")
    result_from_model = validate_project(project, checks=("schema", "mapping"))

    assert isinstance(project, ProjectData)
    assert result_from_path.project_name == "api-demo"
    assert result_from_path.summary.status == "pass"
    assert result_from_model.summary.status == "pass"
