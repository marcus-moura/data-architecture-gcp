from google.api_core.exceptions import NotFound
from google.cloud.bigquery.table import TableReference
from google.cloud import bigquery, storage
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger
from io import BytesIO
import pandas as pd
import unidecode
import requests
import zipfile
import pytz
import re
import io

tz = pytz.timezone('America/Sao_Paulo')

# Constantes de nível de módulo
INPUT_DIR = "input_data"
PROCESSED_DIR = "processed_data"

class CloudStorage:
    """
    Classe para interagir com o Cloud Storage.

    :param bucket_target: O nome do bucket do Google Cloud Storage para onde os arquivos CSV serão enviados.
    :param source: Nome da origem do dados, onde será criado um diretório no Cloud Storage(Opcional).
    :param subdir_name: Nome ddo subdiretório que será criado dentro do diretório INPUT_DIR(Opcional).
    """
    def __init__(self, bucket_target: str, source: str = None, subdir_name: str = None) -> None:
        self.bucket_target = bucket_target
        self.source = source
        self.subdir_name = subdir_name
        self.client_gcs = storage.Client()
        self.bucket = self.client_gcs.get_bucket(bucket_target)
    
    def move_blob_bucket(self, blob_name: storage.Blob, delete_after=True) -> None:
        """
        Move um blob para o diretório de arquivos processados no Google Cloud Storage.

        :param blob_name: Nome do blob a ser movido do diretorio input para processed
        :param delete_after: Se True, o blob é excluído após a movimentação (opcional, padrão é True).
        """
        
        blob = self.bucket.blob(blob_name)
        destination_blob_name = blob_name.replace(INPUT_DIR, PROCESSED_DIR)
        self.bucket.copy_blob(blob, self.bucket, new_name=destination_blob_name)
        if delete_after:
            blob.delete()
        
    def get_list_blobs(self, source: str = None, subdir_name: str = None) -> list:
        """
        Lista os blobs no bucket do Google Cloud Storage.
        
        :param source: Nome da origem do dados, onde será criado um diretório no Cloud Storage(Opcional).
        :param subdir_name: Nome do subdiretório(Opcional).
        :return: Lista de blobs.
        """
        
        source = self.source or source
        subdir_name = self.subdir_name or subdir_name
        
        return self.bucket.list_blobs(prefix=f"{INPUT_DIR}/{source}/{subdir_name}")
    
    def download_file_to_gcs(self, url_file: str, source: str = None, subdir_name: str = None) -> None:
        """
        Carrega o conteúdo do arquivo, incluindo arquivos dentro de um .zip, para o Google Cloud Storage.

        :param url_file: URL do arquivo a ser baixado.
        :param source: Nome da origem do dados, onde será criado um diretório no Cloud Storage (Opcional).
        :param subdir_name: Nome do subdiretório (Opcional).
        """
        
        source = self.source or source
        subdir_name = self.subdir_name or subdir_name
        file_name = url_file.split('/')[-1]
        
        # Define o diretório base no GCS
        base_blob_dir = f"{INPUT_DIR}/{source}/{subdir_name}"

        logger.info(f"Baixando arquivo {file_name} da URL {url_file}...")

        # Baixa o conteúdo do arquivo da URL
        response = requests.get(url_file)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            if file_name.endswith('.zip'):
                # Abre o conteúdo do .zip e extrai cada arquivo
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    for zip_info in z.infolist():
                        # Define o nome do arquivo e o blob path no GCS
                        extracted_file_name = zip_info.filename
                        blob_name = f"{base_blob_dir}/{extracted_file_name}"
                        
                        # Carrega o conteúdo do arquivo extraído para o GCS
                        with z.open(zip_info) as extracted_file:
                            blob = self.bucket.blob(blob_name)
                            blob.upload_from_file(extracted_file, content_type='application/octet-stream')
                            logger.info(f"Arquivo {extracted_file_name} carregado com sucesso para {blob_name}.")
            else:
                # Carrega o arquivo diretamente para o GCS se não for .zip
                blob_name = f"{base_blob_dir}/{file_name}"
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(response.content)
                logger.info(f"Arquivo {file_name} carregado com sucesso para {blob_name}.")
        else:
            logger.error(f"Falha ao baixar o arquivo {file_name} da URL {url_file}. Status code: {response.status_code}")

