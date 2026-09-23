import requests
import pandas as pd

URL_DATASET = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/records"

REGIONS = ["Pays de la Loire", "Nouvelle-Aquitaine"]


def fetch_energy_region(region: str) -> pd.DataFrame:
    params = {
        "limit": 100,
        "refine": f'libelle_region:"{region}"',
        "where": "consommation is NOT null",
        "order_by": "date_heure DESC",
    }
    response = requests.get(URL_DATASET, params=params)
    if "error_code" in response.json():
        raise ValueError(
            f"Error fetching data for region {region}: {response.json()['error_code']}, message: {response.json()['message']}"
        )
    data = response.json()["results"]
    df = pd.DataFrame(data)

    df = df.drop(columns=["date"])
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
    return pd.concat(all_dfs)


if __name__ == "__main__":
    energy_df = fetch_energy_all()
    print("\nAperçu du jeu de données Energy :")
    print(energy_df.head())
    print(f"\nTotal enregistrements : {len(energy_df)}")
