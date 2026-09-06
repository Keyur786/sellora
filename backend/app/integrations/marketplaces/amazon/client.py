import asyncio
import logging
import random
from typing import Any, Dict, Optional
import httpx

from app.integrations.marketplaces.amazon.auth import AmazonLWAAuth

logger = logging.getLogger(__name__)


class AmazonSPAPIClient:
    """Official Amazon Selling Partner API (SP-API) HTTP Client with rate-limit retries and India endpoint support."""

    # India marketplace endpoint (EU region)
    BASE_URL = "https://sellingpartnerapi-eu.amazon.com"
    INDIA_MARKETPLACE_ID = "A21TJRUUN4KGV"

    def __init__(
        self,
        refresh_token: str = "",
        client_id: str = "",
        client_secret: str = "",
        mock_mode: bool = True,
    ):
        self.refresh_token = refresh_token
        self.mock_mode = mock_mode or not (client_id and client_secret and refresh_token and not refresh_token.startswith("mock_"))
        self.auth = AmazonLWAAuth(client_id=client_id, client_secret=client_secret)

    async def execute_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes an authorized request against Amazon SP-API.
        Handles HTTP 429 rate limit backoff with jitter.
        """
        if self.mock_mode:
            return await self._get_mock_response(path, params)

        access_token = await self.auth.get_access_token(self.refresh_token)
        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "User-Agent": "Sellora/1.0 (Language=Python/3.11; Platform=Linux)",
        }

        url = f"{self.BASE_URL}{path}"
        backoff = 1.0

        async with httpx.AsyncClient(timeout=20.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )

                    if response.status_code == 429:
                        if attempt == max_retries:
                            response.raise_for_status()
                        sleep_time = backoff + random.uniform(0.1, 0.5)
                        logger.warning(f"SP-API 429 Rate Limit hit for {path}. Backing off for {sleep_time:.2f}s...")
                        await asyncio.sleep(sleep_time)
                        backoff *= 2.0
                        continue

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < max_retries:
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                        continue
                    raise

        return {}

    async def _get_mock_response(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provides realistic mock responses mirroring official Amazon SP-API documentation."""
        if path.endswith("/orderItems"):
            return {
                "payload": {
                    "OrderItems": [
                        {
                            "ASIN": "B08N5WRWNW",
                            "SellerSKU": "CU-BOTTLE-1000ML",
                            "OrderItemId": "ITEM-9988112",
                            "Title": "Pure Copper Hammered Water Bottle 1000ml",
                            "QuantityOrdered": 1,
                            "ItemPrice": {"CurrencyCode": "INR", "Amount": "999.00"},
                            "ItemTax": {"CurrencyCode": "INR", "Amount": "152.38"},
                            "ShippingPrice": {"CurrencyCode": "INR", "Amount": "0.00"},
                        }
                    ]
                }
            }
        elif path.endswith("/financialEvents"):
            return {
                "payload": {
                    "FinancialEvents": {
                        "ShipmentEventList": [
                            {
                                "AmazonOrderId": "402-8877112-9900123",
                                "ShipmentItemList": [
                                    {
                                        "SellerSKU": "CU-BOTTLE-1000ML",
                                        "QuantityShipped": 1,
                                        "ItemChargeList": [
                                            {"ChargeType": "Principal", "ChargeAmount": {"CurrencyCode": "INR", "CurrencyAmount": 999.00}},
                                            {"ChargeType": "Tax", "ChargeAmount": {"CurrencyCode": "INR", "CurrencyAmount": 152.38}},
                                        ],
                                        "ItemFeeList": [
                                            {"FeeType": "Commission", "FeeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -119.88}},
                                            {"FeeType": "FixedClosingFee", "FeeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -25.00}},
                                            {"FeeType": "WeightHandlingFee", "FeeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -75.00}},
                                        ],
                                        "ItemTaxWithheldList": [
                                            {
                                                "TaxesWithheld": [
                                                    {"ChargeType": "TCS-CGST", "ChargeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -5.00}},
                                                    {"ChargeType": "TCS-SGST", "ChargeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -5.00}},
                                                    {"ChargeType": "TDS-194O", "ChargeAmount": {"CurrencyCode": "INR", "CurrencyAmount": -1.00}},
                                                ]
                                            }
                                        ],
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        elif "/orders" in path:
            return {
                "payload": {
                    "Orders": [
                        {
                            "AmazonOrderId": "402-8877112-9900123",
                            "PurchaseDate": "2026-09-04T10:15:30Z",
                            "LastUpdateDate": "2026-09-04T18:00:00Z",
                            "OrderStatus": "Shipped",
                            "FulfillmentChannel": "MFN",  # Easy Ship
                            "SalesChannel": "Amazon.in",
                            "OrderTotal": {"CurrencyCode": "INR", "Amount": "999.00"},
                            "NumberOfItemsShipped": 1,
                            "ShippingAddress": {
                                "City": "Bengaluru",
                                "StateOrRegion": "Karnataka",
                                "PostalCode": "560001",
                                "CountryCode": "IN",
                            },
                        },
                        {
                            "AmazonOrderId": "402-5544332-1122334",
                            "PurchaseDate": "2026-09-05T14:20:00Z",
                            "LastUpdateDate": "2026-09-05T19:30:00Z",
                            "OrderStatus": "Delivered",
                            "FulfillmentChannel": "AFN",  # FBA
                            "SalesChannel": "Amazon.in",
                            "OrderTotal": {"CurrencyCode": "INR", "Amount": "1499.00"},
                            "NumberOfItemsShipped": 1,
                            "ShippingAddress": {
                                "City": "Mumbai",
                                "StateOrRegion": "Maharashtra",
                                "PostalCode": "400001",
                                "CountryCode": "IN",
                            },
                        },
                    ]
                }
            }
        return {"payload": {}}
