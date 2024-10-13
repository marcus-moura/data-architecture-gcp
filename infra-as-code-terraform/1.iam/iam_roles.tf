# Attach role in service account cloud functions
resource "google_project_iam_member" "attach_roles_sa_cloudfunctions" {
  for_each = toset(["roles/bigquery.dataEditor", "roles/bigquery.dataViewer", "roles/bigquery.jobUser", 
                    "roles/storage.admin"])
  project = var.project_id
  role  = each.key
  member  = "serviceAccount:${local.sa_prefix}-${local.sa_cloudfunctions}@${var.project_id}.iam.gserviceaccount.com"

  # Dependência da ativação das APIs e criação da Service Account
  depends_on = [module.project-services, module.service_account_with_roles]
}

# Attach role in service account composer
resource "google_project_iam_member" "attach_roles_sa_composer" {
  for_each = toset(["roles/run.invoker","roles/composer.worker",
                    "roles/bigquery.jobUser", "roles/bigquery.dataEditor", 
                    "roles/iam.serviceAccountUser","roles/dataform.editor"])
  project = var.project_id
  role  = each.key
  member  = "serviceAccount:${local.sa_prefix}-${local.sa_composer}@${var.project_id}.iam.gserviceaccount.com"

  # Dependência da ativação das APIs e criação da Service Account
  depends_on = [module.project-services, module.service_account_with_roles]
}

# Attach role in service account dataform
resource "google_project_iam_member" "attach_roles_sa_dataform" {
  for_each = toset(["roles/bigquery.dataEditor", "roles/secretmanager.secretAccessor","roles/bigquery.jobUser"])
  project = var.project_id
  role  = each.key
  member  = "serviceAccount:${local.sa_prefix}-${local.sa_composer}@${var.project_id}.iam.gserviceaccount.com"

  # Dependência da ativação das APIs e criação da Service Account
  depends_on = [module.project-services, module.service_account_with_roles]
}

# Attach role in default service account dataform
resource "google_project_iam_member" "attach_roles_default_sa_dataform" {
  for_each = toset(["roles/secretmanager.secretAccessor"])
  project = var.project_id
  role  = each.key
  member  = "serviceAccount:service-${local.project_number}@gcp-sa-dataform.iam.gserviceaccount.com"
}
# Attach role in service account github in project Data
resource "google_project_iam_member" "attach_roles_sa_github" {
  for_each = toset(["roles/bigquery.admin","roles/cloudfunctions.developer","roles/run.admin", 
                    "roles/storage.admin","roles/iam.serviceAccountAdmin",
                    "roles/iam.serviceAccountUser", "roles/composer.environmentAndStorageObjectAdmin",
                    "roles/serviceusage.serviceUsageAdmin","roles/resourcemanager.projectIamAdmin"])
  project = var.project_id
  role  = each.key
  member  = "serviceAccount:${local.sa_prefix}-${local.sa_github}@${var.project_id}.iam.gserviceaccount.com"

  # Dependência da ativação das APIs e criação da Service Account
  depends_on = [module.project-services, module.service_account_with_roles]
}