import pytest
from income.core import number,county,acs_chunk,validate,FIELDS,BRACKETS,acs,bea,bls

def test_numbers():
    assert number('1,234')==1234
    for x in ['-666666666','(NA)','NaN','inf',None]: assert number(x) is None

def test_county():
    assert county('01001') and county('11001')
    assert not any(county(f) for f in ['01000','72001','123','ABCDE'])

def test_chunk():
    assert list(acs_chunk([['NAME','state','county'],['Autauga','01','001'],['Excluded','72','001']],'county'))==['01001']
    with pytest.raises(ValueError): acs_chunk([['NAME','state','county'],['A','01','001'],['B','01','001']],'county')

def test_validation():
    v={k:None for k in FIELDS}; v.update(gini=.4,households=16,poverty_count=1,poverty_universe=2); v.update({f'bracket_{i}':1 for i in range(2,18)}); validate(v)
    assert len(BRACKETS)==16
    with pytest.raises(ValueError): validate(dict(v,gini=1.1))
    with pytest.raises(ValueError): validate(dict(v,households=15))
    with pytest.raises(ValueError): validate(dict(v,poverty_count=3))
class Response:
    def __init__(self,data=None,text=''): self.data=data; self.text=text
    def raise_for_status(self): pass
    def json(self): return self.data
class ACS:
    def get(self,url,params,timeout):
        h=params['get'].split(','); vals=['Autauga' if x=='NAME' else '0' for x in h]; return Response([h+['state','county'],vals+['01','001']])
def test_acs_complete():
    rows=acs(ACS(),2024,'fake','county'); assert len(rows)==1 and len(rows[0][4])==len(FIELDS)
class BEA:
    def get(self,*a,**kw): return Response({'BEAAPI':{'Results':{'Data':[{'GeoFips':'01001','TimePeriod':'2024','DataValue':'40,000'}]}}})
def test_bea(): assert bea(BEA(),2024,'fake')==[('01001',2024,40000)]
class BLS:
    def get(self,*a,**kw): return Response(text='area_fips,own_code,industry_code,size_code,year,disclosure_code,annual_avg_emplvl,avg_annual_pay\n01001,0,10,0,2024,,100,50000\n01003,0,10,0,2024,N,0,0\n')
def test_bls(): assert bls(BLS(),2024)==[('01001',2024,'10','0',100,50000),('01003',2024,'10','0',None,None)]
