"""
边界情况测试：不寻常的输入、极端值、组合异常
这类测试是 QA 工作中最有价值的部分
"""
import pytest
from discount_engine import (
    Product, CartItem, DiscountEngine,
    PercentageDiscount, FixedDiscount,
)


class TestEdgeCases:

    def test_single_item_cart(self):
        item = CartItem(Product("Solo", 9.99), 1)
        result = DiscountEngine().add_rule(PercentageDiscount(10)).checkout([item])
        assert result.subtotal == 9.99
        assert result.final_price == round(9.99 * 0.9, 2)

    def test_final_price_never_negative(self):
        # FixedDiscount 远超商品价格，最终应为 0，不会是负数
        item = CartItem(Product("Cheap", 5.00), 1)
        result = DiscountEngine().add_rule(FixedDiscount(100)).checkout([item])
        assert result.final_price == 0.00

    def test_discount_exceeds_subtotal_in_stacking(self):
        # 两个叠加折扣超过小计时，最终价格 >= 0
        item = CartItem(Product("Item", 10.00), 1)
        result = (
            DiscountEngine()
            .add_rule(FixedDiscount(8))   # 10 - 8 = 2
            .add_rule(FixedDiscount(5))   # 2 - 5 → 实际只减2（不超过剩余）
            .checkout([item])
        )
        assert result.final_price == 0.00

    def test_same_rule_added_twice(self):
        # 同一规则加两次，叠加计算
        item = CartItem(Product("Item", 100.00), 1)
        result = (
            DiscountEngine()
            .add_rule(PercentageDiscount(10))  # 100 * 10% = 10 → 90
            .add_rule(PercentageDiscount(10))  # 90  * 10% = 9  → 81
            .checkout([item])
        )
        assert result.final_price == 81.00

    def test_very_large_quantity(self):
        item = CartItem(Product("Bulk", 1.00), 10_000)
        result = DiscountEngine().add_rule(PercentageDiscount(50)).checkout([item])
        assert result.subtotal == 10_000.00
        assert result.final_price == 5_000.00

    def test_high_precision_price_no_crash(self):
        # 不测精确值，只确保不崩溃、结果合理
        item = CartItem(Product("Precise", 19.999), 3)
        result = DiscountEngine().add_rule(PercentageDiscount(10)).checkout([item])
        assert result.final_price > 0

    def test_mixed_categories_in_cart(self):
        items = [
            CartItem(Product("Shampoo", 18.00, "haircare"), 1),
            CartItem(Product("Lipstick", 25.00, "makeup"), 1),
            CartItem(Product("Sunscreen", 30.00, "skincare"), 1),
        ]
        result = DiscountEngine().add_rule(FixedDiscount(10)).checkout(items)
        assert result.subtotal == 73.00
        assert result.final_price == 63.00

    def test_savings_percentage_is_zero_when_no_discount(self):
        item = CartItem(Product("Item", 50.00), 1)
        result = DiscountEngine().checkout([item])
        assert result.savings_percentage == 0.0

    def test_savings_percentage_is_100_when_free(self):
        item = CartItem(Product("Item", 10.00), 1)
        result = DiscountEngine().add_rule(FixedDiscount(10)).checkout([item])
        assert result.savings_percentage == 100.0
