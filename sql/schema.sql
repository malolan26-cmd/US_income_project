CREATE TABLE IF NOT EXISTS acs (
 fips text NOT NULL, level text NOT NULL CHECK(level IN ('us','state','county')), name text NOT NULL, year integer NOT NULL,
 estimates jsonb NOT NULL, margins jsonb NOT NULL, loaded_at timestamptz DEFAULT now(), PRIMARY KEY(fips,year));
CREATE TABLE IF NOT EXISTS bea (fips text NOT NULL,year integer NOT NULL,personal_income_per_capita double precision, PRIMARY KEY(fips,year));
CREATE TABLE IF NOT EXISTS bls (fips text NOT NULL,year integer NOT NULL,industry text NOT NULL,ownership text NOT NULL,employment double precision,annual_pay double precision,PRIMARY KEY(fips,year,industry,ownership));
CREATE TABLE IF NOT EXISTS etl_runs (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,source text NOT NULL,year integer NOT NULL,rows_loaded integer NOT NULL, loaded_at timestamptz DEFAULT now());
CREATE OR REPLACE VIEW income_metrics AS SELECT a.fips,a.level,a.name,a.year,
 (estimates->>'households')::double precision AS households,
 (estimates->>'median_income')::double precision AS median_income,
 (margins->>'median_income')::double precision AS median_income_moe,
 (estimates->>'gini')::double precision AS gini,
 (estimates->>'per_capita_income')::double precision AS per_capita_income,
 100*(estimates->>'poverty_count')::double precision / NULLIF((estimates->>'poverty_universe')::double precision,0) AS poverty_rate,
 100*((estimates->>'education_22')::double precision+(estimates->>'education_23')::double precision+(estimates->>'education_24')::double precision+(estimates->>'education_25')::double precision)/NULLIF((estimates->>'education_universe')::double precision,0) AS bachelors_plus_pct,
 (estimates->>'quintile_5')::double precision AS top_quintile_share,
 b.personal_income_per_capita,w.employment,w.annual_pay,a.estimates,a.margins
 FROM acs a LEFT JOIN bea b USING(fips,year) LEFT JOIN bls w ON w.fips=a.fips AND w.year=a.year AND w.industry='10' AND w.ownership='0';
