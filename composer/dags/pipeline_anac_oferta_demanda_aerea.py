from airflow.decorators import dag, task
from airflow.utils.task_group import TaskGroup
from airflow.models.baseoperator import chain
from airflow.providers.google.cloud.operators.dataform import (
    DataformCreateWorkflowInvocationOperator, 
    DataformCreateCompilationResultOperator
)
from airflow.providers.http.operators.http import HttpOperator
from google.auth.transport.requests import Request
from google.oauth2.id_token import fetch_id_token
from airflow.operators.empty import EmptyOperator
from alert.slack import send_fail_alert_slack
from airflow.utils.timezone import pendulum
from datetime import timedelta
import os

PROJECT_ID = os.getenv("PROJECT")
LOCATION = os.getenv("LOCATION")

# Cloudfunctions parameters
URL_BASE_CF = os.getenv("URL_BASE_GCF")
ENDPOINT = "cf_extract_anac_oferta_demanda_aerea_basica_to_bronze"
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
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': send_fail_alert_slack
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
    
    # Chama a Cloud Functions que extrai os dados e faz o carregamento na camada bronze do BigQuery
    cf_extract_load_bronze = HttpOperator(
        task_id="cf_extract_load_to_bronze",
        task_display_name="CF - Extract Load To Bronze",
        method="POST",
        http_conn_id="cf_conn_id",
        endpoint=ENDPOINT,
        headers={'Authorization': f"Bearer {TOKEN_CF}", "Content-Type": "application/json"}
    )
    
    # Inicia um ambiente virtual Python e executa a checagem de qualidade na tabela bronze
    @task(task_display_name="Soda Check Bronze")
    def soda_check_bronze(data_source='bigquery_soda_bronze', checks_subpath='bronze', scan_name='anac_oferta_demanda_aerea_basica'): 
        from soda.scan_operations import run_soda_scan
        return run_soda_scan(data_source, scan_name, checks_subpath)
    
    # Compila o repositório do Dataform
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
    # Cria a tabela silver
    df_transform_silver = DataformCreateWorkflowInvocationOperator(
        task_id="df_transform_bronze_to_silver",
        task_display_name="DF - Transform Bronze To Silver",
        project_id=PROJECT_ID,
        region=LOCATION,
        repository_id=DATAFORM_REPO_ID,
        workflow_invocation={
            "compilation_result": "{{ task_instance.xcom_pull('df_compilation_repository')['name'] }}",
            "invocation_config": {
                "included_targets": [{"database": PROJECT_ID, "name": "tb_anac_oferta_demanda_aerea_basica", "schema": DATASET_SILVER}],
                "transitive_dependencies_included": False,
                "transitive_dependents_included": False,
                "fully_refresh_incremental_tables_enabled": False
            },
        },
    )
    
    # Inicia um ambiente virtual Python e executa a checagem de qualidade na tabela silver
    @task(task_display_name="Soda Check Silver")
    def soda_check_silver(data_source='bigquery_soda_silver', checks_subpath='silver', scan_name='tb_anac_oferta_demanda_aerea_basica'): 
        from soda.scan_operations import run_soda_scan
        return run_soda_scan(data_source, scan_name, checks_subpath)
    
    # Cria a tabela gold analise_trecho_detalhado_voo
    df_gold_trecho_detalhado = DataformCreateWorkflowInvocationOperator(
        task_id="df_gold_analise_trecho_detalhado_voo",
        task_display_name="DF - Gold Analise Trecho Detalhado",
        project_id=PROJECT_ID,
        region=LOCATION,
        repository_id=DATAFORM_REPO_ID,
        workflow_invocation={
            "compilation_result": "{{ task_instance.xcom_pull('df_compilation_repository')['name'] }}",
            "invocation_config": {
                "included_targets": [{"database": PROJECT_ID, "name": "analise_trecho_detalhado_voo", "schema": DATASET_GOLD}],
                "transitive_dependencies_included": False,
                "transitive_dependents_included": False,
                "fully_refresh_incremental_tables_enabled": False
            },
        },
    )
    
    # Cria a tabela gold analise_trecho_consolidado_voo
    df_gold_trecho_consolidado = DataformCreateWorkflowInvocationOperator(
        task_id="df_gold_analise_trecho_consolidado_voo",
        task_display_name="DF - Gold Analise Trecho Consolidado",
        project_id=PROJECT_ID,
        region=LOCATION,
        repository_id=DATAFORM_REPO_ID,
        workflow_invocation={
            "compilation_result": "{{ task_instance.xcom_pull('df_compilation_repository')['name'] }}",
            "invocation_config": {
                "included_targets": [{"database": PROJECT_ID, "name": "analise_trecho_consolidado_voo", "schema": DATASET_GOLD}],
                "transitive_dependencies_included": False,
                "transitive_dependents_included": False,
                "fully_refresh_incremental_tables_enabled": False
            },
        },
    )
    
    finish = EmptyOperator(task_id="finish", task_display_name="Finish 🏆")
    
    # Define a dependência das tasks
    chain(
          start,
          cf_extract_load_bronze,
          soda_check_bronze(),
          df_compilation_repo,
          df_transform_silver,
          soda_check_silver(),
          [df_gold_trecho_detalhado, df_gold_trecho_consolidado],
          finish
    )

pipeline_anac()
