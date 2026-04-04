# LeadScrapper Paraguay

Herramienta web para extraer leads comerciales de Google Maps en Paraguay. Permite buscar negocios por tipo y ciudad, visualizar los resultados en tabla y descargarlos como CSV.

---

## Características

- Búsqueda de negocios por **tipo** (restaurantes, farmacias, hoteles, etc.) y **ciudad/distrito**
- Extracción de: nombre, dirección, teléfono, calificación, reseñas y enlace a Google Maps
- Carga por lotes con botón **"Extraer más"** para obtener resultados adicionales
- Filtro geográfico automático: descarta registros fuera de Paraguay
- Descarga de resultados en **CSV** compatible con Excel (UTF-8 BOM)
- Interfaz web con tema visual moderno construida en Streamlit

---

## Estructura del proyecto

```
Webscrapping/
├── app.py            # Interfaz Streamlit (UI + lógica de orquestación)
├── scraper.py        # Motor de scraping con Playwright (headless Chromium)
├── cleaner.py        # Limpieza y normalización de registros
├── config.py         # Configuración: tipos de negocio, ciudades, parámetros
├── requirements.txt  # Dependencias Python
└── README.md
```

---

## Requisitos

- Python 3.10 o superior
- Conexión a internet (accede a Google Maps en tiempo real)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd Webscrapping
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar el navegador Chromium de Playwright

```bash
playwright install chromium
```

---

## Uso

```bash
streamlit run app.py
```

Se abrirá la app en el navegador en `http://localhost:8501`.

1. Selecciona un **Tipo de Negocio** en el primer desplegable
2. Selecciona una **Ciudad o Distrito** de Paraguay
3. Presiona **Extraer Leads** — el scraper abrirá Chromium en segundo plano
4. Cuando finalice, verás la tabla con los resultados y las métricas resumen
5. Presiona **Extraer más** para cargar el siguiente lote (hasta que se agoten los resultados)
6. Descarga los datos con el botón **Descargar CSV**

---

## Datos extraídos por negocio

| Campo | Descripción |
|---|---|
| Nombre de Negocio | Nombre tal como aparece en Google Maps |
| Calificación (Estrellas) | Puntaje promedio (ej. 4.5) |
| Número de Reseñas | Cantidad de reseñas en Google |
| Dirección Completa | Dirección normalizada |
| Localidad | Localidad inferida de la dirección |
| Ciudad | Ciudad inferida de la dirección |
| Barrio | Barrio / zona (cuando está disponible) |
| Número de Teléfono | Teléfono normalizado |
| URL de Google Maps | Enlace directo al negocio |

---

## Configuración

Los parámetros principales se pueden ajustar en [config.py](config.py):

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `BATCH_SIZE` | `30` | Negocios por lote de extracción |
| `MAX_SCROLL_ATTEMPTS` | `40` | Máximo de scrolls en el feed de Google Maps |
| `SCROLL_PAUSE_MS` | `1200` | Pausa entre scrolls (milisegundos) |
| `ACTION_DELAY_MIN/MAX` | `0.5 / 2.5` | Delay aleatorio entre acciones (segundos) |

---

## Consideraciones técnicas

- El scraper usa **Playwright** con Chromium en modo headless y el plugin `playwright-stealth` para reducir la detección como bot.
- Cada negocio abre una segunda pestaña para extraer el teléfono y la dirección completa desde el panel de detalle.
- Los registros de países extranjeros (Argentina, Brasil, etc.) son filtrados automáticamente.
- En Windows, el event loop usa `ProactorEventLoop` para compatibilidad con Playwright.

---

## Uso responsable

Esta herramienta accede a datos públicos de Google Maps. Úsala de forma ética y responsable:

- No realices scraping masivo o automatizado de forma continua
- Respeta los [Términos de Servicio de Google Maps](https://maps.google.com/help/terms_maps/)
- Los datos extraídos son de uso informativo y no deben ser revendidos sin consentimiento
