# src/transformation/build_datamart.py
import pandas as pd
from sqlalchemy import text

from src.config import REGION_MAP, engine
from src.ingestion.fetch_energy import fetch_energy_all
from src.ingestion.fetch_weather import fetch_weather_all


def process_energy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Adjust the timezone and aggregate the energy consumption by hour."""
    df["date"] = df["date"].dt.tz_convert("Europe/Paris")
    df["date"] = df["date"].dt.tz_localize(None)

    df["date_hourly"] = df["date"].dt.floor("h")
    df = (
        df.groupby(["date_hourly", "region", "code_insee_region"])
        .mean(numeric_only=True)
        .reset_index()
    )
    df = df.rename(columns={"date_hourly": "date"})
    return df


def run_pipeline():
    print("⏳ Récupération des données météo...")
    df_weather = fetch_weather_all()
    df_weather["region"] = df_weather["city"].map(REGION_MAP)

    print("⏳ Récupération des données énergie...")
    df_energy = fetch_energy_all()
    df_energy = process_energy_data(df_energy)

    print("⏳ Fusion des données météo et énergie...")
    df_weather["date"] = pd.to_datetime(df_weather["date"]).dt.tz_localize(None)
    df_merged = pd.merge(df_weather, df_energy, on=["date", "region"], how="inner")

    if df_merged.empty:
        print("⚠️ Aucune donnée fusionnée à insérer.")
        return

    print(f"✅ Fusion réussie : {len(df_merged)} lignes prêtes à être transformées.")

    print("⏳ Transformation pour le schéma du Datamart...")

    # 1. Extraction de la clé de date journalière (AAAAMMJJ) et de l'heure
    df_merged["date_key"] = df_merged["date"].dt.strftime("%Y%m%d").astype(int)
    df_merged["hour"] = df_merged["date"].dt.hour

    # 2. Récupération de dim_region pour mapper avec region_id
    dim_region = pd.read_sql(
        "SELECT region_id, region_name FROM analytics.dim_region", con=engine
    )
    df_merged = df_merged.merge(
        dim_region, left_on="region", right_on="region_name", how="inner"
    )

    # 3. Alignement des noms de colonnes avec schema.sql
    # Adapte ces noms selon le nom exact de tes colonnes issues de la fusion
    column_mapping = {
        "temperature_celsius": "temp_mean_celsius",  # Exemple selon tes données
        "precipitation": "precipitation_mm",
        "wind_speed": "wind_speed_max_kmh",
        "consommation": "consumption_mw",
    }
    df_merged = df_merged.rename(columns=column_mapping)

    # 4. Sélection stricte des colonnes de fact_weather_energy
    fact_columns = [
        "date_key",
        "region_id",
        "hour",
        "temp_mean_celsius",
        "precipitation_mm",
        "wind_speed_max_kmh",
        "consumption_mw",
    ]

    # Conserve uniquement les colonnes présentes dans la table de faits
    final_cols = [col for col in fact_columns if col in df_merged.columns]
    df_fact = df_merged[final_cols]

    print("⏳ Insertion dans analytics.fact_weather_energy...")
    df_fact.to_sql(
        name="fact_weather_energy",
        con=engine,
        schema="analytics",
        if_exists="append",
        index=False,
    )
    print("🎉 Pipeline terminé ! Données enregistrées dans la table de faits.")


if __name__ == "__main__":
    run_pipeline()
