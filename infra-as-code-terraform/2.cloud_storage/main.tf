provider "google" {
  # credentials = file("path_sa") # Descomentar caso precise utilizar sa json
  project       = var.project_id
  region        = var.location
}

locals {
  bucket_name_landing = "tcc-landing"
  bucket_name_composer = "tcc-composer"
}

module "gcs_buckets" {
  source         = "terraform-google-modules/cloud-storage/google"
  version        = "~> 6.0"
  project_id     = var.project_id
  location       = var.location
  # prefixo utilizado em todos os buckets
  prefix         = "bkt"
  # lista com o nome dos buckets, o prefix será anexado à esses nomes
  names          = [
      local.bucket_name_landing,
      local.bucket_name_composer
  ]
  # pastas criadas dentro do bucket especifico
  folders = {
    "${local.bucket_name_landing}" = ["input_data", "processed_data"]
  }

  public_access_prevention = "enforced"
}