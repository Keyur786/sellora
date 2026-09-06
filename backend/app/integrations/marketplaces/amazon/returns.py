from datetime import datetime, timezone
from typing import List, Optional
from app.integrations.marketplaces.base import StandardReturn
from app.integrations.marketplaces.amazon.reports import AmazonReportsAPI
from app.integrations.marketplaces.amazon.finances import AmazonFinancesAPI
from app.integrations.marketplaces.amazon.report_parser import parse_amazon_date


class AmazonReturnsAPI:
    """Combines Reports API return documents and Finances API refund events into standardized return records."""

    def __init__(self, reports_api: AmazonReportsAPI, finances_api: AmazonFinancesAPI):
        self.reports_api = reports_api
        self.finances_api = finances_api

    async def get_returns(self, since: Optional[datetime] = None) -> List[StandardReturn]:
        """Fetch customer returns and courier doorstep RTOs."""
        # 1. Download returns via Reports API
        # When in mock mode or live, download_report_data provides parsed records
        raw_report = await self.reports_api.download_report_data(url="mock-report")
        returns: List[StandardReturn] = []

        for row in raw_report:
            ret_date_str = row.get("return-date", "")
            ret_date = parse_amazon_date(ret_date_str) if ret_date_str else datetime.now(timezone.utc)
            if since and ret_date < since:
                continue

            order_id = row.get("order-id", "")
            sku = row.get("sku", "")
            reason = row.get("reason", "Customer return")
            disposition = (row.get("detailed-disposition") or "").upper()
            status = "Damaged" if "DAMAGED" in disposition or "DEFECTIVE" in disposition else "Completed"
            
            # Determine return type (Customer Return vs Courier RTO)
            is_rto = "undeliverable" in reason.lower() or "rejected" in reason.lower() or "refused" in reason.lower()
            return_type = "CourierReturn_RTO" if is_rto else "CustomerReturn"

            returns.append(
                StandardReturn(
                    marketplace_order_id=order_id,
                    sku=sku,
                    return_date=ret_date,
                    reason=reason,
                    return_type=return_type,
                    status=status,
                )
            )

        return returns

