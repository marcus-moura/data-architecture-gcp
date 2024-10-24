variable "project_id" {
  type        = string
  description = "ID do Projeto onde o composer será criado"
  nullable    = false
}

variable "project_number" {
  type        = string
  description = "Número do Projeto onde o composer será criado"
  nullable    = false
}

variable "location" {
  type        = string
  description = "Região onde o composer será criado"
  default     = "southamerica-east1"
  nullable    = false
}

# Config relacionadas ao composer
variable "composer_name" {
  type        = string
  description = "Nome da instância do composer"
  nullable    = false
}

variable "image_version_composer" {
  type        = string
  description = "Versão do composer"
  nullable    = false
}

variable "sa_composer_name" {
  type        = string
  description = "Nome da service account que será criada para execução do composer"
  nullable    = false

}

variable "bucket_name_composer" {
  type        = string
  description = "Nome do bucket main do composer"
  nullable    = false

}

variable "labels" {
  type        = map(string)
  description = "Dicionário com as labels"
  nullable    = true
}

variable "env_variables" {
  type        = map(string)
  description = "Dicionário com as váriaveis de ambiente"
  default     = null
  nullable    = true
}

variable "airflow_config_overrides" {
  description = "Triggerer configuration"
  type = object({
    dags_are_paused_at_creation        = optional(string)
    parallelism                        = optional(string)
    max_active_tasks_per_dag           = optional(string)
    metrics_use_pattern_match          = optional(string)
    worker_concurrency                 = optional(string)
    worker_autoscale                   = optional(string)
  })
  default = {
    dags_are_paused_at_creation        = "True"
    parallelism                        = 32
    max_active_tasks_per_dag           = 32
    metrics_use_pattern_match          = "True"
    worker_concurrency                 = "16"
    worker_autoscale                   = "16,8"
  }
}

variable "pypi_packages" {
  description = "Pacotes python"
  type = map(string)
  nullable = true
}

variable "environment_size" {
  type        = string
  description = "Tamanho do ambiente composer"
  default     = "ENVIRONMENT_SIZE_SMALL"
  nullable    = false
}

variable "scheduler_config" {
  description = "Scheduler configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    storage_gb = number
    count      = number
  })
  default = {
    cpu        = 0.5
    memory_gb  = 2
    storage_gb = 1
    count      = 1
  }
}

variable "web_server_config" {
  description = "Web server configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    storage_gb = number
  })
  default = {
    cpu        = 0.5
    memory_gb  = 2
    storage_gb = 1
  }
}

variable "worker_config" {
  description = "Worker configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    storage_gb = number
    min_count  = number
    max_count  = number
  })
  default = {
    cpu        = 0.5
    memory_gb  = 2
    storage_gb = 1
    min_count  = 1
    max_count  = 3
  }
}

variable "triggerer_config" {
  description = "Triggerer configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    count      = number
  })
  default = {
    cpu        = 0.5
    memory_gb  = 0.5
    count      = 1
  }
}

variable "dataplex_data_lineage" {
  type        = bool
  description = "Ativa o integração de data lineage"
  default = false
}

