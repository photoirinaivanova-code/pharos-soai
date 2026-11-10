"""Small ABI helpers for addresses, quantities, and ERC-20 return values."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
TX_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


def is_address(value: str) -> bool:
    return bool(ADDRESS_RE.fullmatch(value or ""))


def is_tx_hash(value: str) -> bool:
    return bool(TX_HASH_RE.fullmatch(value or ""))


def normalize_address(value: str) -> str:
    if not is_address(value):
        raise ValueError(f"Invalid address: {value!r}")
    return value.lower()


def hex_to_int(value: str | None) -> int:
    if value in (None, "", "0x"):
        return 0
    return int(value, 16)


def int_to_hex(value: int) -> str:
    return hex(value)


def pad_address_arg(address: str) -> str:
    addr = normalize_address(address)[2:]
    return "0x" + ("0" * 24) + addr


def topic_to_address(topic: str) -> str:
    raw = topic[2:] if topic.startswith("0x") else topic
    if len(raw) < 40:
        raise ValueError(f"Topic too short to contain an address: {topic!r}")
    return "0x" + raw[-40:].lower()


def decode_uint256(data: str) -> int:
    if not data or data == "0x":
        return 0
    return int(data, 16)


def decode_abi_string(data: str) -> str:
    """Decode a standard ABI-encoded string (or a bytes32 string fallback)."""
    if not data or data == "0x":
        return ""
    raw = data[2:] if data.startswith("0x") else data
    if len(raw) < 64:
        return ""
    # Dynamic string: offset, length, payload
    try:
        offset = int(raw[0:64], 16)
        if offset == 32 and len(raw) >= 128:
            length = int(raw[64:128], 16)
            start = 128
            end = start + length * 2
            payload = raw[start:end]
            return bytes.fromhex(payload).decode("utf-8", errors="replace")
    except (ValueError, IndexError):
        pass
    # bytes32 fallback used by some older tokens
    try:
        return bytes.fromhex(raw[:64]).rstrip(b"\x00").decode("utf-8", errors="replace")
    except ValueError:
        return ""


def format_units(value: int, decimals: int) -> str:
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    quant = Decimal(value) / (Decimal(10) ** decimals)
    text = format(quant, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def parse_units(value: str, decimals: int) -> int:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal amount: {value!r}") from exc
    scaled = (amount * (Decimal(10) ** decimals)).to_integral_value()
    return int(scaled)


def same_address(left: str, right: str) -> bool:
    return left.lower() == right.lower()
