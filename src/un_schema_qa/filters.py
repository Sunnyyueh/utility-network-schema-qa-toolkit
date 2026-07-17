"""Non-executing analysis for a documented SQL-style filter subset."""

from __future__ import annotations

import re

from pydantic import Field

from .models.common import StrictModel


class FilterToken(StrictModel):
    """One lexical token from a filter expression."""

    kind: str
    value: str
    position: int = Field(ge=0)


class FilterPredicate(StrictModel):
    """One field predicate discovered during syntax validation."""

    field: str
    operator: str
    values: tuple[str, ...] = ()
    position: int = Field(ge=0)


class FilterAnalysis(StrictModel):
    """Static facts about a filter; the expression is never evaluated."""

    expression: str
    tokens: tuple[FilterToken, ...]
    identifiers: tuple[str, ...]
    predicates: tuple[FilterPredicate, ...]
    errors: tuple[str, ...]
    partition_signature: tuple[tuple[str, tuple[str, ...]], ...] | None = None


_KEYWORDS = {
    "AND",
    "BETWEEN",
    "DATE",
    "IN",
    "IS",
    "LIKE",
    "NOT",
    "NULL",
    "OR",
    "TIMESTAMP",
}
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_.$]*")
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


def _tokenize(expression: str) -> tuple[list[FilterToken], list[str]]:
    tokens: list[FilterToken] = []
    errors: list[str] = []
    position = 0
    while position < len(expression):
        character = expression[position]
        if character.isspace():
            position += 1
            continue
        if character in "(),":
            kind = {"(": "LPAREN", ")": "RPAREN", ",": "COMMA"}[character]
            tokens.append(FilterToken(kind=kind, value=character, position=position))
            position += 1
            continue
        if character in "=<>!":
            operator = expression[position : position + 2]
            if operator in {"<=", ">=", "<>", "!="}:
                tokens.append(FilterToken(kind="OP", value=operator, position=position))
                position += 2
            elif character in "=<>":
                tokens.append(FilterToken(kind="OP", value=character, position=position))
                position += 1
            else:
                errors.append(f"unsupported token {character!r} at position {position}")
                position += 1
            continue
        if character == "'":
            start = position
            position += 1
            string_characters: list[str] = []
            while position < len(expression):
                if expression[position] != "'":
                    string_characters.append(expression[position])
                    position += 1
                    continue
                if position + 1 < len(expression) and expression[position + 1] == "'":
                    string_characters.append("'")
                    position += 2
                    continue
                position += 1
                tokens.append(
                    FilterToken(
                        kind="STRING",
                        value="".join(string_characters),
                        position=start,
                    )
                )
                break
            else:
                errors.append(f"unterminated string starting at position {start}")
            continue
        if character in {'"', "["}:
            start = position
            closing = '"' if character == '"' else "]"
            position += 1
            end = expression.find(closing, position)
            if end == -1:
                errors.append(f"unterminated identifier starting at position {start}")
                position = len(expression)
            else:
                identifier_value = expression[position:end]
                if not identifier_value:
                    errors.append(f"empty identifier at position {start}")
                else:
                    tokens.append(FilterToken(kind="IDENT", value=identifier_value, position=start))
                position = end + 1
            continue
        number = _NUMBER.match(expression, position)
        if number:
            tokens.append(FilterToken(kind="NUMBER", value=number.group(0), position=position))
            position = number.end()
            continue
        word = _WORD.match(expression, position)
        if word:
            word_value = word.group(0)
            upper = word_value.upper()
            tokens.append(
                FilterToken(
                    kind="KEYWORD" if upper in _KEYWORDS else "IDENT",
                    value=upper if upper in _KEYWORDS else word_value,
                    position=position,
                )
            )
            position = word.end()
            continue
        errors.append(f"unsupported token {character!r} at position {position}")
        position += 1
    return tokens, errors


