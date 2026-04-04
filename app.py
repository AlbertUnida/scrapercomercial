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

# ── Custom CSS: purple theme + Poppins Semibold ───────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Poppins', sans-serif !important;
    background-color: #0F0A1E !important;
    color: #FFFFFF !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1E1433 !important;
}

/* Main header */
h1, h2, h3, h4 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
}

/* Primary buttons */
.stButton > button {
    background-color: #7C3AED !important;
    color: #FFFFFF !important;
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.55rem 1.4rem !important;
    transition: background-color 0.2s ease !important;
    width: 100%;
}
.stButton > button:hover:not(:disabled) {
    background-color: #5B21B6 !important;
}
.stButton > button:disabled {
    background-color: #4B5563 !important;
    color: #9CA3AF !important;
    cursor: not-allowed !important;
}

/* Download button */
.stDownloadButton > button {
    background-color: #059669 !important;
    color: #FFFFFF !important;
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.55rem 1.4rem !important;
}
.stDownloadButton > button:hover {
    background-color: #047857 !important;
}

/* Selectboxes */
.stSelectbox label {
    color: #A78BFA !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em !important;
    text-transform: uppercase !important;
}
.stSelectbox > div > div {
    background-color: #1E1433 !important;
    border: 1px solid #7C3AED !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background-color: #7C3AED !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: #1E1433;
    border: 1px solid #7C3AED;
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
[data-testid="stMetricLabel"] {
    color: #A78BFA !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Dataframe container */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #7C3AED;
}

/* Info / error / warning boxes */
.stAlert {
    border-radius: 8px !important;
}

/* Divider */
hr {
    border-color: #7C3AED44 !important;
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background-color: #1E1433 !important;
    border: 1px solid #7C3AED !important;
    border-radius: 8px !important;
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
            [sys.executable, "-m", "playwright", "install", "chromium"],
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
    "<h1 style='text-align:center; color:#A78BFA; margin-bottom:0.2rem;'>"
    "Paraguay Lead Scraper</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#D1D5DB; margin-top:0; margin-bottom:1.5rem;'>"
    "Extrae leads comerciales de Google Maps en Paraguay</p>",
    unsafe_allow_html=True,
)

st.divider()

# ── Search controls ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    selected_business_type = st.selectbox(
        "Tipo de Negocio",
        options=BUSINESS_TYPES,
        index=0,
    )

with col2:
    selected_location = st.selectbox(
        "Ciudad / Distrito",
        options=location_options,
        index=0,
    )

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
        "Extraer Leads",
        disabled=st.session_state.is_scraping,
        use_container_width=True,
        key="extract_btn",
    )

with btn_col2:
    more_btn = st.button(
        "Extraer más",
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
            border: 1px dashed #7C3AED44;
            border-radius: 10px;
            padding: 3rem;
            text-align: center;
            color: #9CA3AF;
        ">
            <p style="font-size:1.1rem; font-weight:600; color:#A78BFA;">
                Selecciona un tipo de negocio y una ciudad, luego presiona
                <span style="color:#7C3AED;">Extraer Leads</span>
            </p>
            <p style="font-size:0.85rem;">
                Los resultados aparecer&#225;n aquí en forma de tabla descargable.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#6B7280; font-size:0.75rem;'>"
    "Paraguay Lead Scraper — Uso responsable y ético de datos públicos."
    "</p>",
    unsafe_allow_html=True,
)
