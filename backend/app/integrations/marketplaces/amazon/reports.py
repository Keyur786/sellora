import asyncio
import csv
import gzip
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient

logger = logging.getLogger(__name__)


class AmazonReportsAPI:
    """Official Amazon SP-API Reports 2021-06-30 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def create_report(
        self,
        report_type: str,
        data_start_time: Optional[datetime] = None,
        data_end_time: Optional[datetime] = None,
    ) -> str:
        """
        Request generation of an official Amazon report.
        Returns reportId.
        """
        json_data: Dict[str, Any] = {
            "reportType": report_type,
            "marketplaceIds": [self.client.INDIA_MARKETPLACE_ID],
        }
        if data_start_time:
            json_data["dataStartTime"] = data_start_time.isoformat()
        if data_end_time:
            json_data["dataEndTime"] = data_end_time.isoformat()

        response = await self.client.execute_request(
            method="POST",
            path="/reports/2021-06-30/reports",
            json_data=json_data,
        )
        return response.get("reportId", "")

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Check status of a generated report (/reports/2021-06-30/reports/{reportId})."""
        return await self.client.execute_request(
            method="GET",
            path=f"/reports/2021-06-30/reports/{report_id}",
        )

    async def get_report_document(self, report_document_id: str) -> Dict[str, Any]:
        """Fetch pre-signed S3 download URL for the report document."""
        return await self.client.execute_request(
            method="GET",
            path=f"/reports/2021-06-30/documents/{report_document_id}",
        )

    async def download_report_data(self, url: str, compression: Optional[str] = None) -> List[Dict[str, str]]:
        """Download document from S3 URL and parse TSV/CSV format into list of dictionaries."""
        if self.client.mock_mode or "mock-report" in url:
            return [
                {
                    "return-date": "2026-09-04T10:00:00Z",
                    "order-id": "402-8877112-9900123",
                    "sku": "CU-BOTTLE-1000ML",
                    "asin": "B08N5WRWNW",
                    "fnsku": "X001ABCD12",
                    "product-name": "Pure Copper Hammered Water Bottle 1000ml",
                    "quantity": "1",
                    "fulfillment-center-id": "BLR1",
                    "detailed-disposition": "CUSTOMER_DAMAGED",
                    "reason": "Defective: Leaking from bottom rim",
                    "status": "Reimbursed",
                },
                {
                    "return-date": "2026-09-05T15:30:00Z",
                    "order-id": "402-5544332-1122334",
                    "sku": "AUDIO-AIR-PODS-PRO",
                    "asin": "B09H2S872K",
                    "fnsku": "X002WXYZ34",
                    "product-name": "True Wireless Earbuds with ENC",
                    "quantity": "1",
                    "fulfillment-center-id": "DEL4",
                    "detailed-disposition": "DEFECTIVE",
                    "reason": "Left earbud audio cutting out after 5 minutes",
                    "status": "Repackaged",
                },
            ]

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url)
            response.raise_for_status()
            content = response.content

            if compression == "GZIP":
                content = gzip.decompress(content)

            text_data = content.decode("utf-8", errors="replace")
            # Auto-detect delimiter (tab vs comma)
            sample = text_data[:1024]
            delimiter = "\t" if "\t" in sample else ","
            reader = csv.DictReader(io.StringIO(text_data), delimiter=delimiter)
            return list(reader)