class AnacWebScraper:
    """
    Classe para realizar a extração de arquivo da Web.
    """
    @staticmethod
    def extract_file_links(url: str, filter_date: str, filter_file: str, file_format: str) -> list:
        """
        Extrai os links para arquivos CSV de uma página web e os carrega no Google Cloud Storage para o path {INPUT_DIR}/{source}/{subdir_name}/{filename}

        :param url: URL da página web.
        :param start_year: Ano de início para a extração dos arquivos.
        :param end_year: Ano de final para a extração dos arquivos.
        :return: None
        """
        logger.info(f"Obtendo a lista de links dos arquivos...")
        
        filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
        
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            files_found = False  # Variável para rastrear se foram encontrados arquivos
      
            file_links = []
            for link in links:
                href = link.get('href', '')
                if href.endswith(f'.{file_format}') and filter_file in href:
                    
                    # Extrai ano e mês do link usando uma expressão regular
                    date_match = re.search(r'(\d{4})-(\d{2})', href).group()
                    file_date = datetime.strptime(date_match, '%Y-%m').date()
                   
                    if file_date >= filter_date:
                        file_links.append(href)
                        files_found = True
            
            if not files_found:
                logger.warning(f"Não há arquivos para o filtro: {filter_date}")
            return file_links
        else:
            logger.error(f"Falha ao acessar a URL {url}. Status code: {response.status_code}")
            return []

