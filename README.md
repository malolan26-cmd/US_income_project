# US Income Observatory

An end-to-end data engineering and analytics project exploring income distribution, wage trends, and economic inequality across the United States.

## Tech Stack

**Python | SQL | PostgreSQL | Apache Airflow | Docker | Streamlit | Plotly | dbt**

## Data Sources

- **U.S. Census Bureau (ACS):** Household income, poverty rates, and income inequality.
- **Bureau of Economic Analysis (BEA):** Regional income and economic indicators.
- **Bureau of Labor Statistics (BLS):** Employment and industry-level wages.

## Project Architecture

`Government APIs → Python ETL → Apache Airflow → PostgreSQL → Streamlit Dashboard`

## Key Features

- Automated ETL pipeline integrating multiple government data sources.
- PostgreSQL database with validated, standardized economic data.
- Apache Airflow orchestration for scheduled ingestion and workflow monitoring.
- Interactive Streamlit dashboard for geographic comparisons, income trends, and inequality analysis.
- Docker containerization for reproducible deployment.

## Getting Started

**1. Clone the repository**

```bash
git clone <repository-url>
cd us-income
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Add your Census and BEA API keys to `.env`.

**3. Start the database**

```bash
docker compose up -d db
```

**4. Run the ETL pipeline**

```bash
docker compose run --rm etl python -m income.load --start 2015 --end 2024
```

**5. Launch the dashboard**

```bash
docker compose up -d dashboard
```

Open **http://localhost:8501**.

**6. Start Airflow (optional)**

```bash
docker compose --profile orchestration up -d airflow
```

Open **http://localhost:8080** to monitor and trigger the `income_refresh` pipeline.

## Purpose

Demonstrates practical experience in API integration, ETL development, relational database management, workflow orchestration, and interactive data visualization.
