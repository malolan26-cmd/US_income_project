import os
import pandas as pd
import plotly.express as px
import streamlit as st
import psycopg
from income.core import BRACKETS
st.set_page_config(page_title='US Income Observatory',layout='wide')
st.title('US Income Observatory')
st.caption('ACS five-year estimates • BEA personal income • BLS covered employment and wages')
@st.cache_data(ttl=300)
def read(query,params=()):
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute(query,params); return pd.DataFrame(cur.fetchall(),columns=[x.name for x in cur.description])
try:
    years=read('SELECT DISTINCT year FROM income_metrics ORDER BY year DESC').year.tolist()
except Exception:
    st.error('Database unavailable. Start PostgreSQL and run the ETL using the README.'); st.stop()
if not years:
    st.info('No data loaded. Run the ETL first.'); st.stop()
year=st.sidebar.selectbox('ACS period ending',years)
level=st.sidebar.radio('Geography',['state','county'])
df=read('SELECT * FROM income_metrics WHERE year=%s AND level=%s',(year,level))
if df.empty: st.warning('No records for this selection.'); st.stop()
metric=st.sidebar.selectbox('Map / ranking metric',['median_income','gini','poverty_rate','bachelors_plus_pct','per_capita_income','top_quintile_share']+(['annual_pay','personal_income_per_capita'] if level=='county' else []))
if level=='county':
    states=read("SELECT fips,name FROM income_metrics WHERE level='state' AND year=%s ORDER BY name",(year,))
    choices={'All states':None,**dict(zip(states.name,states.fips.str[:2]))}; selected=st.sidebar.selectbox('State',list(choices))
    if choices[selected]: df=df[df.fips.str.startswith(choices[selected])]
if df.empty: st.warning('No matching geographies.'); st.stop()
name=st.selectbox('Focus geography',df.sort_values('name').name.tolist()); row=df[df.name==name].iloc[0]
def fmt(v,pattern): return 'Unavailable' if pd.isna(v) else format(v,pattern)
a,b,c,d=st.columns(4)
a.metric('Median household income',('$'+fmt(row.median_income,',.0f') if pd.notna(row.median_income) else 'Unavailable'))
b.metric('Gini coefficient',fmt(row.gini,'.3f')); c.metric('Poverty rate',fmt(row.poverty_rate,'.1f')+'%' if pd.notna(row.poverty_rate) else 'Unavailable'); d.metric('Households',fmt(row.households,',.0f'))
left,right=st.columns(2)
with left:
    if level=='county':
        try:
            import json, urllib.request
            @st.cache_data
            def boundaries():
                with urllib.request.urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json',timeout=40) as f: return json.load(f)
            geo=boundaries(); st.plotly_chart(px.choropleth(df,geojson=geo,locations='fips',color=metric,hover_name='name',scope='usa'),use_container_width=True)
            st.caption('Map uses older county boundaries; unmatched or changed county codes remain in the table.')
        except Exception: st.warning('Map unavailable; all records remain in the table.')
    else:
        codes='AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
        from income.core import STATES
        df=df.assign(abbr=df.fips.str[:2].map(dict(zip(sorted(STATES),codes))))
        st.plotly_chart(px.choropleth(df,locations='abbr',locationmode='USA-states',color=metric,hover_name='name',scope='usa'),use_container_width=True)
with right:
    ranked=df.dropna(subset=[metric]).nlargest(15,metric).sort_values(metric)
    st.plotly_chart(px.bar(ranked,x=metric,y='name',orientation='h',title='Top 15 geographies'),use_container_width=True)
v=row.estimates
br=pd.DataFrame({'bracket':BRACKETS,'households':[v.get(f'bracket_{i}') for i in range(2,18)]})
q=pd.DataFrame({'quintile':[str(i) for i in range(1,6)],'share':[v.get(f'quintile_{i}') for i in range(1,6)]})
a,b=st.columns(2)
with a: st.plotly_chart(px.bar(br,x='bracket',y='households',title='Household income distribution'),use_container_width=True)
with b: st.plotly_chart(px.bar(q,x='quintile',y='share',title='Income share by quintile (%)'),use_container_width=True)
hist=read('SELECT year,median_income,gini,poverty_rate FROM income_metrics WHERE fips=%s ORDER BY year',(row.fips,))
st.plotly_chart(px.line(hist,x='year',y='median_income',markers=True,title='Historical median income (nominal dollars)'),use_container_width=True)
st.caption('Overlapping ACS five-year periods are not independent annual observations. Historical geography changes may interrupt series.')
if level=='county':
    wages=read("SELECT industry,employment,annual_pay FROM bls WHERE fips=%s AND year=%s AND ownership='5' ORDER BY industry",(row.fips,year))
    if not wages.empty: st.plotly_chart(px.bar(wages,x='industry',y='annual_pay',title='Private-sector annual pay by BLS supersector code'),use_container_width=True)
cols=[c for c in df.columns if c not in ('estimates','margins')]; st.dataframe(df[cols],use_container_width=True); st.download_button('Export filtered metrics',df[cols].to_csv(index=False),'income_metrics.csv','text/csv')
