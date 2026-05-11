"""
测试 DiscountEngine（集成测试）
验证多个规则组合在一起时的行为
"""
import pytest
from discount_engine import (
    Product, CartItem, DiscountEngine,
    PercentageDiscount, FixedDiscount, ThresholdDiscount, BuyXGetYDiscount,
)


class TestCheckoutBasics:

    def test_no_rules_returns_subtotal(self, basic_cart, engine):
        result = engine.checkout(basic_cart)
        assert result.subtotal == 38.00
        assert result.final_price == 38.00
        assert result.total_discount == 0.00
        assert result.discounts == []

    def test_empty_cart_raises(self, engine):
        with pytest.raises(ValueError, match="empty"):
            engine.checkout([])

    def test_result_has_all_fields(self, basic_cart, engine):
        engine.add_rule(PercentageDiscount(10))
        result = engine.checkout(basic_cart)
        assert hasattr(result, "subtotal")
        assert hasattr(result, "discounts")
        assert hasattr(result, "total_discount")
        assert hasattr(result, "final_price")
        assert hasattr(result, "savings_percentage")


class TestSingleRule:

    def test_percentage_discount(self, basic_cart, engine):
        engine.add_rule(PercentageDiscount(10))
        result = engine.checkout(basic_cart)
        assert result.final_price == 34.20
        assert result.total_discount == 3.80

    def test_fixed_discount(self, basic_cart, engine):
        engine.add_rule(FixedDiscount(10))
        result = engine.checkout(basic_cart)
        assert result.final_price == 28.00
        assert result.total_discount == 10.00

    def test_threshold_not_met(self, basic_cart, engine):
        engine.add_rule(ThresholdDiscount(100, 20))
        result = engine.checkout(basic_cart)  # 38 < 100
        assert result.total_discount == 0.00
        assert result.final_price == 38.00

    def test_threshold_met(self, large_cart, engine):
        engine.add_rule(ThresholdDiscount(100, 20))
        result = engine.checkout(large_cart)  # 101 >= 100
        assert result.total_discount == 20.00

    def test_savings_percentage_calculation(self, basic_cart, engine):
        engine.add_rule(FixedDiscount(19))  # 19 off 38 = 50%
        result = engine.checkout(basic_cart)
        assert result.savings_percentage == 50.0


class TestStackableRules:

    def test_two_rules_applied_sequentially(self, basic_cart, engine):
        # 第一条：38.00 * 10% = 3.80，剩 34.20
        # 第二条：34.20 - 5.00 = 29.20
        engine.add_rule(PercentageDiscount(10))
        engine.add_rule(FixedDiscount(5))
        result = engine.checkout(basic_cart)
        assert result.final_price == 29.20
        assert len(result.discounts) == 2

    def test_three_rules(self, large_cart, engine):
        # large_cart 小计 = 101.00
        engine.add_rule(ThresholdDiscount(100, 10))  # 101 >= 100 → -10 = 91
        engine.add_rule(PercentageDiscount(5))        # 91 * 5% = 4.55 → 86.45
        engine.add_rule(FixedDiscount(1))              # 86.45 - 1 = 85.45
        result = engine.checkout(large_cart)
        assert result.final_price == 85.45
        assert len(result.discounts) == 3

    def test_order_matters_for_stacking(self, basic_cart):
        # 先百分比后固定 vs 先固定后百分比，结果不同
        e1 = DiscountEngine()
        e1.add_rule(PercentageDiscount(10))  # 38 * 10% = 3.8 → 34.2
        e1.add_rule(FixedDiscount(5))         # 34.2 - 5 = 29.2
        r1 = e1.checkout(basic_cart)

        e2 = DiscountEngine()
        e2.add_rule(FixedDiscount(5))         # 38 - 5 = 33
        e2.add_rule(PercentageDiscount(10))  # 33 * 10% = 3.3 → 29.7
        r2 = e2.checkout(basic_cart)

        assert r1.final_price != r2.final_price

    def test_zero_discount_rule_not_added_to_breakdown(self, basic_cart, engine):
        engine.add_rule(ThresholdDiscount(1000, 50))  # 38 < 1000，不触发
        engine.add_rule(FixedDiscount(5))
        result = engine.checkout(basic_cart)
        # 只有 FixedDiscount 产生了折扣
        assert len(result.discounts) == 1


class TestNonStackableMode:

    def test_applies_best_discount_only(self, basic_cart):
        engine = DiscountEngine(stackable=False)
        engine.add_rule(PercentageDiscount(5))   # 38 * 5% = 1.90
        engine.add_rule(FixedDiscount(10))         # flat $10 ← 更优
        result = engine.checkout(basic_cart)
        assert result.total_discount == 10.00
        assert len(result.discounts) == 1

    def test_no_rules_non_stackable(self, basic_cart):
        engine = DiscountEngine(stackable=False)
        result = engine.checkout(basic_cart)
        assert result.total_discount == 0.00
        assert result.discounts == []


class TestFluentInterface:

    def test_chained_add_rule(self, basic_cart):
        result = (
            DiscountEngine()
            .add_rule(PercentageDiscount(10))
            .add_rule(FixedDiscount(2))
            .checkout(basic_cart)
        )
        # 38 * 10% = 3.8 → 34.2 - 2 = 32.2
        assert result.final_price == 32.20
