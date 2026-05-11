"""
测试数据模型：Product、CartItem、Coupon
覆盖：正常创建、字段验证、边界值、异常
"""
import pytest
from datetime import date

from discount_engine import Product, CartItem, Coupon


class TestProduct:
    def test_create_basic(self):
        p = Product("Shampoo", 18.00)
        assert p.name == "Shampoo"
        assert p.price == 18.00
        assert p.category == "general"

    def test_create_with_category(self):
        p = Product("Shampoo", 18.00, "haircare")
        assert p.category == "haircare"

    def test_zero_price_allowed(self):
        p = Product("Free Sample", 0.0)
        assert p.price == 0.0

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="negative"):
            Product("Bad Item", -5.00)

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            Product("   ", 10.00)

    def test_name_with_spaces_is_fine(self):
        p = Product("All Soft Shampoo", 22.00)
        assert p.name == "All Soft Shampoo"


class TestCartItem:
    def test_subtotal_single(self, shampoo):
        item = CartItem(shampoo, 1)
        assert item.subtotal == 18.00

    def test_subtotal_multiple(self, shampoo):
        item = CartItem(shampoo, 3)
        assert item.subtotal == 54.00

    def test_zero_quantity_raises(self, shampoo):
        with pytest.raises(ValueError, match="positive"):
            CartItem(shampoo, 0)

    def test_negative_quantity_raises(self, shampoo):
        with pytest.raises(ValueError, match="positive"):
            CartItem(shampoo, -1)

    def test_large_quantity(self, shampoo):
        item = CartItem(shampoo, 1000)
        assert item.subtotal == 18000.00


class TestCoupon:
    def test_valid_percentage_coupon(self):
        c = Coupon("SAVE10", "percentage", 10)
        valid, msg = c.is_valid(100)
        assert valid is True
        assert msg == "Valid"

    def test_valid_fixed_coupon(self):
        c = Coupon("FLAT5", "fixed", 5)
        valid, _ = c.is_valid(50)
        assert valid is True

    def test_expired_coupon(self):
        c = Coupon("OLD", "fixed", 10, expiry=date(2020, 1, 1))
        valid, msg = c.is_valid(100)
        assert valid is False
        assert "expired" in msg.lower()

    def test_min_purchase_not_met(self):
        c = Coupon("MIN50", "fixed", 10, min_purchase=50.0)
        valid, msg = c.is_valid(30.0)
        assert valid is False
        assert "minimum" in msg.lower()

    def test_min_purchase_exact_threshold(self):
        c = Coupon("MIN50", "fixed", 10, min_purchase=50.0)
        valid, _ = c.is_valid(50.0)
        assert valid is True

    def test_max_uses_reached(self):
        c = Coupon("ONCE", "fixed", 5, max_uses=1, used_count=1)
        valid, msg = c.is_valid(100)
        assert valid is False
        assert "maximum" in msg.lower()

    def test_unlimited_uses(self):
        c = Coupon("UNLIM", "fixed", 5, max_uses=-1, used_count=9999)
        valid, _ = c.is_valid(100)
        assert valid is True

    def test_percentage_over_100_raises(self):
        with pytest.raises(ValueError):
            Coupon("BAD", "percentage", 110)

    def test_zero_value_raises(self):
        with pytest.raises(ValueError, match="positive"):
            Coupon("ZERO", "fixed", 0)

    def test_negative_value_raises(self):
        with pytest.raises(ValueError, match="positive"):
            Coupon("NEG", "fixed", -5)

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid discount_type"):
            Coupon("BAD", "mystery", 10)
