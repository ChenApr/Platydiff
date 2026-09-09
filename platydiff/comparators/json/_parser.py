"""Bounded RFC 8259 parser producing a private immutable tree."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

from platydiff.core.models import PipelineStage, StructuredResourceLimits
from platydiff.core.problems import DecodeError, ResourceLimitError


@dataclass(frozen=True, slots=True)
class JsonNumber:
    kind: Literal["integer", "decimal"]
    negative: bool
    coefficient: str
    exponent: int
    lexical: str

    @property
    def canonical(self) -> str:
        if self.kind == "integer":
            return (
                ("-" if self.negative else "") + self.coefficient + "0" * self.exponent
            )
        return f"{'-' if self.negative else ''}{self.coefficient}E{self.exponent}"


@dataclass(frozen=True, slots=True)
class JsonScalar:
    kind: Literal["null", "boolean", "integer", "decimal", "string"]
    value: bool | str | JsonNumber | None


@dataclass(frozen=True, slots=True)
class JsonSequence:
    items: tuple[JsonNode, ...]


@dataclass(frozen=True, slots=True)
class JsonMapping:
    items: tuple[tuple[str, JsonNode], ...]


type JsonNode = JsonScalar | JsonSequence | JsonMapping


@dataclass(frozen=True, slots=True)
class ParseStats:
    nodes: int
    maximum_depth: int
    maximum_scalar_bytes: int
    maximum_number_digits: int
    maximum_abs_exponent: int


class _Parser:
    def __init__(self, text: str, limits: StructuredResourceLimits) -> None:
        self.text = text
        self.limits = limits
        self.cursor = 0
        self.nodes = 0
        self.maximum_depth = 0
        self.maximum_scalar_bytes = 0
        self.maximum_number_digits = 0
        self.maximum_abs_exponent = 0

    def parse(self) -> tuple[JsonNode, ParseStats]:
        self._whitespace()
        node = self._value(0)
        self._whitespace()
        if self.cursor != len(self.text):
            self._invalid()
        return node, ParseStats(
            self.nodes,
            self.maximum_depth,
            self.maximum_scalar_bytes,
            self.maximum_number_digits,
            self.maximum_abs_exponent,
        )

    def _value(self, depth: int) -> JsonNode:
        if depth > self.limits.max_depth:
            self._limit("A JSON source exceeded the configured depth limit.")
        if self.nodes >= self.limits.max_nodes:
            self._limit("A JSON source exceeded the configured node limit.")
        self.nodes += 1
        self.maximum_depth = max(self.maximum_depth, depth)
        if self.cursor >= len(self.text):
            self._invalid()
        character = self.text[self.cursor]
        if character == '"':
            return JsonScalar("string", self._string())
        if character == "{":
            return self._object(depth)
        if character == "[":
            return self._array(depth)
        for token, scalar in (
            ("null", JsonScalar("null", None)),
            ("true", JsonScalar("boolean", True)),
            ("false", JsonScalar("boolean", False)),
        ):
            if self.text.startswith(token, self.cursor):
                self.cursor += len(token)
                return scalar
        if character == "-" or (character.isascii() and character.isdigit()):
            number = self._number()
            return JsonScalar(number.kind, number)
        self._invalid()

    def _array(self, depth: int) -> JsonSequence:
        self.cursor += 1
        self._whitespace()
        items: list[JsonNode] = []
        if self._consume("]"):
            return JsonSequence(())
        while True:
            items.append(self._value(depth + 1))
            self._whitespace()
            if self._consume("]"):
                return JsonSequence(tuple(items))
            self._expect(",")
            self._whitespace()

    def _object(self, depth: int) -> JsonMapping:
        self.cursor += 1
        self._whitespace()
        items: list[tuple[str, JsonNode]] = []
        keys: set[str] = set()
        if self._consume("}"):
            return JsonMapping(())
        while True:
            if self.cursor >= len(self.text) or self.text[self.cursor] != '"':
                self._invalid()
            key = self._string()
            if key in keys:
                raise DecodeError("A JSON object contains a duplicate decoded key.")
            keys.add(key)
            self._whitespace()
            self._expect(":")
            self._whitespace()
            value = self._value(depth + 1)
            items.append((key, value))
            self._whitespace()
            if self._consume("}"):
                return JsonMapping(tuple(sorted(items, key=lambda item: item[0])))
            self._expect(",")
            self._whitespace()

    def _string(self) -> str:
        self._expect('"')
        output: list[str] = []
        byte_count = 0
        while self.cursor < len(self.text):
            character = self.text[self.cursor]
            self.cursor += 1
            if character == '"':
                value = "".join(output)
                self.maximum_scalar_bytes = max(self.maximum_scalar_bytes, byte_count)
                return value
            if character == "\\":
                character = self._escape()
            elif ord(character) < 0x20:
                self._invalid()
            encoded = character.encode("utf-8", errors="strict")
            byte_count += len(encoded)
            if byte_count > self.limits.max_scalar_bytes:
                self._limit("A JSON scalar exceeded the configured byte limit.")
            output.append(character)
        self._invalid()

    def _escape(self) -> str:
        if self.cursor >= len(self.text):
            self._invalid()
        escaped = self.text[self.cursor]
        self.cursor += 1
        simple = {
            '"': '"',
            "\\": "\\",
            "/": "/",
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "t": "\t",
        }
        if escaped in simple:
            return simple[escaped]
        if escaped != "u":
            self._invalid()
        first = self._hex_quad()
        if 0xD800 <= first <= 0xDBFF:
            if not self.text.startswith("\\u", self.cursor):
                self._invalid()
            self.cursor += 2
            second = self._hex_quad()
            if not 0xDC00 <= second <= 0xDFFF:
                self._invalid()
            return chr(0x10000 + ((first - 0xD800) << 10) + second - 0xDC00)
        if 0xDC00 <= first <= 0xDFFF:
            self._invalid()
        return chr(first)

    def _hex_quad(self) -> int:
        end = self.cursor + 4
        token = self.text[self.cursor : end]
        if len(token) != 4 or any(
            character not in "0123456789abcdefABCDEF" for character in token
        ):
            self._invalid()
        self.cursor = end
        return int(token, 16)

    def _number(self) -> JsonNumber:
        start = self.cursor
        negative = self._consume("-")
        integer_start = self.cursor
        if self._consume("0"):
            if self.cursor < len(self.text) and self.text[self.cursor].isdigit():
                self._invalid()
        else:
            if (
                self.cursor >= len(self.text)
                or self.text[self.cursor] not in "123456789"
            ):
                self._invalid()
            self.cursor += 1
            while (
                self.cursor < len(self.text)
                and self.text[self.cursor].isascii()
                and self.text[self.cursor].isdigit()
            ):
                self.cursor += 1
        integer_digits = self.text[integer_start : self.cursor]
        fraction_digits = ""
        if self._consume("."):
            fraction_start = self.cursor
            self._digits(required=True)
            fraction_digits = self.text[fraction_start : self.cursor]
        explicit_exponent = 0
        exponent_digits = ""
        exponent_negative = False
        if self.cursor < len(self.text) and self.text[self.cursor] in "eE":
            self.cursor += 1
            exponent_negative = self._consume("-")
            if not exponent_negative:
                self._consume("+")
            exponent_start = self.cursor
            self._digits(required=True)
            exponent_digits = self.text[exponent_start : self.cursor]
        digit_count = len(integer_digits) + len(fraction_digits) + len(exponent_digits)
        if digit_count > self.limits.max_number_digits:
            self._limit("A JSON number exceeded the configured digit limit.")
        if exponent_digits:
            maximum_explicit = self.limits.max_abs_exponent + len(fraction_digits)
            normalized_exponent = exponent_digits.lstrip("0") or "0"
            maximum_text = str(maximum_explicit)
            if len(normalized_exponent) > len(maximum_text) or (
                len(normalized_exponent) == len(maximum_text)
                and normalized_exponent > maximum_text
            ):
                self._limit("A JSON number exceeded the configured exponent limit.")
            explicit_exponent = int(normalized_exponent)
            if exponent_negative:
                explicit_exponent = -explicit_exponent
        exponent = explicit_exponent - len(fraction_digits)
        if abs(exponent) > self.limits.max_abs_exponent:
            self._limit("A JSON number exceeded the configured exponent limit.")
        self.maximum_number_digits = max(self.maximum_number_digits, digit_count)
        self.maximum_abs_exponent = max(self.maximum_abs_exponent, abs(exponent))
        coefficient = (integer_digits + fraction_digits).lstrip("0") or "0"
        if coefficient == "0":
            negative = False
            exponent = 0
        else:
            trailing = len(coefficient) - len(coefficient.rstrip("0"))
            if trailing:
                coefficient = coefficient[:-trailing]
                exponent += trailing
        kind: Literal["integer", "decimal"] = (
            "integer"
            if "." not in self.text[start : self.cursor]
            and "e" not in self.text[start : self.cursor].lower()
            else "decimal"
        )
        return JsonNumber(
            kind, negative, coefficient, exponent, self.text[start : self.cursor]
        )

    def _digits(self, *, required: bool) -> None:
        start = self.cursor
        while (
            self.cursor < len(self.text)
            and self.text[self.cursor].isascii()
            and self.text[self.cursor].isdigit()
        ):
            self.cursor += 1
        if required and self.cursor == start:
            self._invalid()

    def _whitespace(self) -> None:
        while self.cursor < len(self.text) and self.text[self.cursor] in " \t\r\n":
            self.cursor += 1

    def _consume(self, token: str) -> bool:
        if self.text.startswith(token, self.cursor):
            self.cursor += len(token)
            return True
        return False

    def _expect(self, token: str) -> None:
        if not self._consume(token):
            self._invalid()

    def _invalid(self) -> Never:
        raise DecodeError("A source is not valid strict RFC 8259 JSON.")

    def _limit(self, message: str) -> Never:
        raise ResourceLimitError(message, stage=PipelineStage.DECODING)


def parse_json(
    text: str, limits: StructuredResourceLimits
) -> tuple[JsonNode, ParseStats]:
    """Parse exactly one JSON value with deterministic resource accounting."""
    return _Parser(text, limits).parse()
