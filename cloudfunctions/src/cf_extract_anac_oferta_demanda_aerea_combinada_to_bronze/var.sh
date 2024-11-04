#!/bin/bash

# Nome da função Cloud Function
export FUNCTION_NAME="cf_extract_anac_oferta_demanda_aerea_combinada_to_bronze"
# ID do projeto no Google Cloud
export PROJECT="data-architecture-tcc"
# Região onde a função será implantada
export REGION="us-east4"
# Caminho para o diretório contendo o código-fonte da função
export SOURCE="source_code"
# Tempo de execução da função (por exemplo, python312 para Python 3.12)
export RUNTIME="python312"
# Ponto de entrada para a função (nome da função a ser chamada)
export ENTRY_POINT="main"
# Número de CPUs atribuídas à função
export CPU="1"
# Quantidade de memória atribuída à função (por exemplo, "1Gi" para 1 gigabyte)
export MEMORY="2Gi"
# Tempo limite máximo de execução da função em segundos
export TIMEOUT="1200s"
# Número máximo de instâncias da função que podem ser executadas simultaneamente
export CONCURRENCY="1"
# Email da Conta de serviço associada à função (service account)
export SERVICE_ACCOUNT="sa-cloudfunctions@data-architecture-tcc.iam.gserviceaccount.com"
# Configuração de segredos para a função (por exemplo, api_token)
# set-secrets= secret_env_var=secret_name ou secret_path=projects/{project_id}/secrets/{secret_name}:{version}
# export SET_SECRETS="OBS_TURISTICO_API_KEY_GOOGLE_PLACES=projects/${PROJECT}/secrets/OBS_TURISTICO_API_KEY_GOOGLE_PLACES:latest"
export SET_SECRETS=""
# Número mínimo de instâncias a serem mantidas ativas
export MIN_INSTANCES="1"
# Número máximo de instâncias que a função pode criar dinamicamente
export MAX_INSTANCES="3"
# Variáveis de ambiente adicionais que podem ser necessárias para a função
# set-env-vars=KEY=VALUE,...
export ENV_VARS="PROJECT_ID=${PROJECT},LOCATION=${REGION},BUCKET_LANDING=bkt-tcc-landing"
