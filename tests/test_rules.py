"""
测试所有折扣规则
重点展示 pytest 参数化：用一个测试函数跑多组数据
"""
import pytest
from discount_engine import Product, CartItem, Coupon
from discount_engine.rules import (
    PercentageDiscount,
    FixedDiscount,
    ThresholdDiscount,
    BuyXGetYDiscount,
    CouponDiscount,
)


# ------------------------------------------------------------------ #
#  PercentageDiscount                                                  #
# ------------------------------------------------------------------ #

class TestPercentageDiscount:

    # pytest.mark.parametrize：一个测试函数 × N 组数据 = N 条用例
    @pytest.mark.parametrize("percentage, subtotal, expected", [
        (10,  100.00, 10.00),   # 10% off 100
        (20,   50.00, 10.00),   # 20% off 50
        (100,  30.00, 30.00),   # 全额折扣
        (15,   38.00,  5.70),   # 非整数结果
        (50,    0.01,  0.01),   # 极小金额
    ])
    def test_calculation(self, percentage, subtotal, expected):
        rule = PercentageDiscount(percentage)
        assert rule.apply([], subtotal) == expected

    def test_zero_percentage_raises(self):
        with pytest.raises(ValueError):
            PercentageDiscount(0)

    def test_over_100_raises(self):
        with pytest.raises(ValueError):
            PercentageDiscount(101)

    def test_exactly_100_allowed(self):
        rule = PercentageDiscount(100)
        assert rule.apply([], 50) == 50.00

    def test_description_contains_percentage(self):
        rule = PercentageDiscount(20)
        assert "20" in rule.description()


# ------------------------------------------------------------------ #
#  FixedDiscount                                                       #
# ------------------------------------------------------------------ #

class TestFixedDiscount:

    @pytest.mark.parametrize("amount, subtotal, expected", [
        (20.00, 100.00, 20.00),   # 正常减
        (20.00,  15.00, 15.00),   # 折扣 > 小计，只减到 0
        ( 0.01,   0.01,  0.01),   # 刚好等于小计
        (100.00, 200.00, 100.00), # 大折扣，小计足够
    ])
    def test_calculation(self, amount, subtotal, expected):
        rule = FixedDiscount(amount)
        assert rule.apply([], subtotal) == expected

    def test_zero_amount_raises(self):
        with pytest.raises(ValueError):
            FixedDiscount(0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError):
            FixedDiscount(-10)

    def test_description_contains_amount(self):
        rule = FixedDiscount(15)
        assert "15" in rule.description()


# ------------------------------------------------------------------ #
#  ThresholdDiscount（满减）                                           #
# ------------------------------------------------------------------ #

class TestThresholdDiscount:

    @pytest.mark.parametrize("threshold, discount, subtotal, expected", [
        (100, 20, 100.00,  20.00),  # 刚好达到门槛
        (100, 20,  99.99,   0.00),  # 差一分钱没达到
        (100, 20, 150.00,  20.00),  # 超过门槛
        ( 50, 10,  30.00,   0.00),  # 没达到
        (  1,  5,   0.01,   0.00),  # 极小小计未达到
    ])
    def test_threshold_logic(self, threshold, discount, subtotal, expected):
        rule = ThresholdDiscount(threshold, discount)
        assert rule.apply([], subtotal) == expected

    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError):
            ThresholdDiscount(0, 10)

    def test_zero_discount_raises(self):
        with pytest.raises(ValueError):
            ThresholdDiscount(100, 0)

    def test_description(self):
        rule = ThresholdDiscount(100, 20)
        desc = rule.description()
        assert "100" in desc and "20" in desc


# ------------------------------------------------------------------ #
#  BuyXGetYDiscount（买X送Y）                                          #
# ------------------------------------------------------------------ #

class TestBuyXGetYDiscount:

    def _items(self, prices):
        """辅助方法：快速生成商品列表"""
        return [CartItem(Product(f"P{i}", p), 1) for i, p in enumerate(prices)]

    def test_buy2_get1_same_price(self):
        items = self._items([10.00, 10.00, 10.00])
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 30.00) == 10.00

    def test_buy2_get1_cheapest_is_free(self):
        # 价格不同时，最便宜的免费
        items = self._items([30.00, 20.00, 10.00])
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 60.00) == 10.00

    def test_not_enough_items_no_discount(self):
        items = self._items([20.00, 20.00])  # 需要3件，只有2件
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 40.00) == 0.00

    def test_exactly_enough_items(self):
        items = self._items([15.00, 15.00, 15.00])
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 45.00) == 15.00

    def test_multiple_groups(self):
        # 6件 = 2个「买2送1」组，送出2件
        items = self._items([10.00] * 6)
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 60.00) == 20.00

    def test_leftover_items_not_discounted(self):
        # 7件 = 2个完整组(6件) + 1件剩余，只送2件
        items = self._items([10.00] * 7)
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert rule.apply(items, 70.00) == 20.00

    def test_zero_buy_raises(self):
        with pytest.raises(ValueError):
            BuyXGetYDiscount(buy=0, get=1)

    def test_zero_get_raises(self):
        with pytest.raises(ValueError):
            BuyXGetYDiscount(buy=2, get=0)

    def test_description(self):
        rule = BuyXGetYDiscount(buy=2, get=1)
        assert "2" in rule.description() and "1" in rule.description()


# ------------------------------------------------------------------ #
#  CouponDiscount                                                      #
# ------------------------------------------------------------------ #

class TestCouponDiscount:

    def test_percentage_coupon(self, valid_coupon, basic_cart):
        rule = CouponDiscount(valid_coupon)
        subtotal = sum(i.subtotal for i in basic_cart)  # 38.00
        discount = rule.apply(basic_cart, subtotal)
        assert discount == round(subtotal * 0.10, 2)  # 3.80

    def test_fixed_coupon(self):
        coupon = Coupon("FLAT10", "fixed", 10.0)
        rule = CouponDiscount(coupon)
        assert rule.apply([], 50.00) == 10.00

    def test_expired_coupon_returns_zero(self, expired_coupon, basic_cart):
        rule = CouponDiscount(expired_coupon)
        assert rule.apply(basic_cart, 100.00) == 0.0

    def test_min_purchase_not_met_returns_zero(self):
        coupon = Coupon("MIN100", "fixed", 20, min_purchase=100.0)
        rule = CouponDiscount(coupon)
        assert rule.apply([], 50.00) == 0.0

    def test_coupon_cannot_make_price_negative(self):
        # 固定折扣大于小计时，只减到 0
        coupon = Coupon("BIG", "fixed", 999.0)
        rule = CouponDiscount(coupon)
        assert rule.apply([], 10.00) == 10.00

    def test_description_contains_code(self):
        coupon = Coupon("SUMMER", "fixed", 5)
        rule = CouponDiscount(coupon)
        assert "SUMMER" in rule.description()
