# FastMCP Django Tool Design

Create tools as narrow application actions, not generic database access.

## Example

```python
# apps/core/mcp.py
from collections.abc import Callable
from typing import Annotated

from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, transaction
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field


class ResourceNotFound(Exception):
    """Safe not-found error for MCP clients."""


def get_current_actor_id() -> int:
    """Return the authenticated Django user ID from trusted MCP auth context."""
    raise PermissionDenied("Authentication is required")


def _order_summary(order_id: int, actor_id: int) -> dict:
    from apps.orders.models import Order

    try:
        order = Order.objects.select_related("customer").get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise ResourceNotFound("Order not found") from exc

    if not order.can_be_viewed_by_id(actor_id):
        raise PermissionDenied("Not allowed to view this order")

    return {
        "id": order.pk,
        "status": order.status,
        "customer": order.customer.name,
        "total_cents": order.total_cents,
    }


def create_mcp(
    actor_id_dependency: Callable[[], int] = get_current_actor_id,
) -> FastMCP:
    mcp = FastMCP("Project MCP", on_duplicate_tools="error")

    @mcp.tool(timeout=10)
    def get_order_summary(
        order_id: Annotated[int, Field(gt=0, description="Internal order ID")],
        actor_id: int = Depends(actor_id_dependency),
    ) -> dict:
        """Return a concise order summary the actor is allowed to view."""
        close_old_connections()
        try:
            return _order_summary(order_id=order_id, actor_id=actor_id)
        except ResourceNotFound:
            return {"error": "not_found", "message": "Order not found"}
        except PermissionDenied:
            return {
                "error": "forbidden",
                "message": "Not allowed to view this order",
            }
        finally:
            close_old_connections()

    @mcp.tool(timeout=20)
    def cancel_order(
        order_id: Annotated[int, Field(gt=0)],
        reason: Annotated[str, Field(min_length=3, max_length=500)],
        actor_id: int = Depends(actor_id_dependency),
    ) -> dict:
        """Cancel an order if the actor is allowed to do so."""
        close_old_connections()
        try:
            with transaction.atomic():
                from apps.orders.services import cancel_order_for_actor

                order = cancel_order_for_actor(
                    order_id=order_id,
                    actor_id=actor_id,
                    reason=reason,
                )
                transaction.on_commit(lambda: order.enqueue_cancellation_email())
                return {"id": order.pk, "status": order.status}
        except PermissionDenied:
            return {
                "error": "forbidden",
                "message": "Not allowed to cancel this order",
            }
        except ValueError:
            return {
                "error": "invalid_state",
                "message": "Order cannot be cancelled",
            }
        finally:
            close_old_connections()

    return mcp


mcp = create_mcp()
```

## Tool Contract Rules

- Use typed parameters, Pydantic `Field` constraints, docstrings, return type
  annotations, and small JSON-serializable return values.
- Use existing Django services and policy methods. Do not duplicate permission
  logic inside MCP modules when a project already has one source of truth.
- Keep writes idempotent where possible. Include explicit confirmation fields or
  idempotency keys for costly/destructive tools.
- Pass durable identifiers, not Django model instances, request objects, lazy
  querysets, open files, or huge payloads.
- Paginate and cap every list/search tool. Return stable IDs and summaries, not
  entire model dumps.
- Add `timeout=...` on slow or externally dependent tools and make long-running
  work enqueue a background job instead of holding the MCP request open.
- Never let the model provide privileged identity fields in production. Inject
  the current user/account from validated auth context or a trusted dependency.

## Django Async Rules

- A synchronous `def` FastMCP tool is usually simplest for Django ORM work.
  FastMCP dispatches sync tools without blocking the event loop, and the tool can
  use normal ORM, transactions, forms, and serializers.
- In an `async def` tool, do not call sync ORM or other async-unsafe Django code
  directly. Use Django async ORM methods (`aget`, `acreate`, `asave`,
  `async for`) when they cover the operation.
- Transactions do not work in Django async mode. Put transactional work in one
  synchronous helper and call it with `sync_to_async(..., thread_sensitive=True)`
  from the async tool.
- Do not set `DJANGO_ALLOW_ASYNC_UNSAFE` to make MCP tools work. Fix the calling
  boundary instead.
- Because MCP calls are not Django requests, there is no normal request
  lifecycle to clean database connections. For long-lived MCP processes, call
  `close_old_connections()` around ORM work or centralize connection cleanup in
  a thin helper that preserves function signatures.

## Resources And Prompts

- Use tools for permissioned data, mutations, searches, and any result that
  depends on the current user.
- Use resources for bounded, read-only, low-risk content such as public docs,
  product metadata, or static schemas. Do not publish private model tables as
  global resources unless every client may read them.
- Use prompts for reusable agent workflows such as "triage this customer", but
  keep prompts free of secrets and make them call tools rather than embedding
  stale database facts.
