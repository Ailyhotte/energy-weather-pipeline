CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Table de dimension Temps
CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Table de dimension Région
CREATE TABLE IF NOT EXISTS analytics.dim_region (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) UNIQUE NOT NULL,
    main_city VARCHAR(100) NOT NULL
);

-- Table de Faits : Météo + Énergie
CREATE TABLE IF NOT EXISTS analytics.fact_weather_energy (
    fact_id SERIAL PRIMARY KEY,
    date_key INT REFERENCES analytics.dim_date(date_key),
    region_id INT REFERENCES analytics.dim_region(region_id),
    hour INT NOT NULL CHECK (hour BETWEEN 0 AND 23),
    temp_mean_celsius FLOAT,
    precipitation_mm FLOAT,
    wind_speed_max_kmh FLOAT,
    consumption_mw FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_date_region UNIQUE (date_key, region_id)
);