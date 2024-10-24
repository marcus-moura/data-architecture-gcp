variable "project_id" {
  type        = string
  description = "ID do Projeto onde o composer será criado"
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
}

variable "pypi_packages" {
  description = "Pacotes python"
  type = map(string)
  nullable = true
}

variable "env_variables" {
  type        = map(string)
  description = "Dicionário com as váriaveis de ambiente"
  default     = null
  nullable    = true
}

variable "environment_size" {
  type        = string
  description = "Tamanho do ambiente composer"
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
}

variable "web_server_config" {
  description = "Web server configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    storage_gb = number
  })
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
}

variable "triggerer_config" {
  description = "Triggerer configuration"
  type = object({
    cpu        = number
    memory_gb  = number
    count      = number
  })
}

variable "dataplex_data_lineage" {
  type        = bool
  description = "Ativa o integração de data lineage"
  default = false
}