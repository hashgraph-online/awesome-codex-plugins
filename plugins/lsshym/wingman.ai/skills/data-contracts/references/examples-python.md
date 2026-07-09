# Python Boundary Examples

Use this only for the shape of a focused boundary: source payload, receiver model, explicit validation, intentional enum mapping, and a small proof. Do not copy the domain names.

## Contents

- [Stable Receiver Mapping](#stable-receiver-mapping)

## Stable Receiver Mapping

`contract_example.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


class ApiOrder(TypedDict, total=False):
    order_id: str
    status: Literal["pending", "paid", "cancelled"]
    total_cents: int
    currency: str

OrderStatus = Literal["PendingPayment", "Paid", "Cancelled"]

@dataclass(frozen=True)
class Order:
    id: str
    status: OrderStatus
    total_cents: int
    currency: str


class ContractError(ValueError):
    pass


def require_str(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or value == "":
        raise ContractError(f"ApiOrder.{field} is required")
    return value


def map_status(status: str) -> OrderStatus:
    match status:
        case "pending":
            return "PendingPayment"
        case "paid":
            return "Paid"
        case "cancelled":
            return "Cancelled"
        case _:
            raise ContractError(f"Unsupported ApiOrder.status: {status}")


def map_api_order(payload: dict[str, Any]) -> Order:
    total_cents = payload.get("total_cents")
    if not isinstance(total_cents, int):
        raise ContractError("ApiOrder.total_cents must be an integer")

    return Order(
        id=require_str(payload, "order_id"),
        status=map_status(require_str(payload, "status")),
        total_cents=total_cents,
        currency=require_str(payload, "currency"),
    )


assert map_api_order(
    {"order_id": "ord_123", "status": "paid", "total_cents": 2599, "currency": "USD"}
) == Order(id="ord_123", status="Paid", total_cents=2599, currency="USD")

try:
    map_api_order({"order_id": "ord_124", "status": "pending", "total_cents": 1300})
except ContractError as exc:
    assert "currency is required" in str(exc)
else:
    raise AssertionError("Expected missing currency to fail")
```

Run:

```bash
python3 contract_example.py
```

Project use: replace the names, source shape, receiver model, error type, and test style with the project's existing patterns. If the receiver is local and display-only with identical meanings, prefer direct source fields or local aliases instead of this mapper.
