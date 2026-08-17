# Etsy Data Pipeline

[English](README.md) | [Türkçe](README_TR.md) | [Deutsch](README_DE.md)

Playwright-Automatisierungspipeline mit Retries, Zeitplanung, PostgreSQL-Persistenz und Analyse-Dashboard.

![Demo](docs/demo.svg)

## Funktionen
- Browser-basierte Datensammlung
- Wiederholungslogik für temporäre Fehler
- Strukturierte Speicherung und Skill-Matching
- Dashboard für Status und Kennzahlen
- Docker, Tests und CI

## Start

    cp .env.example .env
    docker compose up --build

Die Pipeline ist als erweiterbare Basis für echte Collector-Worker aufgebaut. Zugangsdaten und Datenschutzregeln müssen vor dem produktiven Crawling konfiguriert werden.

