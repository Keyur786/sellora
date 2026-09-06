from typing import Any, Dict, List, Optional
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient


class AmazonFBAInventoryAPI:
    """Official Amazon SP-API FBA Inventory Summaries v1 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def get_inventory_summaries(
        self,
        seller_skus: Optional[List[str]] = None,
        details: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch live FBA inventory levels for Indian fulfillment centers.
        Endpoint: /fba/inventory/v1/summaries
        """
        params: Dict[str, Any] = {
            "details": "true" if details else "false",
            "granularityType": "Marketplace",
            "granularityId": self.client.INDIA_MARKETPLACE_ID,
            "marketplaceIds": self.client.INDIA_MARKETPLACE_ID,
        }
        if seller_skus:
            params["sellerSkus"] = ",".join(seller_skus)

        all_summaries: List[Dict[str, Any]] = []

        while True:
            response = await self.client.execute_request(
                method="GET",
                path="/fba/inventory/v1/summaries",
                params=params,
            )
            payload = response.get("payload", {})
            summaries = payload.get("inventorySummaries", [])
            all_summaries.extend(summaries)

            next_token = response.get("pagination", {}).get("nextToken")
            if next_token and not self.client.mock_mode:
                params = {"nextToken": next_token}
            else:
                break

        return all_summaries

