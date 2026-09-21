import os

from sqlalchemy import create_engine

REGION_MAP = {
    "Nantes": "Pays de la Loire",
    "Bordeaux": "Nouvelle-Aquitaine",
}

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
