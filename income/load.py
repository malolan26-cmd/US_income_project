import argparse, os, logging
from pathlib import Path
from income.core import session, acs, bea, bls
ROOT=Path(__file__).resolve().parents[1]

def run(source,year):
    import psycopg
    from psycopg.types.json import Jsonb
    s=session()
    if source=='acs':
        rows=[(f,l,n,y,Jsonb(v),Jsonb(m)) for level in ('us','state','county') for f,l,n,y,v,m in acs(s,year,os.environ['CENSUS_API_KEY'],level)]
        query='INSERT INTO acs(fips,level,name,year,estimates,margins) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(fips,year) DO UPDATE SET level=excluded.level,name=excluded.name,estimates=excluded.estimates,margins=excluded.margins,loaded_at=now()'
    elif source=='bea':
        rows=bea(s,year,os.environ['BEA_API_KEY']); query='INSERT INTO bea VALUES (%s,%s,%s) ON CONFLICT(fips,year) DO UPDATE SET personal_income_per_capita=excluded.personal_income_per_capita'
    elif source=='bls':
        rows=[r for industry in ['10','1011','1012','1013','1021','1022','1023','1024','1025','1026','1027'] for r in bls(s,year,industry)]
        query='INSERT INTO bls VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(fips,year,industry,ownership) DO UPDATE SET employment=excluded.employment,annual_pay=excluded.annual_pay'
    else: raise ValueError(source)
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT/'sql/schema.sql').read_text()); cur.executemany(query,rows); cur.execute('INSERT INTO etl_runs(source,year,rows_loaded) VALUES (%s,%s,%s)',(source,year,len(rows)))
    logging.info('%s %s: %s rows',source,year,len(rows))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--start',type=int,default=2015); p.add_argument('--end',type=int,default=2024); p.add_argument('--source',choices=['acs','bea','bls','all'],default='all'); a=p.parse_args(); logging.basicConfig(level=logging.INFO)
    if a.start>a.end: p.error('start must be <= end')
    for year in range(a.start,a.end+1):
        for source in (['acs','bea','bls'] if a.source=='all' else [a.source]): run(source,year)
if __name__=='__main__': main()
