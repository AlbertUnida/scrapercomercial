# scraper.py

import asyncio
import random
import re
from typing import Callable, Optional
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, ElementHandle

from config import (
    BATCH_SIZE,
    MAX_SCROLL_ATTEMPTS,
    SCROLL_PAUSE_MS,
    ACTION_DELAY_MIN,
    ACTION_DELAY_MAX,
    GOOGLE_MAPS_BASE,
)

# Try to import playwright-stealth; gracefully skip if not installed
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False


def build_search_url(business_type: str, location: str) -> str:
    query = f"{business_type} en {location} Paraguay"
    encoded = quote(query)
    return f"{GOOGLE_MAPS_BASE}{encoded}?hl=es"


async def random_delay():
    delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
    await asyncio.sleep(delay)


async def extract_card_data(card: ElementHandle) -> dict:
    record = {
        "Nombre de Negocio": "N/A",
        "Calificación (Estrellas)": "N/A",
        "Número de Reseñas": "N/A",
        "Dirección Completa": "N/A",
        "Localidad": "N/A",
        "Ciudad": "N/A",
        "Barrio": "N/A",
        "Número de Teléfono": "N/A",
        "URL de la ubicación en Google Maps": "N/A",
    }

    # Business name — try heading classes first, fall back to any h3/h2
    for sel in [
        ".fontHeadlineSmall",
        "[class*='fontHeadlineSmall']",
        "h3",
        "h2",
    ]:
        el = await card.query_selector(sel)
        if el:
            text = (await el.inner_text()).strip()
            if text:
                record["Nombre de Negocio"] = text
                break

    # Rating from aria-label  (e.g. "4.5 stars" / "4,5 estrellas")
    for sel in [
        'span[aria-label*="stars"]',
        'span[aria-label*="estrellas"]',
        'span[aria-label*="estrella"]',
    ]:
        el = await card.query_selector(sel)
        if el:
            label = await el.get_attribute("aria-label") or ""
            m = re.search(r"([\d][.,]?[\d]?)", label)
            if m:
                record["Calificación (Estrellas)"] = m.group(1).replace(",", ".")
                break

    # Review count
    for sel in [
        'span[aria-label*="reviews"]',
        'span[aria-label*="reseñas"]',
        'span[aria-label*="reseña"]',
    ]:
        el = await card.query_selector(sel)
        if el:
            label = await el.get_attribute("aria-label") or ""
            m = re.search(r"([\d.,]+)", label)
            if m:
                record["Número de Reseñas"] = m.group(1).replace(".", "").replace(",", "")
                break

    # Direct Google Maps link from card
    for sel in ["a.hfpxzc", "a[href*='/maps/place/']", "a[data-value]"]:
        el = await card.query_selector(sel)
        if el:
            href = await el.get_attribute("href") or ""
            if href:
                record["URL de la ubicación en Google Maps"] = href
                break

    return record


async def extract_detail_panel(page: Page, record: dict) -> dict:
    try:
        await page.wait_for_selector("h1", timeout=10000)
    except Exception:
        return record

    await random_delay()

    # Phone — 3-tier cascade
    phone = "N/A"

    # Tier 1: data-item-id attribute
    el = await page.query_selector('[data-item-id^="phone:tel:"]')
    if el:
        raw = await el.get_attribute("data-item-id") or ""
        phone = raw.replace("phone:tel:", "").strip()

    # Tier 2: aria-label containing phone label
    if not phone or phone == "N/A":
        for sel in [
            '[aria-label*="Teléfono:"]',
            '[aria-label*="Phone:"]',
            '[aria-label*="Teléfono "]',
        ]:
            el = await page.query_selector(sel)
            if el:
                raw = await el.get_attribute("aria-label") or ""
                phone = raw.split(":", 1)[-1].strip() if ":" in raw else raw.strip()
                if phone:
                    break

    # Tier 3: regex scan of all visible spans
    if not phone or phone == "N/A":
        spans = await page.query_selector_all("span")
        for span in spans[:80]:  # cap to avoid huge DOMs
            try:
                text = (await span.inner_text()).strip()
                if re.match(r"^\+?[\d][\d\s\-\(\)]{5,15}$", text):
                    phone = text
                    break
            except Exception:
                continue

    record["Número de Teléfono"] = phone if phone else "N/A"

    # Address — try aria-label then data-item-id
    for sel in [
        '[aria-label^="Dirección:"]',
        '[aria-label^="Address:"]',
        '[data-item-id="address"]',
        'button[data-item-id="address"]',
    ]:
        el = await page.query_selector(sel)
        if el:
            raw = (await el.get_attribute("aria-label") or await el.inner_text() or "").strip()
            if ":" in raw:
                raw = raw.split(":", 1)[-1].strip()
            if raw:
                record["Dirección Completa"] = raw
                break

    # Use final page URL as canonical Maps link
    current_url = page.url
    if "/maps/place/" in current_url:
        record["URL de la ubicación en Google Maps"] = current_url

    return record


