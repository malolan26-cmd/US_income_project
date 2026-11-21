select *, fips || '-' || year::text as county_year from {{ source('warehouse','income_metrics') }} where level='county'
