"""Regression tests for the supported consumer billing tiers."""

from lib.settings import settings
from routes.stripe_webhook import map_price_to_plan


def test_known_plan_prices(monkeypatch):
    monkeypatch.setattr(settings, "NEXT_PUBLIC_STRIPE_PRICE_PRO", "price_pro_test")
    monkeypatch.setattr(settings, "NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS", "price_career_test")
    assert map_price_to_plan("price_pro_test") == "pro"
    assert map_price_to_plan("price_career_test") == "career_plus"


def test_retired_investor_plan_does_not_grant_access():
    assert map_price_to_plan("price_investor_xxx") == "free"


def test_unknown_prices_are_never_premium():
    assert map_price_to_plan("price_unknown_xxx") == "free"
