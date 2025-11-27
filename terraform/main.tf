provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "my_repo" {
  location      = var.region
  repository_id = var.repo_name
  format        = "DOCKER"
  description   = "Repo Docker pour ${var.app_name}"

  depends_on = [google_project_service.artifactregistry]
}

resource "google_cloud_run_v2_service" "transcriber_app" {
  name     = var.app_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}/${var.app_name}:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      env {
        name  = "NOTION_TOKEN"
        value = var.notion_api_key
      }
      env {
        name  = "NOTION_DB_SCHEMA"
        value = var.notion_config_json
      }
      env {
        name  = "NOTION_TITLE"
        value = var.notion_title
      }
      env {
        name  = "NOTION_CATEGORY"
        value = var.notion_category
      }

      ports {
        container_port = 8080
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
  }
}
