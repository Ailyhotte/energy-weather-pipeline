import requests
import pandas as pd

URL_DATASET = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/records"

REGIONS = ["Pays de la Loire", "Nouvelle-Aquitaine"]


def fetch_energy_region(region: str) -> pd.DataFrame:
    params = {"limit": 2, "refine": f'libelle_region:"{region}"'}
    response = requests.get(URL_DATASET, params=params)
    data = response.json()["results"]
    df = pd.DataFrame(data)

    df = df.drop(columns=["date"])
    df = df.rename(columns={"date_heure": "date"})
    df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_energy_all_regions() -> pd.DataFrame:
    all_dfs = [fetch_energy_region(region) for region in REGIONS]
    return pd.concat(all_dfs)


if __name__ == "__main__":
    energy_df = fetch_energy_all_regions()
    print("\nAperçu du jeu de données Energy :")
    print(energy_df.head())
    print(f"\nTotal enregistrements : {len(energy_df)}")
