from decimal import Decimal
import pytest
from app.services.profit_engine import ProfitEngine, UnitProfitInput


def test_unit_profit_exact_specification():
    """
    Verify the exact benchmark from specification:
    Selling price = ₹999
    Product cost = ₹350
    Marketplace fees = ₹180
    Advertising = ₹100
    Shipping = ₹80
    Returns = ₹40
    Expected:
    Net profit = ₹249
    Profit margin = 24.92%
    """
    data = UnitProfitInput(
        selling_price=Decimal("999.00"),
        product_cost=Decimal("350.00"),
        marketplace_fees=Decimal("180.00"),
        advertising_cost=Decimal("100.00"),
        shipping_cost=Decimal("80.00"),
        returns_cost=Decimal("40.00"),
    )
    result = ProfitEngine.calculate_unit_profit(data)

    assert result.net_profit == Decimal("249.00")
    assert result.profit_margin_percentage == Decimal("24.92")
    assert result.total_costs == Decimal("750.00")


def test_unit_profit_with_packaging_and_other_costs():
    """Verify inclusion of packaging and other per-unit costs."""
    data = UnitProfitInput(
        selling_price=Decimal("1500.00"),
        product_cost=Decimal("500.00"),
        packaging_cost=Decimal("30.00"),
        marketplace_fees=Decimal("250.00"),
        shipping_cost=Decimal("90.00"),
        advertising_cost=Decimal("120.00"),
        returns_cost=Decimal("50.00"),
        other_cost=Decimal("10.00"),
    )
    result = ProfitEngine.calculate_unit_profit(data)

    # 1500 - (500 + 30 + 250 + 90 + 120 + 50 + 10) = 1500 - 1050 = 450
    assert result.net_profit == Decimal("450.00")
    # 450 / 1500 * 100 = 30.00%
    assert result.profit_margin_percentage == Decimal("30.00")


def test_zero_selling_price_safety():
    """Ensure zero revenue does not cause ZeroDivisionError."""
    data = UnitProfitInput(
        selling_price=Decimal("0.00"),
        product_cost=Decimal("100.00"),
        marketplace_fees=Decimal("20.00"),
    )
    result = ProfitEngine.calculate_unit_profit(data)
    assert result.net_profit == Decimal("-120.00")
    assert result.profit_margin_percentage == Decimal("0.00")


def test_loss_making_product():
    """Ensure negative profit and negative margin are calculated accurately."""
    data = UnitProfitInput(
        selling_price=Decimal("500.00"),
        product_cost=Decimal("400.00"),
        marketplace_fees=Decimal("150.00"),
        shipping_cost=Decimal("60.00"),
    )
    result = ProfitEngine.calculate_unit_profit(data)
    # 500 - 610 = -110.00
    assert result.net_profit == Decimal("-110.00")
    # -110 / 500 * 100 = -22.00%
    assert result.profit_margin_percentage == Decimal("-22.00")


def test_portfolio_profit_aggregation():
    """Verify aggregated portfolio calculation."""
    res = ProfitEngine.calculate_portfolio_profit(
        total_revenue=Decimal("100000.00"),
        total_product_costs=Decimal("35000.00"),
        total_packaging_costs=Decimal("2500.00"),
        total_marketplace_fees=Decimal("18000.00"),
        total_shipping_costs=Decimal("8000.00"),
        total_advertising_costs=Decimal("10000.00"),
        total_returns_costs=Decimal("4000.00"),
        total_other_expenses=Decimal("2500.00"),
    )
    # Total costs: 35000+2500+18000+8000+10000+4000+2500 = 80000
    # Net profit: 20000 (20.00%)
    assert res.total_costs == Decimal("80000.00")
    assert res.net_profit == Decimal("20000.00")
    assert res.profit_margin_percentage == Decimal("20.00")
