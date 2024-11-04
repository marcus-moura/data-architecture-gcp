from ingestion import AnacWebScraper, CloudStorage, BigQueryLoader, DataTransformer
from loguru import logger
from datetime import datetime
import pytz
import sys
import yaml
import os

# Configuração do log
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | {level} | {message}")
logger.level("INFO")

# Configuração do fuso horário
tz = pytz.timezone('America/Sao_Paulo')
        
def load_yaml(name_file: str):
    """Load yaml file with args"""
    path_yaml = os.path.join(os.getcwd(), name_file)
    with open(path_yaml, 'r', encoding='utf-8') as y:
        config = yaml.load(y.read(), yaml.Loader)
    return config

def main(request=None):
    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_LANDING")
    location = os.getenv("LOCATION")
    
    # Load configuration from YAML file
    config = load_yaml("config.yaml")
    extract_config = config["extract"]
    bq_config = config["bigquery"]

    dataset_id = bq_config['dataset_id']
    table_id = bq_config['table_id']
    partition_field = bq_config['partition_field']
    
    # Instanciação das classes
    web_scraper = AnacWebScraper()
    cloud_storage = CloudStorage(bucket_target=bucket_name)
    transformer = DataTransformer()
    bigquery = BigQueryLoader(project_id, location)
    
    filter_date = datetime.strptime(extract_config['start_date'], '%Y-%m-%d').date() # Inicio da carga histórica para a primeira carga da tabela.
    
    last_date_update = bigquery.get_last_update_table(dataset_id, table_id, partition_field)
    if last_date_update:
        filter_date = last_date_update
        logger.info(f"Iniciando o processo de carga incremental com filtro: {filter_date}.")
    else:
        # Se a tabela não existir, realiza uma carga completa
        logger.info(f"Iniciando o processo de carga completa com data de início: {filter_date}")
    
    # Extrai os links para os arquivos CSV da página da web
    file_links = web_scraper.extract_file_links(
                    url=extract_config['url'],
                    filter_date=filter_date,
                    file_format=extract_config['file_format_link'],
                    filter_file=extract_config['filter_file']
                )
    
    # Realiza o download dos arquivos
    for file_link in file_links:
        cloud_storage.download_file_to_gcs(file_link, source=extract_config['source'], subdir_name=extract_config['subdir_name'])

    # Lista os arquivos no Cloud Storage
    blobs = list(cloud_storage.get_list_blobs(extract_config['source'], extract_config['subdir_name']))
    if not blobs:
        logger.warning("Nenhum arquivo encontrado para processar. O pipeline será encerrado!!")
        return

    # Deleta a partição de acordo com o filtro de filter_date para evitar duplicidade
    bigquery.delete_partition(
                dataset_id=dataset_id, 
                table_id=table_id, 
                partition_column=partition_field, 
                partition_start=filter_date,
                partition_end=filter_date
    )

    for blob in blobs:
        # Transformação dos dados
        df = transformer.transform_file_to_df(
                            blob=blob, 
                            partition_field=partition_field,
                            file_format=extract_config['file_format']
        )

        # Carregamento dos dados no BigQuery
        bigquery.load_dataframe(dataframe=df, **bq_config)
        
        # Movendo o arquivo para o diretório de arquivos processados
        logger.info(f"Movendo o arquivo {blob.name} para o diretório de arquivos processados.")
        cloud_storage.move_blob_bucket(blob.name, delete_after=True)
        logger.success(f"Arquivo {blob.name} movido com sucesso!")
        
    return "Ingestão concluída com sucesso!!"

main()