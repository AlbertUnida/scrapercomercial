# config.py

APP_TITLE = "Paraguay Lead Scraper"
BATCH_SIZE = 30
MAX_SCROLL_ATTEMPTS = 40
SCROLL_PAUSE_MS = 1200
ACTION_DELAY_MIN = 0.5
ACTION_DELAY_MAX = 2.5
GOOGLE_MAPS_BASE = "https://www.google.com/maps/search/"

BUSINESS_TYPES = [
    "Bar",
    "Bodega",
    "Restaurant",
    "Pizzeria",
    "Cafetería",
    "Confitería",
    "Discoteca",
    "Pub",
    "Casa de Fiesta",
    "Salón de Fiesta",
    "Tienda",
    "Salón de Belleza",
    "Spa",
    "Hotel",
    "Motel",
    "Supermercado",
    "Mini Mercado",
    "Gimnasio",
    "Academia de Danza",
    "Shopping",
    "Galería",
    "Casino",
    "Salón de Juegos",
    "Estación de Servicios",
    "Balneario",
    "Farmacia",
    "Club",
    "Cooperativa",
    "Centro Médico",
    "Hospital",
    "Sanatorio",
    "Clínica",
]

PARAGUAY_LOCATIONS = {
    "Asunción (Capital)": ["Asunción"],
    "Central": [
        "Areguá",
        "Capiatá",
        "Fernando de la Mora",
        "Guarambaré",
        "Itá",
        "Itauguá",
        "Juan Augusto Saldívar",
        "Lambaré",
        "Limpio",
        "Luque",
        "Mariano Roque Alonso",
        "Nueva Italia",
        "Ñemby",
        "San Antonio",
        "San Lorenzo",
        "Villa Elisa",
        "Villeta",
        "Ypacaraí",
        "Ypané",
    ],
    "Alto Paraná": [
        "Ciudad del Este",
        "Hernandarias",
        "Minga Guazú",
        "Minga Porá",
        "Presidente Franco",
        "Santa Rita",
        "Itakyry",
    ],
    "Itapúa": [
        "Encarnación",
        "Coronel Bogado",
        "Hohenau",
        "Obligado",
        "Cambyretá",
        "Capitán Miranda",
        "Carmen del Paraná",
    ],
    "Caaguazú": [
        "Coronel Oviedo",
        "Caaguazú",
        "Repatriación",
        "San Joaquín",
        "Doctor Juan Manuel Frutos",
    ],
    "Concepción": [
        "Concepción",
        "Horqueta",
        "Belén",
        "Loreto",
    ],
    "Amambay": [
        "Pedro Juan Caballero",
        "Bella Vista Norte",
        "Capitán Bado",
    ],
    "Cordillera": [
        "Caacupé",
        "Tobatí",
        "Emboscada",
        "San Bernardino",
    ],
    "Guairá": [
        "Villarrica",
        "Coronel Martínez",
        "Mbocayaty",
    ],
    "Misiones": [
        "San Juan Bautista",
        "San Ignacio",
        "Santa Rosa de Lima",
        "Ayolas",
    ],
    "Paraguarí": [
        "Paraguarí",
        "Carapeguá",
        "Ybycuí",
    ],
    "San Pedro": [
        "San Estanislao",
        "Santa Rosa del Aguaray",
        "Guayaibí",
    ],
    "Boquerón": [
        "Filadelfia",
        "Loma Plata",
        "Mariscal Estigarribia",
    ],
    "Presidente Hayes": [
        "Villa Hayes",
        "Benjamín Aceval",
    ],
    "Alto Paraguay": [
        "Fuerte Olimpo",
        "Puerto Casado",
    ],
    "Caazapá": [
        "Caazapá",
        "San Juan Nepomuceno",
        "Yuty",
    ],
    "Canindeyú": [
        "Salto del Guairá",
        "Curuguaty",
    ],
    "Ñeembucú": [
        "Pilar",
        "Alberdi",
    ],
}

OUTPUT_COLUMNS = [
    "Nombre de Negocio",
    "Calificación (Estrellas)",
    "Número de Reseñas",
    "Dirección Completa",
    "Localidad",
    "Ciudad",
    "Barrio",
    "Número de Teléfono",
    "URL de la ubicación en Google Maps",
]

# UI theme
PRIMARY_COLOR = "#7C3AED"
SECONDARY_COLOR = "#5B21B6"
ACCENT_COLOR = "#A78BFA"
BACKGROUND_DARK = "#0F0A1E"
CARD_BACKGROUND = "#1E1433"
