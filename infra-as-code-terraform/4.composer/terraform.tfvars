# Variaveis para criação do composer do ambiente de dev
project_id                  = "data-architecture-tcc"
location                    = "us-east4"
image_version_composer      = "composer-2.8.6-airflow-2.9.1"
composer_name               = "tcc-composer"
sa_composer_name            = "sa-composer"
bucket_name_composer        = "bkt-tcc-composer"
airflow_config_overrides    = {
                                dags_are_paused_at_creation        = "True"
                                parallelism                        = "10"
                                max_active_tasks_per_dag           = "12"
                                metrics_use_pattern_match          = "True"
                                worker_concurrency                 = "6"
                                worker_autoscale                   = "6,2"
                            }
pypi_packages               = {
                                soda-core-bigquery = ""
                                apache-airflow-providers-slack = ""
                            }
environment_size            = "ENVIRONMENT_SIZE_SMALL"
scheduler_config            = {
                                cpu        = 0.5
                                memory_gb  = 2
                                storage_gb = 1
                                count      = 1
                            }
web_server_config           = {
                                cpu        = 0.5
                                memory_gb  = 2
                                storage_gb = 1
                            }
worker_config               = {
                                cpu        = 0.5
                                memory_gb  = 2
                                storage_gb = 1
                                min_count  = 1
                                max_count  = 3
                            }
triggerer_config            = {
                                cpu        = 0.5
                                memory_gb  = 0.5
                                count      = 1
                            }
