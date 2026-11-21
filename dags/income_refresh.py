from datetime import datetime,timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from income.load import run

def refresh(source,**context):
    # Explicit release year prevents accidentally requesting unpublished data.
    year=int((context['dag_run'].conf or {}).get('year',2024))
    run(source,year)
with DAG('income_refresh',start_date=datetime(2026,1,1),schedule='0 6 1 * *',catchup=False,max_active_runs=1,default_args={'retries':2,'retry_delay':timedelta(minutes=10)}) as dag:
    first=PythonOperator(task_id='acs',python_callable=refresh,op_kwargs={'source':'acs'})
    second=PythonOperator(task_id='bea',python_callable=refresh,op_kwargs={'source':'bea'})
    third=PythonOperator(task_id='bls',python_callable=refresh,op_kwargs={'source':'bls'})
    first >> second >> third
