"""Source adapters and validation; no database dependency."""
import csv, io, re, math
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STATES=set('01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56'.split())
FIELDS={'households':'B19001_001','median_income':'B19013_001','gini':'B19083_001','per_capita_income':'B19301_001','poverty_universe':'B17001_001','poverty_count':'B17001_002','education_universe':'B15003_001',**{f'education_{i}':f'B15003_{i:03}' for i in range(22,26)},**{f'bracket_{i}':f'B19001_{i:03}' for i in range(2,18)},**{f'quintile_{i}':f'B19082_{i+1:03}' for i in range(1,6)}}
BRACKETS=['Under $10k','$10–15k','$15–20k','$20–25k','$25–30k','$30–35k','$35–40k','$40–45k','$45–50k','$50–60k','$60–75k','$75–100k','$100–125k','$125–150k','$150–200k','$200k+']

def session():
    s=requests.Session(); s.mount('https://',HTTPAdapter(max_retries=Retry(total=4,backoff_factor=1,status_forcelist=[429,500,502,503,504],allowed_methods=['GET']))); s.headers['User-Agent']='US-income-research/1.0 (public economic data)'; return s

def number(x):
    try: v=float(str(x).replace(',',''))
    except (ValueError,TypeError): return None
    return v if math.isfinite(v) and v>=0 else None

def county(f): return bool(re.fullmatch(r'\d{5}',f)) and f[:2] in STATES and f[2:]!='000'

def acs_chunk(payload, level):
    if not isinstance(payload,list) or len(payload)<2: raise ValueError('Empty or invalid ACS response')
    header,*rows=payload; out={}
    for row in rows:
        if len(row)!=len(header): raise ValueError('Invalid ACS row width')
        r=dict(zip(header,row)); f=r['state']+r.get('county','000') if level!='us' else '00000'
        if level=='county' and not county(f): continue
        if level=='state' and f[:2] not in STATES: continue
        if f in out: raise ValueError('Duplicate ACS geography')
        out[f]=r
    return out

def acs(s,year,key,level):
    variables=[v+t for v in FIELDS.values() for t in ('E','M')]; merged={}
    for start in range(0,len(variables),45):
        p={'get':','.join(['NAME']+variables[start:start+45]),'for':{'county':'county:*','state':'state:*','us':'us:1'}[level],'key':key}
        if level=='county': p['in']='state:*'
        response=s.get(f'https://api.census.gov/data/{year}/acs/acs5',params=p,timeout=90); response.raise_for_status(); chunk=acs_chunk(response.json(),level)
        if merged and merged.keys()!=chunk.keys(): raise ValueError('ACS chunks have different geographies')
        for f,r in chunk.items(): merged.setdefault(f,{}).update(r)
    result=[]
    for f,r in merged.items():
        values={k:number(r[v+'E']) for k,v in FIELDS.items()}; moe={k:number(r[v+'M']) for k,v in FIELDS.items()}; validate(values)
        result.append((f,level,r['NAME'],year,values,moe))
    if not result: raise ValueError('No ACS records')
    return result

def validate(v):
    if v['gini'] is not None and v['gini']>1: raise ValueError('Invalid Gini')
    if v['poverty_count'] is not None and v['poverty_universe'] is not None and v['poverty_count']>v['poverty_universe']: raise ValueError('Invalid poverty count')
    b=[v[f'bracket_{i}'] for i in range(2,18)]
    if None not in b and v['households'] is not None and sum(b)!=v['households']: raise ValueError('Income brackets do not reconcile')

def bea(s,year,key):
    r=s.get('https://apps.bea.gov/api/data/',params={'UserID':key,'method':'GetData','datasetname':'Regional','TableName':'CAINC1','LineCode':'3','GeoFips':'COUNTY','Year':year,'ResultFormat':'JSON'},timeout=120); r.raise_for_status()
    results=r.json()['BEAAPI']['Results']; rows=results.get('Data') if isinstance(results,dict) else None
    if not rows: raise ValueError('BEA returned no data; check credentials and year')
    out=[(x['GeoFips'].strip(),year,number(x['DataValue'])) for x in rows if county(x['GeoFips'].strip()) and str(x['TimePeriod'])==str(year)]
    if not out: raise ValueError('No BEA counties')
    return out

def bls(s,year,industry='10'):
    r=s.get(f'https://data.bls.gov/cew/data/api/{year}/a/industry/{industry}.csv',timeout=120); r.raise_for_status()
    out=[]
    for x in csv.DictReader(io.StringIO(r.text.lstrip('\ufeff'))):
        f=x['area_fips']; own=x['own_code']
        if not county(f) or x['industry_code']!=industry or own!=('0' if industry=='10' else '5') or x.get('size_code','0')!='0': continue
        if int(x['year'])!=year: raise ValueError('Unexpected BLS year')
        suppressed=x.get('disclosure_code')=='N'; out.append((f,year,industry,own,None if suppressed else number(x['annual_avg_emplvl']),None if suppressed else number(x['avg_annual_pay'])))
    if not out: raise ValueError('No BLS county records')
    return out
