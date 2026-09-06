from typing import Any, Dict, List, Optional
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient


class AmazonCatalogAPI:
    """Official Amazon SP-API Catalog Items 2022-04-01 Service."""

    def __init__(self, client: AmazonSPAPIClient):
        self.client = client

    async def get_catalog_item(
        self,
        asin: str,
        included_data: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch full catalog metadata for a specific ASIN.
        included_data: ['summaries', 'attributes', 'images', 'dimensions', 'classifications', 'productTypes']
        """
        if not included_data:
            included_data = ["summaries", "images", "classifications", "productTypes"]

        params = {
            "marketplaceIds": self.client.INDIA_MARKETPLACE_ID,
            "includedData": ",".join(included_data),
        }

        response = await self.client.execute_request(
            method="GET",
            path=f"/catalog/2022-04-01/items/{asin}",
            params=params,
        )
        return response

    async def search_catalog_items(
        self,
        keywords: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None,
        identifiers_type: str = "SKU",
        page_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search catalog items by keywords or identifiers (SKU, ASIN, UPC, EAN).
        """
        params: Dict[str, Any] = {
            "marketplaceIds": self.client.INDIA_MARKETPLACE_ID,
            "pageSize": page_size,
            "includedData": "summaries,images,classifications",
        }
        if keywords:
            params["keywords"] = ",".join(keywords)
        if identifiers:
            params["identifiers"] = ",".join(identifiers)
            params["identifiersType"] = identifiers_type

        response = await self.client.execute_request(
            method="GET",
            path="/catalog/2022-04-01/items",
            params=params,
        )
        return response.get("items", [])

