import pandas as pd
import requests

from src.config import REGION_MAP

URL_DATASET = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/records"

REGIONS = REGION_MAP.values()


def fetch_energy_region(region: str) -> pd.DataFrame:
    params = {
        "limit": 100,
        "refine": f'libelle_region:"{region}"',
        "where": "consommation is NOT null",
        "order_by": "date_heure DESC",
    }
    response = requests.get(URL_DATASET, params=params)
    res_json = response.json()

    if "error_code" in res_json:
        raise ValueError(
            f"Error fetching data for region {region}: {res_json['error_code']}, message: {res_json['message']}"
        )

    data = res_json.get("results", [])
    df = pd.DataFrame(data)

    # 1. Sécurité : Si aucune donnée n'est renvoyée pour cette région
    if df.empty:
        print(f"No data found for region : {region}")
        return pd.DataFrame(
            columns=["date", "region", "code_insee_region", "consumption_mw"]
        )

    # 2. Suppression de la colonne date simple si elle existe
    if "date" in df.columns:
        df = df.drop(columns=["date"])

    # 3. Renommage et typage
    df = df.rename(
        columns={
            "date_heure": "date",
            "libelle_region": "region",
            "consommation": "consumption_mw",
            "production": "production_mw",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_energy_all() -> pd.DataFrame:
    all_dfs = [fetch_energy_region(region) for region in REGIONS]
    valid_dfs = [d for d in all_dfs if not d.empty]

    if not valid_dfs:
        print("No result from the API for any region. Returning empty DataFrame.")
        return pd.DataFrame()

    return pd.concat(valid_dfs, ignore_index=True)


if __name__ == "__main__":
    energy_df = fetch_energy_all()
    print("\nAperçu du jeu de données Energy :")
    print(energy_df.head())
    print(f"\nTotal enregistrements : {len(energy_df)}")
