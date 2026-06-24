# Python Contract Examples

These examples show executable boundary handling style. Use the shape, not the domain names.

## Contents

- [API Payload To Domain Model With Explicit Missing Data](#api-payload-to-domain-model-with-explicit-missing-data)
- [Database Row To Domain Entity With Boundary Validation](#database-row-to-domain-entity-with-boundary-validation)

## API Payload To Domain Model With Explicit Missing Data

`order_contract.py`:

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


def require_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or value == "":
        raise ContractError(f"ApiOrder.{field} is required")
    return value


def require_int(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if not isinstance(value, int):
        raise ContractError(f"ApiOrder.{field} must be an integer")
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
    return Order(
        id=require_string(payload, "order_id"),
        status=map_status(require_string(payload, "status")),
        total_cents=require_int(payload, "total_cents"),
        currency=require_string(payload, "currency"),
    )


def main() -> None:
    order = map_api_order(
        {
            "order_id": "ord_123",
            "status": "paid",
            "total_cents": 2599,
            "currency": "USD",
        }
    )

    assert order == Order(
        id="ord_123",
        status="Paid",
        total_cents=2599,
        currency="USD",
    )

    try:
        map_api_order({"order_id": "ord_124", "status": "pending", "total_cents": 1300})
    except ContractError as exc:
        assert "currency is required" in str(exc)
    else:
        raise AssertionError("Expected missing currency to fail")


if __name__ == "__main__":
    main()
```

Run:

```bash
python3 order_contract.py
```

## Database Row To Domain Entity With Boundary Validation

`account_contract.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal


AccountState = Literal["Active", "Suspended", "Closed"]


@dataclass(frozen=True)
class Account:
    id: str
    state: AccountState
    balance: Decimal
    currency: str


class ContractError(ValueError):
    pass


def require_string(row: dict[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or value == "":
        raise ContractError(f"account row field {field} is required")
    return value


def map_state(row_state: str) -> AccountState:
    match row_state:
        case "active":
            return "Active"
        case "suspended":
            return "Suspended"
        case "closed":
            return "Closed"
        case _:
            raise ContractError(f"Unknown account row state: {row_state}")


def map_account_row(row: dict[str, Any]) -> Account:
    return Account(
        id=require_string(row, "account_id"),
        state=map_state(require_string(row, "state")),
        balance=Decimal(require_string(row, "balance_cents")) / Decimal("100"),
        currency=require_string(row, "currency_code"),
    )


def main() -> None:
    account = map_account_row(
        {
            "account_id": "acct_123",
            "state": "active",
            "balance_cents": "1050",
            "currency_code": "USD",
        }
    )

    assert account == Account(
        id="acct_123",
        state="Active",
        balance=Decimal("10.5"),
        currency="USD",
    )

    try:
        map_account_row(
            {
                "account_id": "acct_456",
                "state": "paused",
                "balance_cents": "0",
                "currency_code": "USD",
            }
        )
    except ContractError as exc:
        assert "Unknown account row state" in str(exc)
    else:
        raise AssertionError("Expected unknown account state to fail")


if __name__ == "__main__":
    main()
```

Run:

```bash
python3 account_contract.py
```
