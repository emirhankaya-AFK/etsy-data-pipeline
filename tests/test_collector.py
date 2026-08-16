from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.collector import CollectorError, DemoCollector, PlaywrightCollector, parse_price


@pytest.mark.parametrize(
    ("raw", "price", "currency"),
    [
        ("$24.90", Decimal("24.90"), "USD"),
        ("EUR 19,50", Decimal("19.50"), "EUR"),
        ("₺1,249.00", Decimal("1249.00"), "TRY"),
        (None, None, None),
    ],
)
def test_parse_price(raw: str | None, price: Decimal | None, currency: str | None) -> None:
    assert parse_price(raw) == (price, currency)


async def test_demo_collector_is_deterministic() -> None:
    records = await DemoCollector().collect(None)
    assert len(records) == 2
    assert records[0].source_url.startswith("https://")


def test_playwright_collector_rejects_unapproved_host() -> None:
    collector = PlaywrightCollector(Settings())
    with pytest.raises(CollectorError, match="ALLOWED_HOSTS"):
        collector._validate_target("https://untrusted.example/products")
