import os
from sqlalchemy import create_engine

REGION_MAP = {
    "Lyon": "Auvergne-Rhône-Alpes",
    "Dijon": "Bourgogne-Franche-Comté",
    "Rennes": "Bretagne",
    "Orléans": "Centre-Val de Loire",
    "Ajaccio": "Corse",
    "Strasbourg": "Grand Est",
    "Lille": "Hauts-de-France",
    "Rouen": "Normandie",
    "Bordeaux": "Nouvelle-Aquitaine",
    "Toulouse": "Occitanie",
    "Nantes": "Pays de la Loire",
    "Marseille": "Provence-Alpes-Côte d'Azur",
}

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "energy_weather_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

engine = create_engine(DATABASE_URL)
