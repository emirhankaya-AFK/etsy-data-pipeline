import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings


@dataclass(frozen=True, slots=True)
class ListingRecord:
    source_url: str
    title: str
    image_url: str | None = None
    price: Decimal | None = None
    currency: str | None = None


class CollectorError(RuntimeError):
    pass


def parse_price(value: str | None) -> tuple[Decimal | None, str | None]:
    if not value:
        return None, None
    currency_match = re.search(r"(USD|EUR|GBP|TRY|\$|€|£|₺)", value, flags=re.IGNORECASE)
    currency_map = {"$": "USD", "€": "EUR", "£": "GBP", "₺": "TRY"}
    raw_currency = currency_match.group(1).upper() if currency_match else None
    currency = currency_map.get(raw_currency, raw_currency)
    number_match = re.search(r"\d[\d.,]*", value)
    if not number_match:
        return None, currency
    raw = number_match.group(0)
    if raw.count(",") == 1 and raw.count(".") == 0:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return Decimal(raw).quantize(Decimal("0.01")), currency
    except InvalidOperation:
        return None, currency


class Collector(ABC):
    @abstractmethod
    async def collect(self, target_url: str | None) -> list[ListingRecord]:
        raise NotImplementedError


class DemoCollector(Collector):
    async def collect(self, target_url: str | None) -> list[ListingRecord]:
        return [
            ListingRecord(
                source_url="https://example.test/listing/handmade-notebook",
                title="Handmade Linen Notebook",
                image_url="https://picsum.photos/seed/notebook/600/400",
                price=Decimal("24.90"),
                currency="USD",
            ),
            ListingRecord(
                source_url="https://example.test/listing/ceramic-mug",
                title="Minimal Ceramic Mug",
                image_url="https://picsum.photos/seed/mug/600/400",
                price=Decimal("31.50"),
                currency="USD",
            ),
        ]


class PlaywrightCollector(Collector):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _validate_target(self, target_url: str | None) -> str:
        if not target_url:
            raise CollectorError("TARGET_URL is required in Playwright mode")
        parsed = urlparse(target_url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in self.settings.allowed_hosts
        ):
            raise CollectorError("Target URL is not in ALLOWED_HOSTS")
        return target_url

    @retry(
        retry=retry_if_exception_type(CollectorError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def collect(self, target_url: str | None) -> list[ListingRecord]:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright

        url = self._validate_target(target_url)
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self.settings.headless)
                page = await browser.new_page()
                page.set_default_timeout(self.settings.request_timeout_ms)
                await page.goto(url, wait_until="domcontentloaded")
                links = page.locator('a[href*="/listing/"]')
                await links.first.wait_for(state="attached")
                raw_items = await links.evaluate_all(
                    r"""
                    elements => elements.map(element => {
                      const card = element.closest('[data-listing-id], li') || element;
                      const image = card.querySelector('img');
                      const title = element.getAttribute('title') ||
                        card.querySelector('h3')?.textContent || image?.alt || element.textContent;
                      const text = card.textContent || '';
                      const pricePattern = /(?:USD|EUR|GBP|TRY|[$€£₺])\s*[0-9][0-9.,]*/i;
                      const price = text.match(pricePattern)?.[0] || null;
                      return {
                        url: element.href.split('?')[0],
                        title: title?.trim(),
                        image: image?.src,
                        price
                      };
                    })
                    """
                )
                await browser.close()
        except PlaywrightTimeoutError as exc:
            raise CollectorError("Timed out while waiting for listing cards") from exc
        except CollectorError:
            raise
        except Exception as exc:
            raise CollectorError(f"Browser collection failed: {exc}") from exc

        unique: dict[str, ListingRecord] = {}
        for item in raw_items:
            if not item.get("url") or not item.get("title"):
                continue
            price, currency = parse_price(item.get("price"))
            unique[item["url"]] = ListingRecord(
                source_url=item["url"],
                title=" ".join(item["title"].split()),
                image_url=item.get("image"),
                price=price,
                currency=currency,
            )
            if len(unique) >= self.settings.max_listings_per_run:
                break
        if not unique:
            raise CollectorError("No listing records were extracted")
        return list(unique.values())


def build_collector(settings: Settings) -> Collector:
    if settings.collector_mode == "playwright":
        return PlaywrightCollector(settings)
    return DemoCollector()
