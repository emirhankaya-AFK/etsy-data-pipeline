# Etsy Data Pipeline

[English](README.md) | [Türkçe](README_TR.md) | [Deutsch](README_DE.md)

![Demo](docs/demo.svg)

## Portföy demosu

Collector akışı Playwright için hazırdır: ilanları toplar, geçici hataları tekrar dener, kayıtları saklar ve eşleşme/durum analizini panelde gösterir.

Mevcut Etsy koleksiyon fikrini production-style veri mühendisliği projesine dönüştüren sistemdir. Playwright ile zamanlanmış veri toplama, geçici hatalarda tekrar deneme, PostgreSQL upsert, fiyat geçmişi ve küçük analiz paneli içerir.

## Özellikler

- Asenkron Playwright collector
- Üstel beklemeli üç denemelik retry mekanizması
- APScheduler ve aynı anda ikinci çalışmayı engelleyen kilit
- PostgreSQL liste, çalışma geçmişi ve fiyat gözlemleri
- Kaynak URL’ye göre idempotent upsert
- İzin verilen domain kontrolü ve toplama sınırları
- İnternetsiz çalışan örnek veri modu
- REST API, analiz paneli, Docker, testler ve CI

## Sorumlu kullanım

Playwright modunu yalnızca sahibi olduğunuz veya otomasyon izni aldığınız sayfalarda kullanın. Hedef sitenin güncel kullanım şartlarını, robots politikasını, resmî API seçeneklerini, hız sınırlarını, telif ve gizlilik kurallarını inceleyin. Sistem giriş, CAPTCHA, erişim kontrolü veya bot koruması atlatmaz.

## Docker ile çalıştırma

```bash
copy .env.example .env
docker compose up --build
```

- Panel: `http://localhost:8002`
- Swagger: `http://localhost:8002/docs`

Varsayılan `COLLECTOR_MODE=demo` modu internet olmadan çalışır. Paneldeki **Run pipeline now** düğmesi örnek kayıtları PostgreSQL’e ekler.

## Yetkili Playwright modu

Otomasyon iznini doğruladıktan sonra `.env` dosyasını düzenleyin:

```env
COLLECTOR_MODE=playwright
TARGET_URL=https://www.etsy.com/izinli-sayfaniz
ALLOWED_HOSTS=["www.etsy.com","etsy.com"]
SCHEDULE_HOURS=6
```

## Testler

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest -q
```

## Sonraki adımlar

- Alembic migration ve veri saklama politikası
- Çoklu sunucu için PostgreSQL advisory lock
- Prometheus metrikleri ve yapılandırılmış loglar
- Kimlik doğrulama ve tenant ayrımı
- Yönetilen PostgreSQL ve secret manager ile bulut dağıtımı
