from airflow.decorators import dag
from airflow.utils.task_group import TaskGroup
from airflow.providers.google.cloud.operators.dataform import (
    DataformCreateWorkflowInvocationOperator, 
    DataformCreateCompilationResultOperator
)
from airflow.providers.http.operators.http import HttpOperator
from google.auth.transport.requests import Request
from google.oauth2.id_token import fetch_id_token
from airflow.operators.empty import EmptyOperator
from airflow.utils.timezone import pendulum
from datetime import timedelta
import os

PROJECT_ID = os.getenv("PROJECT")
LOCATION = os.getenv("LOCATION")

# Cloudfunctions parameters
URL_BASE_CF = os.getenv("URL_BASE_GCF")
ENDPOINT = "cf_extract_anac_oferta_demanda_aerea_to_bronze"
URL_FULL = f"{URL_BASE_CF}/{ENDPOINT}"
TOKEN_CF = fetch_id_token(Request(), URL_FULL)

# Dataform parameters
DATAFORM_REPO_ID = "tcc-repository-dataform"
DATASET_SILVER = "tcc_silver"
DATASET_GOLD = "tcc_gold"

default_args = {
    'owner': "Marcus/Rachel",
    'depends_on_past': False,
    'start_date': pendulum.today("America/Sao_Paulo").add(days=-1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id="pipeline_anac_oferta_demanda_aerea",
    max_active_runs=1,
    schedule=None,
    catchup=False,
    description="Pipeline dos dados anac sobre oferta e demanda aerea",
    default_args=default_args,
    dagrun_timeout=timedelta(minutes=40),
    tags=["source:anac","zones:bronze-silver-gold"]
)
def pipeline_anac():

    start = EmptyOperator(task_id="start", task_display_name="Start 🏁")
    
    cf_run_extract = HttpOperator(
        task_id="cf_extract_load_to_bronze",
        task_display_name="CF - Extract Load To Bronze",
        method="POST",
        http_conn_id="cf_conn_id",
        endpoint=ENDPOINT,
        headers={'Authorization': f"Bearer {TOKEN_CF}", "Content-Type": "application/json"}
    )
    
    df_compilation_repo = DataformCreateCompilationResultOperator(
        task_id=f"df_compilation_repository",
        task_display_name="DF - Compilation Repository",
        project_id=PROJECT_ID,
        region=LOCATION,
        repository_id=DATAFORM_REPO_ID,
        compilation_result={
            "git_commitish": "main",
            "code_compilation_config": {"default_database": PROJECT_ID},
        }
    )
    
    df_transform_silver = DataformCreateWorkflowInvocationOperator(
        task_id="df_transform_bronze_to_silver",
        task_display_name="DF - Transform Bronze To Silver",
        project_id=PROJECT_ID,
        region=LOCATION,
        repository_id=DATAFORM_REPO_ID,
        workflow_invocation={
            "compilation_result": "{{ task_instance.xcom_pull('df_compilation_repository')['name'] }}",
            "invocation_config": {
                "included_targets": [{"database": PROJECT_ID, "name": "tb_anac_oferta_demanda_aerea", "schema": DATASET_SILVER}],
                "transitive_dependencies_included": False,
                "transitive_dependents_included": False,
                "fully_refresh_incremental_tables_enabled": False
            },
        },
    )
    
    finish = EmptyOperator(task_id="finish", task_display_name="Finish 🏆")
    
    start >> cf_run_extract >> df_compilation_repo >> df_transform_silver >> finish
    
pipeline_anac()