class DataTransformer:
    
    @staticmethod
    def _clean_and_normalize_text(text: str) -> str:
        """
        Limpa e normaliza o texto removendo caracteres especiais e substituindo por '_'.
        """
        return unidecode.unidecode(re.sub(r'[-/\s(\)]+', '_', text))
    
    @staticmethod
    def _parse_df_to_str_nan(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte todos os campos do DataFrame para strings, preservando os valores NaN, None e Nat como NoneType.
        """
        return df.map(lambda x: str(x) if pd.notnull(x) else None) 
    
    def transform_file_to_df(self, blob: storage.Blob, partition_field: str, partition_format: str = "%Y%m", file_format: str = "csv") -> pd.DataFrame:
        """
        Transforma os dados do arquivo em um DataFrame pandas.

        :param blob: Blob do Google Cloud Storage.
        :param file_format: formato do arquivo
        :return: DataFrame pandas.
        """
        try:
            if blob.name.endswith(f'.{file_format}'):
                logger.info(f"Carregando arquivo {blob.name} em bytes!")
                # Carrega o arquivo em bytes
                file_content = blob.download_as_bytes()
            
                logger.info("Transformando os dados...")
                df = pd.read_csv(BytesIO(file_content), delimiter=";", encoding='ISO 8859-1')
                # Limpa e normaliza os nomes das colunas
                df.columns = [self._clean_and_normalize_text(column) for column in df.columns]
                
                # Converte todas as colunas para string
                df = self._parse_df_to_str_nan(df)
                
                # Converte a coluna 'ano_particao' para o tipo de dados de data
                df[f'{partition_field}'] = pd.to_datetime(df[f'{partition_field}'], format=f'{partition_format}').dt.date
                
                # Adiciona colunas extras
                df['data_ingestao'] = datetime.now(tz=tz).date()
                df['nome_arquivo'] = blob.name.split("/")[-1]
                
                logger.success("Transformação realizada com sucesso.")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar o arquivo: {e}")
            return None

class BigQueryLoaderError(Exception):
    pass

class BigQueryLoader:
    """
    Class responsible for loading data into BigQuery.
    
    :param: project_id: The ID of the Google Cloud project.
    :param: dataset_id: The ID of the dataset.
    :param: location: The location of the dataset.
    :param: client (bigquery.Client, optional): The BigQuery client. Defaults to bigquery.Client().
    """
    def __init__(self, 
        project_id: str,
        location: str,
        client: bigquery.Client = bigquery.Client()
        ) -> None:
        self.project_id = project_id
        self.location = location
        self.client = client

    def table_exists(self, dataset_id: str, table_id: str):
        """ Check if table exists"""
        table_ref = self._get_destination_table(dataset_id, table_id)
        try:
            self.client.get_table(table_ref)
            return True
        except Exception as e:
            if isinstance(e, NotFound):
                return False
            else:
                raise e

    def _add_labels(self, table_ref: str, labels: str) -> None:
        """
        Adds labels to a BigQuery table.

        :param: table_ref: The destination table.
        :param: labels: The labels to be added.
        """
        table = self.client.get_table(table_ref)
        existing_labels = table.labels
        if existing_labels != labels:
            table.labels = labels
            table = self.client.update_table(table, ["labels"])
            logger.info(f"Added labels to {table.table_id}.")

    def get_last_update_table(self, dataset: str, table: str, column_ref: str):
        """ Obtem a última data de atualização do dado """

        client = bigquery.Client(project=self.project_id)
        query = f"SELECT max({column_ref}) as updated_at FROM `{self.project_id}.{dataset}.{table}`"

        try:
            logger.info(f"Getting last update for table: {table}")
            query_bq = client.query(query)
            max_date = [value['updated_at'] for value in query_bq][0]
        except NotFound:
            max_date = None
            logger.warning(f"Table: {table} not found!")

        return max_date

    def _get_destination_table(self, dataset_id: str, table_id: str) -> str:
        """
        Builds the destination table name in BigQuery.
        
        :param:  table_id: The name of the table.
        Returns:
            str: The destination table name.
        """
        return TableReference.from_string(f"{self.project_id}.{dataset_id}.{table_id}")

    def load_dataframe(self, dataframe: pd.DataFrame, table_id: str, dataset_id: str, schema_fields: str = None, description: str = None, 
                        labels: dict = None, create_disposition: str = "CREATE_IF_NEEDED", write_disposition: str = "WRITE_APPEND", 
                        autodetect: str = True, schema_relax: str = None, time_partitioning: str = None, partition_field: str = None
        ) -> None:
        """
        Loads DataFrame data into BigQuery.

        :param: dataframe (pd.DataFrame): The DataFrame data to be loaded.
        :param: dataset_id: The ID of the dataset.
        :param: table_id: The name of the table.
        :param: schema_fields (optional): The schema fields for the data. Defaults to None.
        :param: description (optional): The table description. Defaults to None.
        :param: create_disposition (optional): The table creation disposition. Defaults to 'CREATE_IF_NEEDED'.
        :param: write_disposition: The write disposition for the job. Defaults to None.
        :param: autodetect (optional): Whether to automatically detect schema. Defaults to True.
        :param: schema_relax (optional): Whether to allow schema field addition. Defaults to False.
        :param: time_partitioning (optional): The type of time partitioning. Defaults to None.
        :param: partition_field (optional): The field to partition the data by. Defaults to None.
        """
        table_ref = self._get_destination_table(dataset_id, table_id)
        
        job_config = bigquery.LoadJobConfig(
            schema=schema_fields,
            destination_table_description=description,
            create_disposition=create_disposition,
            write_disposition=write_disposition,
            autodetect=autodetect,
            schema_update_options=bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION if schema_relax else None,
            time_partitioning=bigquery.TimePartitioning(type_=time_partitioning.upper(), field=partition_field) if time_partitioning else None
        )
  
        job = self.client.load_table_from_dataframe(dataframe=dataframe, destination=table_ref, location=self.location, job_config=job_config)
        try:
            logger.info(f"Inserting data into the {table_id} in BigQuery!")
            job.result()
            logger.success("Successfully entered data")
            if labels:
                self._add_labels(table_ref, labels)
        except Exception as e:
            raise BigQueryLoaderError(f"Failed to insert data into BigQuery: {str(e)}")
    

    def delete_partition(self, dataset_id: str, table_id: str, partition_column: str, partition_start: str, partition_end: str):
        """
        Deleta a partição mais recente na tabela BigQuery.

        :param dataset_id: ID do conjunto de dados no BigQuery.
        :param table_id: ID da tabela no BigQuery.
        :param partition_column: Nome da coluna de partição.
        :param partition_start: Anos de início da partição a ser deletadas.
        :param partition_end: Anos final da partição a ser deletadas.
        """
        table_ref = self._get_destination_table(dataset_id, table_id)
        try:
            query = f"DELETE FROM `{table_ref}` WHERE {partition_column} >= '{partition_start}' AND {partition_column} <= '{partition_end}'"
            logger.info(f"Deletando partição com a query: {query}")
            
            job = self.client.query(query)
            
            job = job.result() # Espera até que a consulta seja concluída
            logger.info(f"Partições deletadas com sucesso na tabela '{table_id}'. Total de {job.num_dml_affected_rows} linhas removidas.")
        except NotFound:
            logger.warning(f"A partição não deletada! Tabela: {table_id} não foi encontrada.")
        except Exception as e:
            logger.warning(f"Não foi possível deletar a partição: {e}.")
            