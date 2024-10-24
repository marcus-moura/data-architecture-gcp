provider "google" {
  # credentials = file("path_sa") # Descomentar caso precise utilizar sa json
  project     = var.project_id
  region      = var.location
}

data "google_project" "project" {
  project_id = var.project_id
}

# Define váriveis locais
locals {
  project_number                 = data.google_project.project.number
  url_gcf                        = "https://${var.location}-${var.project_id}.cloudfunctions.net"
}

# Cria a instância do composer
module "composer_instance" {
  source                      = "../modules/composer_instance"

  project_id                  = var.project_id
  project_number              = local.project_number
  location                    = var.location
  image_version_composer      = var.image_version_composer
  composer_name               = var.composer_name
  sa_composer_name            = var.sa_composer_name
  bucket_name_composer        = var.bucket_name_composer
  environment_size            = var.environment_size
  labels                      = var.labels
  scheduler_config            = var.scheduler_config
  web_server_config           = var.web_server_config
  worker_config               = var.worker_config
  triggerer_config            = var.triggerer_config
  airflow_config_overrides    = var.airflow_config_overrides
  pypi_packages               = var.pypi_packages
  env_variables               = {
          PROJECT                       = var.project_id
          LOCATION                      = var.location
          URL_BASE_GCF                  = local.url_gcf
      }
}
