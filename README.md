# US Income Observatory
End-to-end data engineering portfolio project for US household income distribution, inequality, poverty and regional labor markets. Default backfill: 2015–2024 ACS five-year vintages, BEA annual personal income and BLS annual QCEW. Scope: 50 states and DC; county equivalents included, territories excluded.

## Architecture
Census JSON + BEA JSON + BLS CSV → Python adapters (retry, normalization, validation) → PostgreSQL transactional upserts → SQL analytical view / optional dbt → Streamlit + Plotly dashboard. Airflow schedules refreshes; GitHub Actions runs unit tests.

## Quick start
1. Install Docker Desktop with Compose v2. Obtain free keys from https://api.census.gov/data/key_signup.html and https://apps.bea.gov/API/signup/.
2. Copy `.env.example` to `.env` and fill in both keys. Never commit `.env`.
3. From the repository directory run:

```sh
docker compose up -d db
docker compose run --rm etl python -m income.load --start 2024 --end 2024 --source acs
docker compose run --rm etl python -m income.load --start 2024 --end 2024 --source bea
docker compose run --rm etl python -m income.load --start 2024 --end 2024 --source bls
docker compose up -d dashboard
```
Open http://localhost:8501. Load a single year first to verify credentials and connectivity. To backfill:

```sh
docker compose run --rm etl python -m income.load --start 2015 --end 2024
```
A failed source raises an error rather than silently creating fake records. Rerun a failed source/year using the same CLI; primary keys and upserts prevent duplicate facts. Existing rows are updated, not deleted; revisions that remove a geography require explicit reconciliation. No API key is embedded. The BLS slice service may limit historical access; if a year is unavailable, ingest that year from the official annual files with an adapted loader (not implemented).

## Orchestration and analytics
`docker compose --profile orchestration up -d airflow` starts a local Airflow instance. Read the generated admin password with `docker compose logs airflow`. Visit http://localhost:8080; enable `income_refresh`. It refreshes 2024 monthly by default; manually trigger with JSON `{"year": 2025}` when all three releases are available. The year is explicit rather than inferred. Airflow retries source failures. This is a local development deployment, not a production-hosted service.

Run SQL using `docker compose exec db psql -U income -d income` and paste queries from `sql/analysis.sql`. Optional dbt: install `dbt-postgres` in a separate Python environment, then run `dbt build --project-dir dbt --profiles-dir dbt` while the database is running. For Power BI, connect to PostgreSQL at localhost:5432, database `income`, username `income`, password `income_local`; import `public.income_metrics` and `public.bls`. No proprietary PBIX file is included; the working dashboard implementation is Streamlit instead.

## Data model
- `acs`: one geographic unit × survey vintage, text FIPS key, original normalized estimates and 90% margins of error stored as JSONB. US and state values are directly queried rather than averaging county medians or Gini values.
- `bea`: county × year, personal income per capita in dollars (CAINC1 line 3).
- `bls`: county × year × industry × ownership, annual average employment and annual average pay; total all ownerships and selected private supersectors. Suppression is null, not zero.
- `income_metrics`: typed analytics view; left joins preserve ACS records when other sources are unavailable.
- `etl_runs`: successful load counts and timestamps.

ACS definitions are mapped in `income/core.py`: B19001 (16 income bins and household total), B19013 (median), B19083 (Gini), B19301 (per capita income), B17001 (poverty universe and count), B15003 (education universe and bachelor's or higher), B19082 (quintile income shares). Negative sentinel values are null. Derived rates do not include propagated margins of error. Quintile shares are percentages. All historical dollar amounts are in each vintage's dollars; comparisons are nominal, not inflation-adjusted. Regional price parity and CPI adjustment are future extensions, not implemented. ACS five-year periods overlap; BEA and BLS are single-year measures. BEA personal income, ACS household income and BLS pay have distinct definitions and populations. County FIPS changes (especially Connecticut's transition to planning regions) can cause gaps; do not interpret them as economic changes. County map uses Plotly's older boundaries; unmatched FIPS are retained in the table. Dashboard requires network access for map assets.

## Sources
- https://www.census.gov/data/developers/data-sets/acs-5year.2024.html
- https://api.census.gov/data/2024/acs/acs5/groups.html
- https://apps.bea.gov/API/swagger/index.htm
- https://www.bls.gov/cew/additional-resources/open-data/csv-data-slices.htm
- https://www.bls.gov/cew/classifications/industry/high-level-industries.htm

## QA and limits
`python -m pip install requests pytest` then `python -m pytest -q`. Tests cover sentinel values, FIPS, malformed/duplicate geography data, ACS chunk aggregation, bracket reconciliation, BEA parsing and BLS suppression with synthetic fixtures. Python compilation and these unit tests were executed successfully in the authoring environment. Live credentials, Docker, PostgreSQL, dbt and Streamlit runtime were unavailable there; integration and dashboard rendering remain unverified. No actual government data or fabricated data is bundled. Use a 2024 smoke run before full backfill. A production deployment should add secret management, source snapshots, integration tests, boundary versioning, source-specific release discovery and monitoring.
