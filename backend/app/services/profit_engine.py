from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass(frozen=True)
class UnitProfitInput:
    """Input parameters for unit economics calculation."""
    selling_price: Decimal
    product_cost: Decimal
    marketplace_fees: Decimal
    advertising_cost: Decimal = Decimal("0.00")
    shipping_cost: Decimal = Decimal("0.00")
    returns_cost: Decimal = Decimal("0.00")
    packaging_cost: Decimal = Decimal("0.00")
    other_cost: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class ProfitResult:
    """Computed profit metrics."""
    gross_revenue: Decimal
    total_costs: Decimal
    product_cost: Decimal
    marketplace_fees: Decimal
    shipping_cost: Decimal
    advertising_cost: Decimal
    returns_cost: Decimal
    packaging_cost: Decimal
    other_expenses: Decimal
    net_profit: Decimal
    profit_margin_percentage: Decimal  # e.g., Decimal("24.92")


class ProfitEngine:
    """Deterministic, auditable profit calculation engine using Decimal precision."""

    TWO_PLACES = Decimal("0.01")
    FOUR_PLACES = Decimal("0.0001")

    @classmethod
    def round_currency(cls, value: Decimal) -> Decimal:
        """Round currency value to two decimal places."""
        return value.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_unit_profit(cls, data: UnitProfitInput) -> ProfitResult:
        """
        Calculate net profit and margin for a single SKU/unit.
        
        Formula:
          Revenue
          - Product Cost
          - Packaging Cost
          - Marketplace Fees
          - Shipping / Fulfillment Cost
          - Advertising Cost
          - Returns / Refund Cost
          - Other Cost
          = Net Profit
          
          Margin % = (Net Profit / Revenue) * 100
        """
        selling_price = cls.round_currency(data.selling_price)
        product_cost = cls.round_currency(data.product_cost)
        packaging_cost = cls.round_currency(data.packaging_cost)
        marketplace_fees = cls.round_currency(data.marketplace_fees)
        shipping_cost = cls.round_currency(data.shipping_cost)
        ad_cost = cls.round_currency(data.advertising_cost)
        returns_cost = cls.round_currency(data.returns_cost)
        other_cost = cls.round_currency(data.other_cost)

        total_costs = (
            product_cost
            + packaging_cost
            + marketplace_fees
            + shipping_cost
            + ad_cost
            + returns_cost
            + other_cost
        )

        net_profit = selling_price - total_costs

        if selling_price > Decimal("0.00"):
            raw_margin = (net_profit / selling_price) * Decimal("100")
            profit_margin = cls.round_currency(raw_margin)
        else:
            profit_margin = Decimal("0.00")

        return ProfitResult(
            gross_revenue=selling_price,
            total_costs=total_costs,
            product_cost=product_cost,
            packaging_cost=packaging_cost,
            marketplace_fees=marketplace_fees,
            shipping_cost=shipping_cost,
            advertising_cost=ad_cost,
            returns_cost=returns_cost,
            other_expenses=other_cost,
            net_profit=net_profit,
            profit_margin_percentage=profit_margin,
        )

    @classmethod
    def calculate_portfolio_profit(
        cls,
        total_revenue: Decimal,
        total_product_costs: Decimal,
        total_packaging_costs: Decimal,
        total_marketplace_fees: Decimal,
        total_shipping_costs: Decimal,
        total_advertising_costs: Decimal,
        total_returns_costs: Decimal,
        total_other_expenses: Decimal,
    ) -> ProfitResult:
        """Aggregate portfolio-level profitability across all orders and expenses."""
        revenue = cls.round_currency(total_revenue)
        p_costs = cls.round_currency(total_product_costs)
        pkg_costs = cls.round_currency(total_packaging_costs)
        fees = cls.round_currency(total_marketplace_fees)
        shipping = cls.round_currency(total_shipping_costs)
        ads = cls.round_currency(total_advertising_costs)
        returns = cls.round_currency(total_returns_costs)
        other = cls.round_currency(total_other_expenses)

        total_costs = p_costs + pkg_costs + fees + shipping + ads + returns + other
        net_profit = revenue - total_costs

        if revenue > Decimal("0.00"):
            raw_margin = (net_profit / revenue) * Decimal("100")
            profit_margin = cls.round_currency(raw_margin)
        else:
            profit_margin = Decimal("0.00")

        return ProfitResult(
            gross_revenue=revenue,
            total_costs=total_costs,
            product_cost=p_costs,
            packaging_cost=pkg_costs,
            marketplace_fees=fees,
            shipping_cost=shipping,
            advertising_cost=ads,
            returns_cost=returns,
            other_expenses=other,
            net_profit=net_profit,
            profit_margin_percentage=profit_margin,
        )
