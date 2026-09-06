from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient


class AmazonOrdersAPI:
    """Official Amazon SP-API Orders v0 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def list_orders(
        self,
        created_after: Optional[datetime] = None,
        order_statuses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Call /orders/v0/orders for Indian marketplace."""
        params: Dict[str, Any] = {
            "MarketplaceIds": self.client.INDIA_MARKETPLACE_ID,
        }
        if created_after:
            params["CreatedAfter"] = created_after.isoformat()
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)

        response = await self.client.execute_request(
            method="GET",
            path="/orders/v0/orders",
            params=params,
        )
        return response.get("payload", {}).get("Orders", [])

    async def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        """Call /orders/v0/orders/{orderId}/orderItems."""
        response = await self.client.execute_request(
            method="GET",
            path=f"/orders/v0/orders/{order_id}/orderItems",
        )
        return response.get("payload", {}).get("OrderItems", [])

