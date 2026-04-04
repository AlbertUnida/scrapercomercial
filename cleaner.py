# cleaner.py

import re
import pandas as pd

from config import OUTPUT_COLUMNS


def sanitize_text(value) -> str:
    if not isinstance(value, str) or not value.strip():
        return "N/A"
    cleaned = re.sub(r"[\x00-\x1F\x7F]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else "N/A"


def normalize_phone(phone: str) -> str:
    if not phone or phone == "N/A":
        return "N/A"
    cleaned = re.sub(r"[^\d\+\s\-\(\)]", "", phone).strip()
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 6:
        return "N/A"
    return cleaned


def extract_locality(address: str, location: str) -> dict:
    result = {"Localidad": location, "Ciudad": location, "Barrio": "N/A"}

    if address == "N/A" or not address:
        return result

    parts = [p.strip() for p in address.split(",") if p.strip()]

    # Strip trailing "Paraguay" or "República del Paraguay"
    if parts and parts[-1].lower() in ("paraguay", "república del paraguay", "republic of paraguay"):
        parts = parts[:-1]

    if not parts:
        return result

    # Heuristic: "Street/Barrio, Localidad, Ciudad, Depto"
    # Last part → Ciudad, second-to-last → Localidad, first → Barrio
    result["Ciudad"] = parts[-1]
    if len(parts) >= 2:
        result["Localidad"] = parts[-2]
    if len(parts) >= 3:
        result["Barrio"] = parts[0]

    return result


FOREIGN_COUNTRIES = [
    "argentina", "brasil", "brazil", "bolivia",
    "chile", "perú", "peru", "uruguay", "colombia",
]


def clean_records(raw_records: list[dict], location: str) -> pd.DataFrame:
    cleaned = []

    for rec in raw_records:
        row = {}

        row["Nombre de Negocio"] = sanitize_text(rec.get("Nombre de Negocio", "N/A"))
        if row["Nombre de Negocio"] == "N/A":
            continue  # skip fully empty records

        row["Calificación (Estrellas)"] = sanitize_text(rec.get("Calificación (Estrellas)", "N/A"))
        row["Número de Reseñas"] = sanitize_text(rec.get("Número de Reseñas", "N/A"))

        address = sanitize_text(rec.get("Dirección Completa", "N/A"))

        # Geographic filter: skip if address mentions a non-Paraguay country
        if address != "N/A":
            addr_lower = address.lower()
            if any(c in addr_lower for c in FOREIGN_COUNTRIES):
                if "paraguay" not in addr_lower:
                    continue

        row["Dirección Completa"] = address

        locality = extract_locality(address, location)
        row["Localidad"] = locality["Localidad"]
        row["Ciudad"] = locality["Ciudad"]
        row["Barrio"] = locality["Barrio"]

        row["Número de Teléfono"] = normalize_phone(rec.get("Número de Teléfono", "N/A"))
        row["URL de la ubicación en Google Maps"] = sanitize_text(
            rec.get("URL de la ubicación en Google Maps", "N/A")
        )

        cleaned.append(row)

    return pd.DataFrame(cleaned, columns=OUTPUT_COLUMNS)
