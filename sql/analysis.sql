-- Highest median income, with published 90% margin of error
SELECT name,median_income,median_income_moe FROM income_metrics WHERE level='county' AND year=2024 AND median_income IS NOT NULL ORDER BY median_income DESC LIMIT 20;
-- Inequality with at least 10,000 households
SELECT name,gini,top_quintile_share FROM income_metrics WHERE level='county' AND year=2024 AND households>=10000 AND gini IS NOT NULL ORDER BY gini DESC LIMIT 20;
-- Nominal change over nonoverlapping five-year windows (same FIPS only)
SELECT b.name,a.median_income AS income_2019,b.median_income AS income_2024,100*(b.median_income/a.median_income-1) AS pct_change FROM income_metrics a JOIN income_metrics b USING(fips) WHERE a.year=2019 AND b.year=2024 AND b.level='county' AND a.median_income>0 ORDER BY pct_change DESC NULLS LAST;
-- State education-income association (not causal)
SELECT corr(bachelors_plus_pct,median_income) FROM income_metrics WHERE level='state' AND year=2024;
-- County industry pay and employment
SELECT a.name,b.industry,b.employment,b.annual_pay FROM bls b JOIN acs a USING(fips,year) WHERE b.year=2024 AND b.ownership='5' ORDER BY b.annual_pay DESC NULLS LAST LIMIT 50;
-- Missing joins are not zeros
SELECT year,count(*) AS counties,count(personal_income_per_capita) AS bea_matches,count(annual_pay) AS bls_matches FROM income_metrics WHERE level='county' GROUP BY year ORDER BY year;
