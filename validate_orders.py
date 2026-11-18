"""AI-assisted, synthetic-data learning sample; no client or production claims."""
import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal

ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
AMOUNT = re.compile(r"[0-9]{1,9}(?:\.[0-9]{1,2})?\Z")


@dataclass(frozen=True)
class Accepted:
    source_end_line: int
    order_id: str
    amount: str


@dataclass(frozen=True)
class Rejected:
    source_end_line: int
    reason: str


@dataclass(frozen=True)
class Report:
    accepted: tuple[Accepted, ...]
    rejected: tuple[Rejected, ...]


def validate_orders(text: str) -> Report:
    """Validate comma-delimited text without modifying files or calling services.

    Policy: exact two-column header; ASCII identifier; nonnegative amount with
    up to nine integer digits/two decimal places; first valid identifier wins.
    Entire blank lines are ignored by csv.reader. Header-only input is valid.
    Bad CSV syntax rejects the whole input; bad business rows are quarantined.
    Line numbers identify the last physical line consumed by each record.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    reader = csv.reader(io.StringIO(text.removeprefix("\ufeff"), newline=""), strict=True)
    accepted, rejected, seen = [], [], set()
    try:
        if next(reader, None) != ["order_id", "amount"]:
            raise ValueError("expected exact header: order_id,amount")
        for row in reader:
            if not row:
                continue
            end_line = reader.line_num
            if len(row) != 2:
                rejected.append(Rejected(end_line, "expected two fields"))
                continue
            order_id, amount = (field.strip() for field in row)
            if not ID.fullmatch(order_id):
                rejected.append(Rejected(end_line, "invalid order_id"))
            elif not AMOUNT.fullmatch(amount):
                rejected.append(Rejected(end_line, "invalid amount"))
            elif order_id in seen:
                rejected.append(Rejected(end_line, "duplicate order_id"))
            else:
                seen.add(order_id)
                accepted.append(Accepted(end_line, order_id, f"{Decimal(amount):.2f}"))
    except csv.Error as error:
        raise ValueError(f"malformed CSV near line {reader.line_num}") from error
    return Report(tuple(accepted), tuple(rejected))
