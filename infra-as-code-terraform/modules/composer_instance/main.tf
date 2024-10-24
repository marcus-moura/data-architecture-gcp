#  Attach role ServiceAgentV2Ext in service account composer
resource "google_project_iam_member" "attach_role_composer-agentv2" {
  project = var.project_id
  role    = "roles/composer.ServiceAgentV2Ext"
  member  = "serviceAccount:service-${var.project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

# terraform import module.composer_instance.google_composer_environment.cluster_config_composer projects/data-architecture-tcc/locations/us-east4/environments/tcc-composer
# Create composer instance
resource "google_composer_environment" "cluster_config_composer" {
  name   = var.composer_name
  project = var.project_id
  region = var.location
  provider = google-beta
  labels = var.labels

  storage_config {
      bucket  = var.bucket_name_composer
    }

  config {

    software_config {
        image_version = var.image_version_composer
        airflow_config_overrides = {
            core-dags_are_paused_at_creation  = var.airflow_config_overrides.dags_are_paused_at_creation
            core-parallelism                  = var.airflow_config_overrides.parallelism
            core-max_active_tasks_per_dag     = var.airflow_config_overrides.max_active_tasks_per_dag
            metrics-metrics_use_pattern_match = var.airflow_config_overrides.metrics_use_pattern_match
            celery-worker_concurrency         = var.airflow_config_overrides.worker_concurrency
            celery-worker_autoscale           = var.airflow_config_overrides.worker_autoscale
            secrets-backend                   =  "airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend"
            secrets-backend_kwargs            =  jsonencode({"project_id":"${var.project_id}","connections_prefix":"sm", "variables_prefix":"sm", "sep":"_"})
        }

        pypi_packages = var.pypi_packages

        env_variables = var.env_variables

        cloud_data_lineage_integration {
            enabled  = var.dataplex_data_lineage
        }
    }

    workloads_config {
        scheduler {
          cpu        = var.scheduler_config.cpu
          memory_gb  = var.scheduler_config.memory_gb
          storage_gb = var.scheduler_config.storage_gb
          count      = var.scheduler_config.count
        }
        web_server {
          cpu        = var.web_server_config.cpu
          memory_gb  = var.web_server_config.memory_gb
          storage_gb = var.web_server_config.storage_gb
        }

        worker {
            cpu        = var.worker_config.cpu
            memory_gb  = var.worker_config.memory_gb
            storage_gb = var.worker_config.storage_gb
            min_count  = var.worker_config.min_count
            max_count  = var.worker_config.max_count
        }
        triggerer {
            cpu        = var.triggerer_config.cpu
            memory_gb  = var.triggerer_config.memory_gb
            count      = var.triggerer_config.count
        }

    }
    environment_size = var.environment_size

    node_config {
      service_account       = "${var.sa_composer_name}@${var.project_id}.iam.gserviceaccount.com"
    }

    private_environment_config {
      enable_private_endpoint              = false
    }
  }

  depends_on = [google_project_iam_member.attach_role_composer-agentv2]
}