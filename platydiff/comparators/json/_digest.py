"""Schema-v3 domain-separated structured evidence digests."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

from platydiff.comparators.json._parser import (
    JsonNode,
    JsonNumber,
    JsonScalar,
    JsonSequence,
)
from platydiff.core.models import JsonNumberMode

_MAX_U64 = 2**64 - 1


def _u64(value: int) -> bytes:
    if not 0 <= value <= _MAX_U64:
        raise OverflowError("canonical structured length exceeds U64")
    return value.to_bytes(8, "big")


def _signed(value: int) -> bytes:
    if value == 0:
        return b""
    length = max(1, (value.bit_length() + 8) // 8)
    encoded = value.to_bytes(length, "big", signed=True)
    while len(encoded) > 1 and (
        (encoded[0] == 0 and encoded[1] < 0x80)
        or (encoded[0] == 0xFF and encoded[1] >= 0x80)
    ):
        encoded = encoded[1:]
    return encoded


def _magnitude(decimal: str) -> bytes:
    chunks: list[int] = []
    for offset in range(0, len(decimal), 9):
        width = min(9, len(decimal) - offset)
        factor = 10**width
        carry = int(decimal[offset : offset + width])
        for index in range(len(chunks)):
            value = chunks[index] * factor + carry
            chunks[index] = value & 0xFFFFFFFF
            carry = value >> 32
        while carry:
            chunks.append(carry & 0xFFFFFFFF)
            carry >>= 32
    if not chunks:
        return b""
    encoded = b"".join(item.to_bytes(4, "big") for item in reversed(chunks))
    return encoded.lstrip(b"\x00")


def _integer_text(number: JsonNumber) -> str:
    return number.coefficient + "0" * number.exponent


def _number_payload(number: JsonNumber) -> Iterator[bytes]:
    if number.kind == "integer":
        magnitude = _magnitude(_integer_text(number))
        yield b"\x03"
        yield b"\x01" if number.negative else b"\x00"
        yield _u64(len(magnitude))
        yield magnitude
        return
    coefficient = number.coefficient.encode("ascii")
    exponent = _signed(number.exponent)
    yield b"\x04"
    yield b"\x01" if number.negative else b"\x00"
    yield _u64(len(coefficient))
    yield coefficient
    yield _u64(len(exponent))
    yield exponent


def _payload(node: JsonNode, lengths: dict[int, int]) -> Iterator[bytes]:
    if isinstance(node, JsonScalar):
        if node.kind == "null":
            yield b"\x00"
        elif node.kind == "boolean":
            yield b"\x02" if node.value is True else b"\x01"
        elif node.kind == "string":
            if not isinstance(node.value, str):
                raise RuntimeError("invalid private JSON string")
            encoded = node.value.encode("utf-8")
            yield b"\x05"
            yield _u64(len(encoded))
            yield encoded
        else:
            if not isinstance(node.value, JsonNumber):
                raise RuntimeError("invalid private JSON number")
            yield from _number_payload(node.value)
        return
    if isinstance(node, JsonSequence):
        yield b"\x06"
        yield _u64(len(node.items))
        for child in node.items:
            yield _u64(lengths[id(child)])
            yield from _payload(child, lengths)
        return
    yield b"\x07"
    yield _u64(len(node.items))
    for key, child in node.items:
        encoded = key.encode("utf-8")
        yield _u64(len(encoded))
        yield encoded
        yield _u64(lengths[id(child)])
        yield from _payload(child, lengths)


def _payload_lengths(node: JsonNode) -> dict[int, int]:
    lengths: dict[int, int] = {}

    def visit(current: JsonNode) -> int:
        if isinstance(current, JsonScalar):
            if current.kind in ("null", "boolean"):
                length = 1
            elif current.kind == "string":
                if not isinstance(current.value, str):
                    raise RuntimeError("invalid private JSON string")
                length = 9 + len(current.value.encode("utf-8"))
            else:
                if not isinstance(current.value, JsonNumber):
                    raise RuntimeError("invalid private JSON number")
                if current.value.kind == "integer":
                    magnitude = _magnitude(_integer_text(current.value))
                    length = 10 + len(magnitude)
                else:
                    coefficient = current.value.coefficient.encode("ascii")
                    exponent = _signed(current.value.exponent)
                    length = 18 + len(coefficient) + len(exponent)
        elif isinstance(current, JsonSequence):
            length = 9
            for child in current.items:
                length += 8 + visit(child)
        else:
            length = 9
            for key, child in current.items:
                length += 16 + len(key.encode("utf-8")) + visit(child)
        if length > _MAX_U64:
            raise OverflowError("canonical structured payload exceeds U64")
        lengths[id(current)] = length
        return length

    visit(node)
    return lengths


def evidence_digest(node: JsonNode, number_mode: JsonNumberMode) -> str:
    """Return the RFC 0006 evidence digest for one immutable tree node."""
    if (
        number_mode is JsonNumberMode.LEXICAL
        and isinstance(node, JsonScalar)
        and isinstance(node.value, JsonNumber)
    ):
        domain = "structured/number/lexical"
        lexical_chunks = (node.value.lexical.encode("utf-8"),)
        chunks: Iterator[bytes] = iter(lexical_chunks)
        length = len(lexical_chunks[0])
    else:
        domain = "structured/value"
        lengths = _payload_lengths(node)
        chunks = _payload(node, lengths)
        length = lengths[id(node)]
    digest = hashlib.sha256()
    digest.update(f"platydiff/v3/{domain}".encode())
    digest.update(b"\x00")
    digest.update(_u64(length))
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()
