"""
公共 fixtures，所有测试文件自动共享
pytest 在运行前会自动加载这个文件
"""
import pytest
from datetime import date

from discount_engine import Product, CartItem, Coupon, DiscountEngine


# ---------- 商品 ----------

@pytest.fixture
def shampoo():
    return Product("Redken Shampoo", 18.00, "haircare")


@pytest.fixture
def conditioner():
    return Product("Redken Conditioner", 20.00, "haircare")


@pytest.fixture
def serum():
    return Product("Hair Serum", 45.00, "treatment")


# ---------- 购物车 ----------

@pytest.fixture
def basic_cart(shampoo, conditioner):
    # 小计 = 18 + 20 = 38.00
    return [CartItem(shampoo, 1), CartItem(conditioner, 1)]


@pytest.fixture
def large_cart(shampoo, conditioner, serum):
    # 小计 = 18*2 + 20 + 45 = 101.00（刚好超过满100）
    return [CartItem(shampoo, 2), CartItem(conditioner, 1), CartItem(serum, 1)]


# ---------- 优惠券 ----------

@pytest.fixture
def valid_coupon():
    return Coupon(
        code="SAVE10",
        discount_type="percentage",
        value=10,
        min_purchase=20.0,
    )


@pytest.fixture
def expired_coupon():
    return Coupon(
        code="OLD20",
        discount_type="fixed",
        value=20.0,
        expiry=date(2020, 1, 1),
    )


# ---------- 引擎 ----------

@pytest.fixture
def engine():
    return DiscountEngine()