class _Parser:
    def __init__(self, tokens: list[FilterToken], lexical_errors: list[str]) -> None:
        self.tokens = [*tokens, FilterToken(kind="EOF", value="", position=0)]
        self.index = 0
        self.errors = list(lexical_errors)
        self.identifiers: list[str] = []
        self.predicates: list[FilterPredicate] = []
        self.has_disjunction = False
        self.has_unary_not = False

    @property
    def current(self) -> FilterToken:
        return self.tokens[self.index]

    def advance(self) -> FilterToken:
        token = self.current
        if token.kind != "EOF":
            self.index += 1
        return token

    def accepts(self, kind: str, value: str | None = None) -> FilterToken | None:
        token = self.current
        if token.kind == kind and (value is None or token.value == value):
            return self.advance()
        return None

    def error(self, message: str, token: FilterToken | None = None) -> None:
        location = self.current if token is None else token
        self.errors.append(f"{message} at position {location.position}")

    def add_identifier(self, value: str) -> None:
        if value.casefold() not in {item.casefold() for item in self.identifiers}:
            self.identifiers.append(value)

    def parse(self) -> None:
        if self.current.kind == "EOF":
            self.error("filter expression is empty")
            return
        self.parse_or()
        if self.current.kind != "EOF":
            self.error(f"unexpected token {self.current.value!r}")

    def parse_or(self) -> None:
        self.parse_and()
        while self.accepts("KEYWORD", "OR"):
            self.has_disjunction = True
            self.parse_and()

    def parse_and(self) -> None:
        self.parse_not()
        while self.accepts("KEYWORD", "AND"):
            self.parse_not()

    def parse_not(self) -> None:
        if self.accepts("KEYWORD", "NOT"):
            self.has_unary_not = True
            self.parse_not()
            return
        self.parse_primary()

    def parse_primary(self) -> None:
        if self.accepts("LPAREN"):
            self.parse_or()
            if not self.accepts("RPAREN"):
                self.error("expected closing parenthesis")
            return
        self.parse_predicate()

    def parse_predicate(self) -> None:
        field = self.accepts("IDENT")
        if field is None:
            self.error("expected a field identifier")
            self.advance()
            return
        self.add_identifier(field.value)

        if self.accepts("KEYWORD", "IS"):
            null_operator = "IS NOT NULL" if self.accepts("KEYWORD", "NOT") else "IS NULL"
            if not self.accepts("KEYWORD", "NULL"):
                self.error("expected NULL after IS")
            self._add_predicate(field, null_operator, ())
            return

        negated = bool(self.accepts("KEYWORD", "NOT"))
        if self.accepts("KEYWORD", "IN"):
            self._parse_in(field, "NOT IN" if negated else "IN")
            return
        if self.accepts("KEYWORD", "LIKE"):
            value = self._parse_operand()
            self._add_predicate(field, "NOT LIKE" if negated else "LIKE", self._values(value))
            return
        if self.accepts("KEYWORD", "BETWEEN"):
            first = self._parse_operand()
            if not self.accepts("KEYWORD", "AND"):
                self.error("expected AND in BETWEEN predicate")
            second = self._parse_operand()
            self._add_predicate(
                field,
                "NOT BETWEEN" if negated else "BETWEEN",
                self._values(first, second),
            )
            return
        if negated:
            self.error("NOT must precede IN, LIKE, or BETWEEN")
            return

        comparison_operator = self.accepts("OP")
        if comparison_operator is None:
            self.error("expected a comparison operator")
            return
        value = self._parse_operand()
        self._add_predicate(field, comparison_operator.value, self._values(value))

    def _parse_in(self, field: FilterToken, operator: str) -> None:
        if not self.accepts("LPAREN"):
            self.error("expected opening parenthesis after IN")
            self._add_predicate(field, operator, ())
            return
        operands: list[tuple[str, bool] | None] = []
        if self.current.kind == "RPAREN":
            self.error("IN list cannot be empty")
        else:
            operands.append(self._parse_operand())
            while self.accepts("COMMA"):
                operands.append(self._parse_operand())
        if not self.accepts("RPAREN"):
            self.error("expected closing parenthesis for IN list")
        self._add_predicate(field, operator, self._values(*operands))

    def _parse_operand(self) -> tuple[str, bool] | None:
        token = self.current
        if token.kind in {"STRING", "NUMBER"}:
            self.advance()
            return token.value, True
        if token.kind == "KEYWORD" and token.value in {"DATE", "TIMESTAMP"}:
            prefix = self.advance().value
            value = self.accepts("STRING")
            if value is None:
                self.error(f"expected quoted value after {prefix}")
                return None
            return f"{prefix} {value.value}", True
        if token.kind == "KEYWORD" and token.value == "NULL":
            self.advance()
            return "NULL", True
        if token.kind == "IDENT":
            self.advance()
            self.add_identifier(token.value)
            return token.value, False
        self.error("expected a literal or field identifier")
        self.advance()
        return None

    @staticmethod
    def _values(*operands: tuple[str, bool] | None) -> tuple[str, ...]:
        return tuple(operand[0] for operand in operands if operand is not None)

    def _add_predicate(self, field: FilterToken, operator: str, values: tuple[str, ...]) -> None:
        self.predicates.append(
            FilterPredicate(
                field=field.value,
                operator=operator,
                values=values,
                position=field.position,
            )
        )


def _partition_signature(
    parser: _Parser,
) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    if parser.errors or parser.has_disjunction or parser.has_unary_not:
        return None
    constraints: dict[str, tuple[str, set[str]]] = {}
    for predicate in parser.predicates:
        if predicate.operator not in {"=", "IN"} or not predicate.values:
            return None
        key = predicate.field.casefold()
        values = set(predicate.values)
        if key in constraints:
            display, existing = constraints[key]
            constraints[key] = display, existing & values
        else:
            constraints[key] = predicate.field, values
    return tuple(
        (display, tuple(sorted(values, key=str.casefold)))
        for display, values in constraints.values()
    )


def analyze_filter(expression: str) -> FilterAnalysis:
    """Tokenize and validate a filter without evaluating it or accessing data."""

    tokens, lexical_errors = _tokenize(expression)
    parser = _Parser(tokens, lexical_errors)
    parser.parse()
    return FilterAnalysis(
        expression=expression,
        tokens=tuple(tokens),
        identifiers=tuple(parser.identifiers),
        predicates=tuple(parser.predicates),
        errors=tuple(parser.errors),
        partition_signature=_partition_signature(parser),
    )


def possible_overlap(left: FilterAnalysis, right: FilterAnalysis) -> bool | None:
    """Return whether simple partitions can overlap, or ``None`` when unknown."""

    if left.partition_signature is None or right.partition_signature is None:
        return None
    left_constraints = {
        field.casefold(): {value.casefold() for value in values}
        for field, values in left.partition_signature
    }
    right_constraints = {
        field.casefold(): {value.casefold() for value in values}
        for field, values in right.partition_signature
    }
    for field in left_constraints.keys() & right_constraints.keys():
        if left_constraints[field].isdisjoint(right_constraints[field]):
            return False
    return True
