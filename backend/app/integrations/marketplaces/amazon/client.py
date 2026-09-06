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
        elif "/catalog/2022-04-01/items" in path:
            return {
                "numberOfResults": 1,
                "items": [
                    {
                        "asin": "B08N5WRWNW",
                        "summaries": [
                            {
                                "marketplaceId": self.INDIA_MARKETPLACE_ID,
                                "brand": "Apex Ayurveda",
                                "itemName": "Pure Copper Hammered Water Bottle 1000ml",
                                "itemClassification": "BASE_PRODUCT",
                                "productType": "DRINKING_CUP",
                            }
                        ],
                        "images": [
                            {
                                "marketplaceId": self.INDIA_MARKETPLACE_ID,
                                "images": [
                                    {
                                        "variant": "MAIN",
                                        "link": "https://m.media-amazon.com/images/I/71xyz.jpg",
                                        "height": 500,
                                        "width": 500,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        elif "/fba/inventory/v1/summaries" in path:
            return {
                "payload": {
                    "granularity": {
                        "granularityType": "Marketplace",
                        "granularityId": self.INDIA_MARKETPLACE_ID,
                    },
                    "inventorySummaries": [
                        {
                            "asin": "B08N5WRWNW",
                            "fnSku": "X001ABCD12",
                            "sellerSku": "CU-BOTTLE-1000ML",
                            "condition": "NewItem",
                            "inventoryDetails": {
                                "fulfillableQuantity": 120,
                                "inboundWorkingQuantity": 30,
                                "inboundShippedQuantity": 50,
                                "inboundReceivingQuantity": 10,
                                "reservedQuantity": {
                                    "totalReservedQuantity": 15,
                                    "pendingCustomerOrderQuantity": 10,
                                    "pendingTransshipmentQuantity": 5,
                                    "fcProcessingQuantity": 0,
                                },
                                "unfulfillableQuantity": {
                                    "totalUnfulfillableQuantity": 2,
                                    "customerDamagedQuantity": 2,
                                    "warehouseDamagedQuantity": 0,
                                    "distributorDamagedQuantity": 0,
                                    "carrierDamagedQuantity": 0,
                                    "defectiveQuantity": 0,
                                    "expiredQuantity": 0,
                                },
                            },
                            "totalQuantity": 227,
                        },
                        {
                            "asin": "B09H2S872K",
                            "fnSku": "X002WXYZ34",
                            "sellerSku": "AUDIO-AIR-PODS-PRO",
                            "condition": "NewItem",
                            "inventoryDetails": {
                                "fulfillableQuantity": 45,
                                "inboundWorkingQuantity": 0,
                                "inboundShippedQuantity": 0,
                                "inboundReceivingQuantity": 0,
                                "reservedQuantity": {
                                    "totalReservedQuantity": 5,
                                    "pendingCustomerOrderQuantity": 5,
                                    "pendingTransshipmentQuantity": 0,
                                    "fcProcessingQuantity": 0,
                                },
                                "unfulfillableQuantity": {
                                    "totalUnfulfillableQuantity": 0,
                                    "customerDamagedQuantity": 0,
                                    "warehouseDamagedQuantity": 0,
                                    "distributorDamagedQuantity": 0,
                                    "carrierDamagedQuantity": 0,
                                    "defectiveQuantity": 0,
                                    "expiredQuantity": 0,
                                },
                            },
                            "totalQuantity": 50,
                        },
                    ],
                }
            }
        elif "/reports/2021-06-30/reports" in path:
            return {
                "reports": [
                    {
                        "reportId": "REPORT-998811-IN",
                        "reportType": "GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA",
                        "processingStatus": "DONE",
                        "reportDocumentId": "DOC-RET-8811",
                        "marketplaceIds": [self.INDIA_MARKETPLACE_ID],
                        "createdTime": "2026-09-05T12:00:00Z",
                    }
                ],
                "reportId": "REPORT-998811-IN",
            }
        elif "/reports/2021-06-30/documents" in path:
            return {
                "reportDocumentId": "DOC-RET-8811",
                "url": "https://tortuga-prod-eu.s3-eu-west-1.amazonaws.com/mock-report.tsv",
                "compressionAlgorithm": "GZIP",
            }
        elif "/finances/v0/financialEventGroups" in path:
            return {
                "payload": {
                    "FinancialEventGroupList": [
                        {
                            "FinancialEventGroupId": "GROUP-20260901-IN",
                            "ProcessingStatus": "Closed",
                            "FundTransferStatus": "Successful",
                            "OriginalTotal": {"CurrencyCode": "INR", "CurrencyAmount": 48520.00},
                            "BeginningBalance": {"CurrencyCode": "INR", "CurrencyAmount": 0.00},
                            "FinancialEventGroupStart": "2026-08-15T00:00:00Z",
                            "FinancialEventGroupEnd": "2026-08-31T23:59:59Z",
                        }
                    ]
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

    async def test_connection(self) -> Dict[str, Any]:
        """Test authentication and endpoint connectivity."""
        if self.mock_mode:
            return {
                "success": True,
                "connection_mode": "sandbox",
                "message": "Connected to Sellora Amazon India Developer Sandbox.",
                "marketplace_id": self.INDIA_MARKETPLACE_ID,
            }

        try:
            val_res = await self.auth.validate_credentials(self.refresh_token)
            if not val_res.get("valid"):
                return {
                    "success": False,
                    "connection_mode": "live",
                    "message": val_res.get("message", "LWA token validation failed."),
                    "marketplace_id": self.INDIA_MARKETPLACE_ID,
                }

            # Ping lightweight endpoint
            orders_res = await self.execute_request(
                method="GET",
                path="/orders/v0/orders",
                params={"MarketplaceIds": self.INDIA_MARKETPLACE_ID, "MaxResultsPerPage": 1},
            )
            return {
                "success": True,
                "connection_mode": "live",
                "message": "Successfully connected to Amazon India Selling Partner API (Live Endpoint).",
                "marketplace_id": self.INDIA_MARKETPLACE_ID,
                "orders_count": len(orders_res.get("payload", {}).get("Orders", [])),
            }
        except Exception as e:
            return {
                "success": False,
                "connection_mode": "live",
                "message": f"SP-API Ping failed: {str(e)}",
                "marketplace_id": self.INDIA_MARKETPLACE_ID,
            }
