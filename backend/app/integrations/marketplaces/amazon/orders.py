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
        last_updated_after: Optional[datetime] = None,
        order_statuses: Optional[List[str]] = None,
        fulfillment_channels: Optional[List[str]] = None,
        max_results_per_page: int = 100,
        max_pages: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Call /orders/v0/orders for Indian marketplace with NextToken automatic pagination.
        """
        params: Dict[str, Any] = {
            "MarketplaceIds": self.client.INDIA_MARKETPLACE_ID,
            "MaxResultsPerPage": max_results_per_page,
        }
        if created_after:
            params["CreatedAfter"] = created_after.isoformat()
        if last_updated_after:
            params["LastUpdatedAfter"] = last_updated_after.isoformat()
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)
        if fulfillment_channels:
            params["FulfillmentChannels"] = ",".join(fulfillment_channels)

        all_orders: List[Dict[str, Any]] = []
        page = 0

        while page < max_pages:
            page += 1
            response = await self.client.execute_request(
                method="GET",
                path="/orders/v0/orders",
                params=params,
            )
            payload = response.get("payload", {})
            orders = payload.get("Orders", [])
            all_orders.extend(orders)

            next_token = payload.get("NextToken")
            if next_token and not self.client.mock_mode:
                params = {"NextToken": next_token}
            else:
                break

        return all_orders

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single order by AmazonOrderId (/orders/v0/orders/{orderId})."""
        response = await self.client.execute_request(
            method="GET",
            path=f"/orders/v0/orders/{order_id}",
        )
        return response.get("payload")

    async def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        """Call /orders/v0/orders/{orderId}/orderItems with NextToken pagination."""
        all_items: List[Dict[str, Any]] = []
        params: Dict[str, Any] = {}

        while True:
            response = await self.client.execute_request(
                method="GET",
                path=f"/orders/v0/orders/{order_id}/orderItems",
                params=params if params else None,
            )
            payload = response.get("payload", {})
            items = payload.get("OrderItems", [])
            all_items.extend(items)

            next_token = payload.get("NextToken")
            if next_token and not self.client.mock_mode:
                params = {"NextToken": next_token}
            else:
                break

        return all_items

    async def get_order_address(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Call /orders/v0/orders/{orderId}/address."""
        response = await self.client.execute_request(
            method="GET",
            path=f"/orders/v0/orders/{order_id}/address",
        )
        return response.get("payload", {}).get("ShippingAddress")

