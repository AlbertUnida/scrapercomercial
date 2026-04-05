# app.py

import asyncio
import io
import subprocess
import sys
import threading

import pandas as pd
import streamlit as st

from config import (
    APP_TITLE,
    BATCH_SIZE,
    BUSINESS_TYPES,
    PARAGUAY_LOCATIONS,
    OUTPUT_COLUMNS,
)
from cleaner import clean_records
from scraper import scrape_google_maps

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS: light SaaS theme + Inter ─────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #F4F4F8 !important;
    color: #1A1A2E !important;
}

/* Hide default Streamlit top padding */
.block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 1100px !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
}

/* Headers */
h1, h2, h3, h4 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #1A1A2E !important;
}

/* Purple hero header banner */
.hero-banner {
    background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem 2.2rem 2.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35);
}
.hero-icon {
    background: rgba(255,255,255,0.18);
    border-radius: 14px;
    padding: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    min-width: 58px;
    min-height: 58px;
}
.hero-title {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.hero-subtitle {
    font-size: 0.92rem !important;
    color: rgba(255,255,255,0.80) !important;
    margin: 0.15rem 0 0 0 !important;
}

/* Search card */
.search-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.6rem 2rem;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    margin-bottom: 1.5rem;
}

/* Primary buttons */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%) !important;
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.65rem 1.6rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.30) !important;
    width: 100%;
}
.stButton > button:hover:not(:disabled) {
    background: linear-gradient(135deg, #6D28D9 0%, #5B21B6 100%) !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.40) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:disabled {
    background: #E5E7EB !important;
    color: #9CA3AF !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.65rem 1.6rem !important;
    box-shadow: 0 2px 8px rgba(5,150,105,0.30) !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #047857 0%, #065F46 100%) !important;
    box-shadow: 0 4px 14px rgba(5,150,105,0.40) !important;
}

/* Selectboxes */
.stSelectbox label {
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 0.80rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    color: #1A1A2E !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* Text input */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    color: #1A1A2E !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #A78BFA) !important;
    border-radius: 99px !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1.5px solid #F3F4F6;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
[data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stMetricValue"] {
    color: #1A1A2E !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* Dataframe container */
.stDataFrame {
    border-radius: 14px;
    overflow: hidden;
    border: 1.5px solid #F3F4F6;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    background: #FFFFFF;
}

/* Info / error / warning boxes */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* Divider */
hr {
    border-color: #E5E7EB !important;
    margin: 1.5rem 0 !important;
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* Section label above controls */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Ensure Playwright browsers are installed (once per session) ───────────────
@st.cache_resource(show_spinner=False)
def ensure_playwright_browsers():
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
            check=False,
            capture_output=True,
            timeout=120,
        )
    except Exception:
        pass


ensure_playwright_browsers()


# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS: dict = {
    "leads_df": None,
    "raw_records": [],
    "batch_offset": 0,
    "is_scraping": False,
    "search_exhausted": False,
    "last_business_type": None,
    "last_location": None,
    "error_message": None,
    "status_log": [],
}

for _key, _val in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


# ── Thread runner: isolated ProactorEventLoop for Playwright on Windows ───────
def run_scraper_in_thread(coro) -> list:
    result_box: list = []
    error_box: list = []

    def worker():
        if hasattr(asyncio, "ProactorEventLoop"):
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_box.append(loop.run_until_complete(coro))
        except Exception as exc:
            error_box.append(exc)
        finally:
            loop.close()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=300)

    if not thread.is_alive() and error_box:
        raise error_box[0]
    return result_box[0] if result_box else []


# ── Build flat location list for selectbox ────────────────────────────────────
location_options: list[str] = []
for _dept, _cities in PARAGUAY_LOCATIONS.items():
    location_options.extend(_cities)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-icon">🔍</div>
        <div>
            <p class="hero-title">Buscador de Locales por Rubro con Google Maps</p>
            <p class="hero-subtitle">Extracción locales por rubro dentro de Paraguay</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Search card ───────────────────────────────────────────────────────────────
st.markdown('<div class="search-card">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        '<p class="section-label">&#9906; &nbsp;Tipo de Negocio</p>',
        unsafe_allow_html=True,
    )
    selected_business_type = st.selectbox(
        "Tipo de Negocio",
        options=BUSINESS_TYPES,
        index=0,
        label_visibility="collapsed",
    )

with col2:
    st.markdown(
        '<p class="section-label">&#128205; &nbsp;Ubicación (Paraguay)</p>',
        unsafe_allow_html=True,
    )
    selected_location = st.selectbox(
        "Ciudad / Distrito",
        options=location_options,
        index=0,
        label_visibility="collapsed",
    )

st.markdown("</div>", unsafe_allow_html=True)

# Detect parameter change → reset state
if (
    st.session_state.last_business_type != selected_business_type
    or st.session_state.last_location != selected_location
):
    for _key, _val in DEFAULTS.items():
        st.session_state[_key] = _val
    st.session_state.last_business_type = selected_business_type
    st.session_state.last_location = selected_location

# ── Action buttons ────────────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

with btn_col1:
    extract_btn = st.button(
        "🔍 &nbsp;Buscar Locales",
        disabled=st.session_state.is_scraping,
        use_container_width=True,
        key="extract_btn",
    )

with btn_col2:
    more_btn = st.button(
        "➕ &nbsp;Extraer más",
        disabled=(
            st.session_state.is_scraping
            or st.session_state.leads_df is None
            or st.session_state.search_exhausted
        ),
        use_container_width=True,
        key="more_btn",
    )

st.divider()


# ── Shared progress callback (writes to session_state list) ──────────────────
def _progress_cb(msg: str, pct: float):
    st.session_state.status_log.append((msg, pct))


# ── Scraping: first batch ─────────────────────────────────────────────────────
if extract_btn:
    st.session_state.is_scraping = True
    st.session_state.raw_records = []
    st.session_state.batch_offset = 0
    st.session_state.search_exhausted = False
    st.session_state.error_message = None
    st.session_state.leads_df = None
    st.session_state.status_log = []

    with st.status(
        f"Buscando **{selected_business_type}** en **{selected_location}**...",
        expanded=True,
    ) as status_widget:
        try:
            raw = run_scraper_in_thread(
                scrape_google_maps(
                    selected_business_type,
                    selected_location,
                    batch_offset=0,
                )
            )

            if not raw:
                st.session_state.error_message = (
                    f"No se encontraron resultados para "
                    f"**{selected_business_type}** en **{selected_location}**. "
                    "Intenta con otro tipo de negocio o ubicación."
                )
                status_widget.update(label="Sin resultados", state="error")
            else:
                st.session_state.raw_records = list(raw)
                st.session_state.leads_df = clean_records(raw, selected_location)
                st.session_state.batch_offset = BATCH_SIZE
                status_widget.update(
                    label=f"{len(raw)} negocios extraídos exitosamente",
                    state="complete",
                )

        except Exception as exc:
            st.session_state.error_message = f"Error durante la extracción: {exc}"
            status_widget.update(label="Error", state="error")
        finally:
            st.session_state.is_scraping = False


# ── Scraping: more results ────────────────────────────────────────────────────
if more_btn and st.session_state.leads_df is not None:
    st.session_state.is_scraping = True
    st.session_state.status_log = []

    with st.status("Cargando más resultados...", expanded=True) as status_widget:
        try:
            raw = run_scraper_in_thread(
                scrape_google_maps(
                    selected_business_type,
                    selected_location,
                    batch_offset=st.session_state.batch_offset,
                )
            )

            if not raw:
                st.session_state.search_exhausted = True
                status_widget.update(
                    label="No hay más resultados disponibles en Google Maps.",
                    state="complete",
                )
            else:
                st.session_state.raw_records.extend(raw)
                st.session_state.leads_df = clean_records(
                    st.session_state.raw_records, selected_location
                )
                st.session_state.batch_offset += BATCH_SIZE
                status_widget.update(
                    label=(
                        f"{len(st.session_state.raw_records)} negocios en total "
                        f"({len(raw)} nuevos)"
                    ),
                    state="complete",
                )

        except Exception as exc:
            st.session_state.error_message = f"Error: {exc}"
            status_widget.update(label="Error", state="error")
        finally:
            st.session_state.is_scraping = False


# ── Notifications ─────────────────────────────────────────────────────────────
if st.session_state.error_message:
    st.error(st.session_state.error_message)

if st.session_state.search_exhausted and st.session_state.leads_df is not None:
    st.info(
        "Se han cargado todos los resultados disponibles en Google Maps para esta búsqueda."
    )


# ── Results section ───────────────────────────────────────────────────────────
if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
    df: pd.DataFrame = st.session_state.leads_df

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Negocios", len(df))
    m2.metric("Con Teléfono", int((df["Número de Teléfono"] != "N/A").sum()))
    m3.metric("Con Calificación", int((df["Calificación (Estrellas)"] != "N/A").sum()))
    m4.metric("Con Dirección", int((df["Dirección Completa"] != "N/A").sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    # Results table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "URL de la ubicación en Google Maps": st.column_config.LinkColumn(
                "URL Maps",
                display_text="Ver en Maps",
            ),
            "Calificación (Estrellas)": st.column_config.TextColumn(
                "Estrellas",
            ),
            "Número de Reseñas": st.column_config.TextColumn(
                "Reseñas",
            ),
        },
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # CSV download — utf-8-sig for Excel Spanish char compatibility
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    csv_bytes = csv_buffer.getvalue().encode("utf-8-sig")

    file_name = (
        f"leads_{selected_business_type.replace(' ', '_')}_"
        f"{selected_location.replace(' ', '_')}.csv"
    )

    dl_col, _, _ = st.columns([1, 2, 1])
    with dl_col:
        st.download_button(
            label="Descargar CSV",
            data=csv_bytes,
            file_name=file_name,
            mime="text/csv",
            use_container_width=True,
        )

elif st.session_state.leads_df is not None and st.session_state.leads_df.empty:
    st.warning(
        "La extracción completó pero todos los registros fueron filtrados "
        "(posiblemente negocios fuera de Paraguay o sin nombre)."
    )

else:
    # Placeholder when nothing scraped yet
    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 2px dashed #E5E7EB;
            border-radius: 16px;
            padding: 3.5rem 2rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        ">
            <div style="font-size:2.5rem; margin-bottom:0.8rem;">📋</div>
            <p style="font-size:1.05rem; font-weight:600; color:#1A1A2E; margin-bottom:0.5rem;">
                Ningún local extraído aún
            </p>
            <p style="font-size:0.88rem; color:#9CA3AF; margin:0;">
                Selecciona un tipo de negocio y una ciudad, luego presiona
                <span style="color:#7C3AED; font-weight:600;">Buscar Locales</span>
                para comenzar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#9CA3AF; font-size:0.75rem; margin-top:1rem;'>"
    "Buscador de Locales por Rubro con Google Maps &nbsp;·&nbsp; Uso responsable y ético de datos públicos - Creado por Alberto Aguilera"
    "</p>",
    unsafe_allow_html=True,
)