async def scrape_google_maps(
    business_type: str,
    location: str,
    batch_offset: int = 0,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> list[dict]:
    results = []
    url = build_search_url(business_type, location)

    def emit(msg: str, pct: float = 0.0):
        if progress_callback:
            try:
                progress_callback(msg, pct)
            except Exception:
                pass

    emit("Iniciando navegador...", 0.02)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--lang=es-PY",
            ],
        )

        context = await browser.new_context(
            locale="es-PY",
            timezone_id="America/Asuncion",
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )

        # Block heavy resources to speed up scraping
        await context.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,mp4,webm,ico}",
            lambda route, _: route.abort(),
        )

        page = await context.new_page()

        if STEALTH_AVAILABLE:
            await stealth_async(page)

        emit("Navegando a Google Maps...", 0.05)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            emit(f"Error al cargar Google Maps: {e}", 1.0)
            await browser.close()
            return []

        await random_delay()

        # Dismiss cookie consent / accept dialog
        for sel in [
            'button[aria-label*="Accept"]',
            'button[aria-label*="Aceptar"]',
            'button[aria-label*="Agree"]',
            "#L2AGLb",
            'form:has(button) button:first-of-type',
        ]:
            try:
                btn = await page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await random_delay()
                    break
            except Exception:
                continue

        # Wait for feed
        emit("Esperando resultados...", 0.10)
        try:
            await page.wait_for_selector('div[role="feed"]', timeout=20000)
        except Exception:
            emit("No se encontraron resultados.", 1.0)
            await browser.close()
            return []

        # ── Scroll to load enough cards ──────────────────────────────────────
        target_count = batch_offset + BATCH_SIZE
        feed = await page.query_selector('div[role="feed"]')
        prev_count = 0
        stale = 0

        for _ in range(MAX_SCROLL_ATTEMPTS):
            content = await page.content()
            if (
                "Has llegado al final de la lista" in content
                or "You've reached the end of the list" in content
                or "No hay más resultados" in content
            ):
                break

            cards = await page.query_selector_all('div[role="article"]')
            current_count = len(cards)

            pct = min(0.10 + (current_count / max(target_count, 1)) * 0.45, 0.55)
            emit(f"Cargando... {current_count} negocios encontrados", pct)

            if current_count >= target_count:
                break

            # Scroll the feed panel
            if feed:
                try:
                    await feed.focus()
                    await feed.press("End")
                except Exception:
                    pass

            await page.wait_for_timeout(SCROLL_PAUSE_MS + random.randint(0, 400))

            # JS fallback when stale
            if current_count == prev_count:
                stale += 1
                if stale >= 3:
                    try:
                        await page.evaluate(
                            "(feed) => { feed.scrollTop = feed.scrollHeight; }",
                            feed,
                        )
                    except Exception:
                        pass
                    await page.wait_for_timeout(1500)
                if stale >= 6:
                    break  # truly exhausted
            else:
                stale = 0

            prev_count = current_count

        # ── Extract data from each card ──────────────────────────────────────
        all_cards = await page.query_selector_all('div[role="article"]')
        cards_to_process = all_cards[batch_offset: batch_offset + BATCH_SIZE]
        total = len(cards_to_process)

        if total == 0:
            emit("No hay más resultados disponibles.", 1.0)
            await browser.close()
            return []

        emit(f"Extrayendo datos de {total} negocios...", 0.58)

        for idx, card in enumerate(cards_to_process):
            pct = 0.58 + (idx / max(total, 1)) * 0.40
            emit(f"Procesando negocio {idx + 1} de {total}...", pct)

            record = await extract_card_data(card)

            # Open detail URL in a new tab to get phone + full address
            detail_url = record.get("URL de la ubicación en Google Maps", "N/A")
            if detail_url != "N/A" and "/maps/place/" in detail_url:
                detail_page = None
                try:
                    detail_page = await context.new_page()
                    if STEALTH_AVAILABLE:
                        await stealth_async(detail_page)
                    await detail_page.goto(
                        detail_url, wait_until="domcontentloaded", timeout=20000
                    )
                    record = await extract_detail_panel(detail_page, record)
                except Exception:
                    pass
                finally:
                    if detail_page:
                        try:
                            await detail_page.close()
                        except Exception:
                            pass

                await random_delay()

            if record["Nombre de Negocio"] != "N/A":
                results.append(record)

        emit("Extracción completada.", 1.0)
        await browser.close()

    return results
