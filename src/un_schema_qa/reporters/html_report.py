"""Self-contained accessible HTML report rendering."""

from __future__ import annotations

from jinja2 import Environment, PackageLoader, StrictUndefined

from un_schema_qa.models import Finding, ValidationResult


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


def render_html(result: ValidationResult) -> str:
    """Render escaped HTML with embedded styles and no external resources."""

    environment = Environment(
        loader=PackageLoader("un_schema_qa", "templates"),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("report.html.j2")
    return template.render(result=result, groups=_groups(result))
