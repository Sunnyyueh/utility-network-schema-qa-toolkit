"""Load and evaluate explainable civil-engineering classification rules."""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from .exceptions import InputFormatError
from .models import EngineeringContext, EngineeringRule, SourceLocation
from .models.common import StrictModel

RuleStatus = Literal["no_match", "single_match", "multiple_matches", "conflicting_matches"]


class RuleEvaluation(StrictModel):
    """Deterministic matches and review information for one context."""

    status: RuleStatus
    matches: tuple[EngineeringRule, ...]
    explanations: tuple[str, ...]
    missing_attributes: tuple[str, ...]
    conflicting_targets: tuple[str, ...]


def _normalized(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().casefold()
    return value


def _equals(actual: Any, expected: Any) -> bool:
    return bool(_normalized(actual) == _normalized(expected))


def _not_equals(actual: Any, expected: Any) -> bool:
    return not _equals(actual, expected)


def _as_collection(expected: Any) -> Collection[Any]:
    if isinstance(expected, Collection) and not isinstance(expected, (str, bytes, dict)):
        return expected
    return (expected,)


def _in(actual: Any, expected: Any) -> bool:
    return any(_equals(actual, candidate) for candidate in _as_collection(expected))


def _not_in(actual: Any, expected: Any) -> bool:
    return not _in(actual, expected)


def _compare(actual: Any, expected: Any, comparator: Callable[[Any, Any], bool]) -> bool:
    try:
        return comparator(actual, expected)
    except TypeError:
        try:
            return comparator(float(actual), float(expected))
        except (TypeError, ValueError):
            return False


def _greater_than(actual: Any, expected: Any) -> bool:
    return _compare(actual, expected, lambda left, right: left > right)


def _greater_or_equal(actual: Any, expected: Any) -> bool:
    return _compare(actual, expected, lambda left, right: left >= right)


def _less_than(actual: Any, expected: Any) -> bool:
    return _compare(actual, expected, lambda left, right: left < right)


def _less_or_equal(actual: Any, expected: Any) -> bool:
    return _compare(actual, expected, lambda left, right: left <= right)


def _exists(actual: Any, expected: Any) -> bool:
    present = actual is not None and actual != ""
    desired = True if expected is None else bool(expected)
    return present is desired


def _contains(actual: Any, expected: Any) -> bool:
    if actual is None:
        return False
    if isinstance(actual, str):
        return str(expected).strip().casefold() in actual.casefold()
    if isinstance(actual, Collection):
        return any(_equals(candidate, expected) for candidate in actual)
    return False


_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "equals": _equals,
    "not_equals": _not_equals,
    "in": _in,
    "not_in": _not_in,
    "greater_than": _greater_than,
    "greater_or_equal": _greater_or_equal,
    "less_than": _less_than,
    "less_or_equal": _less_or_equal,
    "exists": _exists,
    "contains": _contains,
}


def load_engineering_rules(path: Path | str) -> tuple[EngineeringRule, ...]:
    """Load strict YAML rules and attach reviewable source locations."""

    rule_path = Path(path).expanduser().resolve()
    if not rule_path.is_file():
        raise InputFormatError(f"engineering rule file does not exist: {rule_path}")
    try:
        payload = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise InputFormatError(f"cannot parse engineering rules {rule_path}: {error}") from error
    raw_rules = payload.get("rules") if isinstance(payload, dict) else payload
    if not isinstance(raw_rules, list):
        raise InputFormatError(f"engineering rule file must contain a rules list: {rule_path}")

    rules: list[EngineeringRule] = []
    seen: set[str] = set()
    for index, raw_rule in enumerate(raw_rules, start=1):
        if not isinstance(raw_rule, dict):
            raise InputFormatError(f"engineering rule {index} must be a mapping")
        candidate = dict(raw_rule)
        candidate["location"] = SourceLocation(path=str(rule_path), row=index)
        try:
            rule = EngineeringRule.model_validate(candidate)
        except ValidationError as error:
            raise InputFormatError(f"invalid engineering rule {index}: {error}") from error
        if not rule.conditions:
            raise InputFormatError(f"engineering rule {rule.rule_id!r} has no conditions")
        unknown = sorted(
            {
                condition.operator
                for condition in rule.conditions
                if condition.operator not in _OPERATORS
            }
        )
        if unknown:
            raise InputFormatError(
                f"engineering rule {rule.rule_id!r} uses unsupported operator(s): "
                f"{', '.join(unknown)}"
            )
        key = rule.rule_id.casefold()
        if key in seen:
            raise InputFormatError(f"duplicate engineering rule id {rule.rule_id!r}")
        seen.add(key)
        rules.append(rule)
    return tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id.casefold())))


def _rule_matches(context: EngineeringContext, rule: EngineeringRule) -> bool:
    outcomes = []
    for condition in rule.conditions:
        operator = _OPERATORS.get(condition.operator)
        if operator is None:
            raise InputFormatError(
                f"engineering rule {rule.rule_id!r} uses unsupported operator "
                f"{condition.operator!r}"
            )
        outcomes.append(operator(context.value(condition.field), condition.value))
    return any(outcomes) if rule.match == "any" else all(outcomes)


def evaluate_engineering_rules(
    context: EngineeringContext,
    rules: Sequence[EngineeringRule],
) -> RuleEvaluation:
    """Evaluate rules in stable priority order without modifying the mapping."""

    ordered_rules = tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id.casefold())))
    missing: list[str] = []
    seen_missing: set[str] = set()
    for rule in ordered_rules:
        for condition in rule.conditions:
            if context.value(condition.field) is None:
                key = condition.field.casefold()
                if key not in seen_missing:
                    missing.append(condition.field)
                    seen_missing.add(key)

    matches = tuple(rule for rule in ordered_rules if _rule_matches(context, rule))
    targets = {
        (rule.target_asset_group.casefold(), rule.target_asset_type.casefold()): (
            f"{rule.target_asset_group} / {rule.target_asset_type}"
        )
        for rule in matches
    }
    conflicting_targets = (
        tuple(sorted(targets.values(), key=str.casefold)) if len(targets) > 1 else ()
    )
    if not matches:
        status: RuleStatus = "no_match"
    elif len(matches) == 1:
        status = "single_match"
    elif conflicting_targets:
        status = "conflicting_matches"
    else:
        status = "multiple_matches"
    return RuleEvaluation(
        status=status,
        matches=matches,
        explanations=tuple(f"{rule.rule_id}: {rule.explanation}" for rule in matches),
        missing_attributes=tuple(missing),
        conflicting_targets=conflicting_targets,
    )
