from datetime import datetime
from typing import Any, Dict, List, Optional
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient


class AmazonFinancesAPI:
    """Official Amazon SP-API Finances v0 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def get_financial_events_for_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch itemized fee deductions, refunds, and taxes withheld for a specific order."""
        response = await self.client.execute_request(
            method="GET",
            path=f"/finances/v0/orders/{order_id}/financialEvents",
        )
        return response.get("payload", {}).get("FinancialEvents", {})

    async def list_financial_events(
        self,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        max_results_per_page: int = 100,
    ) -> Dict[str, Any]:
        """Fetch store-wide financial events by date range (/finances/v0/financialEvents)."""
        params: Dict[str, Any] = {"MaxResultsPerPage": max_results_per_page}
        if posted_after:
            params["PostedAfter"] = posted_after.isoformat()
        if posted_before:
            params["PostedBefore"] = posted_before.isoformat()

        response = await self.client.execute_request(
            method="GET",
            path="/finances/v0/financialEvents",
            params=params,
        )
        return response.get("payload", {}).get("FinancialEvents", {})

    async def list_financial_event_groups(
        self,
        started_after: Optional[datetime] = None,
        max_results_per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch bank settlement disbursement cycles (/finances/v0/financialEventGroups)."""
        params: Dict[str, Any] = {"MaxResultsPerPage": max_results_per_page}
        if started_after:
            params["FinancialEventGroupStartedAfter"] = started_after.isoformat()

        response = await self.client.execute_request(
            method="GET",
            path="/finances/v0/financialEventGroups",
            params=params,
        )
        return response.get("payload", {}).get("FinancialEventGroupList", [])

