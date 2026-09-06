from typing import Any, Dict
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient


class AmazonFinancesAPI:
    """Official Amazon SP-API Finances v0 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def get_financial_events_for_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch itemized fee deductions and taxes withheld for a specific order."""
        response = await self.client.execute_request(
            method="GET",
            path=f"/finances/v0/orders/{order_id}/financialEvents",
        )
        return response.get("payload", {}).get("FinancialEvents", {})

