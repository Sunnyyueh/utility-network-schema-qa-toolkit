"""Review-friendly Markdown report rendering."""

from __future__ import annotations

from un_schema_qa.models import Finding, ValidationResult


def _cell(value: object | None) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _groups(result: ValidationResult) -> tuple[tuple[str, tuple[Finding, ...]], ...]:
    names = list(result.validators)
    known = {name.casefold() for name in names}
    for item in result.findings:
        if item.validator.casefold() not in known:
            names.append(item.validator)
            known.add(item.validator.casefold())
    return tuple(
        (
            name,
            tuple(item for item in result.findings if item.validator.casefold() == name.casefold()),
        )
        for name in names
        if any(item.validator.casefold() == name.casefold() for item in result.findings)
    )


def render_markdown(result: ValidationResult) -> str:
    """Render a concise grouped GitHub-flavored Markdown report."""

    counts = result.summary.counts
    lines = [
        "# Utility Network Schema QA Report",
        "",
        f"**Project:** {_cell(result.project_name)}  ",
        f"**Status:** `{result.summary.status.value}`  ",
        f"**Toolkit version:** `{result.toolkit_version}`  ",
        f"**Input fingerprint:** `{result.input_fingerprint}`",
        "",
        "## Summary",
        "",
        "| Total | Errors | Warnings | Info |",
        "| ---: | ---: | ---: | ---: |",
        (
            f"| {result.summary.total} | {counts['error']} | {counts['warning']} | "
            f"{counts['info']} |"
        ),
        "",
        f"**Validators run:** {_cell(', '.join(result.validators) or 'None')}",
        "",
    ]
    groups = _groups(result)
    if not groups:
        lines.extend(("## Findings", "", "No findings were reported.", ""))
        return "\n".join(lines)
    for name, findings in groups:
        lines.extend(
            (
                f"## {_cell(name)}",
                "",
                "| Severity | Code | Dataset / Field | Mapping | Message | Recommendation |",
                "| --- | --- | --- | --- | --- | --- |",
            )
        )
        for item in findings:
            affected = " / ".join(value for value in (item.dataset, item.field) if value)
            lines.append(
                f"| {_cell(item.severity.value)} | `{_cell(item.code)}` | "
                f"{_cell(affected)} | {_cell(item.mapping_id)} | {_cell(item.message)} | "
                f"{_cell(item.recommendation)} |"
            )
        lines.append("")
    return "\n".join(lines)
