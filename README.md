# Energy & Weather Data Pipeline & Anomaly Dashboard

An end-to-end containerized ETL pipeline, Machine Learning anomaly detector, and interactive analytics dashboard built with Python, PostgreSQL, Isolation Forest, and Streamlit.

The project automatically ingests hourly electricity consumption data across French regions alongside localized meteorological metrics, builds a relational Star-Schema Data Mart, flags contextual consumption anomalies using Machine Learning, and visualizes real-time metrics.

---

## Access the dashboard

**The dashboard is self-hosted, and available [here](https://energy-weather.legrobato.site/).**


## Architecture Overview

The pipeline operates across five orchestrated Docker services:

1. **Database (`db`)**: PostgreSQL database storing raw dimensional models and facts (`analytics` schema).
2. **Schema & DB Initialization (`init_db`)**: Creates table schemas and populates reference calendar and region dimension tables.
3. **ETL & ML Engine (`datamart_job`)**:
   * Fetches weather metrics (Open-Meteo API) and electricity data (éCo2mix / ODRE API).
   * Aggregates, cleans, and joins time-series datasets.
   * Runs **Isolation Forest** (scikit-learn) to flag contextual consumption anomalies.
   * Performs deduplicated upserts into the PostgreSQL fact table (`analytics.fact_weather_energy`).
4. **Dashboard (`dashboard`)**: Interactive Streamlit web app with Plotly dual-axis charts, statistical correlation tests (Pearson/Spearman), and anomaly tracking tables.
5. **Scheduler (`scheduler`)**: Runs cron jobs (via Ofelia) to automatically trigger the ETL job hourly.

---

## Tech Stack

* **Language**: Python 3.12
* **Database & ORM**: PostgreSQL 15, SQLAlchemy
* **Data Processing**: Pandas, NumPy
* **Machine Learning**: Scikit-Learn (Isolation Forest)
* **Visualization & Frontend**: Streamlit, Plotly, SciPy
* **Infrastructure**: Docker, Docker Compose, Ofelia (Cron Scheduler)

---

## Data Model (Star Schema)

* **`analytics.dim_date`**: Daily calendar reference (Year, Month, Day, Day of Week, Is Weekend).
* **`analytics.dim_region`**: French administrative regions mapped to representative cities.
* **`analytics.fact_weather_energy`**: Hourly fact table containing:
  * `temp_mean_celsius`, `precipitation_mm`, `wind_speed_kmh`
  * `consumption_mw`
  * `is_anomaly` (Boolean flag) & `anomaly_score` (Float score)

---

## Quickstart

### Prerequisites
* [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) installed.

### 1. Clone the repository
```bash
git clone [https://github.com/Ailyhotte/energy-weather-pipeline.git](https://github.com/Ailyhotte/energy-weather-pipeline.git)
cd energy-weather-pipeline
```

### 2. Environment setup
Create a `.env` file in the project root with:
```bash
POSTGRES_DB=energy_weather_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
POSTGRES_PORT=5432
```

### 3. Build & Run

```bash
docker compose up --build -d
```

### 4. Access the dashboard

Open any browser and navigate to [http://localhost:8501](http://localhost:8501)