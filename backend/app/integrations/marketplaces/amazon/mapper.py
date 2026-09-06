from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.integrations.marketplaces.base import StandardOrder, StandardOrderItem, StandardFee
from app.integrations.marketplaces.amazon.report_parser import parse_decimal, parse_amazon_date


class AmazonSPAPIMapper:
    """Transforms official Amazon SP-API JSON payloads into standardized internal domain models."""

    @classmethod
    def map_order(
        cls,
        order_payload: Dict[str, Any],
        items_payload: List[Dict[str, Any]],
        finances_payload: Optional[Dict[str, Any]] = None,
    ) -> StandardOrder:
        order_id = order_payload.get("AmazonOrderId", "")
        order_date_str = order_payload.get("PurchaseDate", "")
        order_date = parse_amazon_date(order_date_str)
        status = order_payload.get("OrderStatus", "Pending")
        
        # MFN is Merchant Fulfillment (EasyShip / SelfShip), AFN is Amazon Fulfillment Network (FBA)
        f_channel = order_payload.get("FulfillmentChannel", "MFN")
        channel = "FBA" if f_channel == "AFN" else "EasyShip"

        total_data = order_payload.get("OrderTotal", {})
        total_amount = parse_decimal(total_data.get("Amount", "0.00"))
        currency = total_data.get("CurrencyCode", "INR")

        shipping_address = order_payload.get("ShippingAddress", {})
        city = shipping_address.get("City", "")
        state = shipping_address.get("StateOrRegion", "")
        postal_code = shipping_address.get("PostalCode", "")

        # Map Line Items & Fees
        standard_items: List[StandardOrderItem] = []
        for it in items_payload:
            sku = it.get("SellerSKU", "")
            title = it.get("Title", f"Amazon Item {sku}")
            qty = int(it.get("QuantityOrdered", 1))

            item_price = parse_decimal(it.get("ItemPrice", {}).get("Amount", "0.00"))
            tax_amount = parse_decimal(it.get("ItemTax", {}).get("Amount", "0.00"))
            ship_price = parse_decimal(it.get("ShippingPrice", {}).get("Amount", "0.00"))

            # Extract Fees from FinancialEvents if provided
            fees: List[StandardFee] = []
            if finances_payload:
                shipment_events = finances_payload.get("ShipmentEventList", [])
                for ev in shipment_events:
                    for s_item in ev.get("ShipmentItemList", []):
                        if s_item.get("SellerSKU") == sku:
                            # 1. ItemFeeList (Commission, Closing, WeightHandling)
                            for fee in s_item.get("ItemFeeList", []):
                                f_type = fee.get("FeeType", "MarketplaceFee")
                                f_amt = abs(parse_decimal(fee.get("FeeAmount", {}).get("CurrencyAmount", "0.00")))
                                fees.append(StandardFee(fee_type=f_type, amount=f_amt, currency=currency))
                            
                            # 2. Taxes Withheld (TCS, TDS)
                            for withheld_group in s_item.get("ItemTaxWithheldList", []):
                                for tax in withheld_group.get("TaxesWithheld", []):
                                    t_type = tax.get("ChargeType", "WithheldTax")
                                    t_amt = abs(parse_decimal(tax.get("ChargeAmount", {}).get("CurrencyAmount", "0.00")))
                                    fees.append(StandardFee(fee_type=t_type, amount=t_amt, currency=currency))

            standard_items.append(
                StandardOrderItem(
                    marketplace_item_id=it.get("OrderItemId", f"ITEM-{order_id}"),
                    sku=sku,
                    title=title,
                    quantity=qty,
                    item_price=item_price,
                    shipping_price=ship_price,
                    tax_amount=tax_amount,
                    fees=fees,
                )
            )

        return StandardOrder(
            marketplace_order_id=order_id,
            marketplace_type="amazon",
            order_date=order_date,
            status=status,
            fulfillment_channel=channel,
            total_amount=total_amount,
            currency=currency,
            customer_city=city,
            customer_state=state,
            postal_code=postal_code,
            items=standard_items,
        )
