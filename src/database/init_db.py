from operator import le
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.config import engine, REGION_MAP


def apply_schema():
    """Exécute le fichier schema.sql pour créer la structure."""
    with open("src/database/schema.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    with engine.begin() as conn:
        conn.execute(text(sql_script))
    print("✅ Schéma SQL appliqué.")


def reset_dimensions():
    """Vides les tables de dimensions pour repartir d'un état propre."""
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE analytics.dim_region, analytics.dim_date CASCADE;")
        )
    print("🧹 Tables de dimensions nettoyées.")


def reset_facts():
    with engine.begin() as conn:
        conn.execute(
            text("DROP TABLE IF EXISTS analytics.fact_weather_energy CASCADE;")
        )
    print("🧹 Tables de faits nettoyées.")


def populate_dim_region():
    """Alimente la table dim_region."""
    regions = [{"region_name": v, "main_city": k} for k, v in REGION_MAP.items()]
    df = pd.DataFrame(regions)
    df.to_sql(
        "dim_region",
        con=engine,
        schema="analytics",
        if_exists="append",
        index=False,
    )
    print("✅ Table dim_region alimentée.")


def populate_dim_date():
    """Génère le calendrier journalier pour l'année 2026."""
    dates = pd.date_range(start="2026-01-01", end="2026-12-31", freq="D")
    df = pd.DataFrame({"full_date": dates.date})

    # Date key au format AAAAMMJJ (ex: 20260917)
    df["date_key"] = pd.to_datetime(df["full_date"]).dt.strftime("%Y%m%d").astype(int)
    df["year"] = pd.to_datetime(df["full_date"]).dt.year
    df["month"] = pd.to_datetime(df["full_date"]).dt.month
    df["day"] = pd.to_datetime(df["full_date"]).dt.day
    df["day_of_week"] = pd.to_datetime(df["full_date"]).dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6])

    df.to_sql(
        "dim_date",
        con=engine,
        schema="analytics",
        if_exists="append",
        index=False,
    )
    print("✅ Table dim_date alimentée (365 jours).")


def init_db():
    """Fonction principale d'initialisation."""
    print("⏳ Initialisation de la base de données...")
    apply_schema()
    reset_dimensions()
    reset_facts()
    populate_dim_region()
    populate_dim_date()
    print("🎉 Initialisation terminée avec succès !")


if __name__ == "__main__":
    init_db()
