variable "project_id" {
  description = "Project ID for the GCP project"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "notion_api_key" {
  description = "Notion API Key"
  type        = string
  sensitive   = true
}

variable "notion_title" {
  description = "Title for Notion pages created"
  type        = string
  default     = "Daily"
}

variable "notion_category" {
  description = "Category for Notion pages created"
  type        = string
  default     = "Standup"
}

variable "notion_config_json" {
  description = "Notion configuration in JSON format"
  type        = string
}

variable "app_name" {
  description = "Application name for Cloud Run service"
  type        = string
  default     = "daily-meeting-transcriber"
}

variable "repo_name" {
  description = "Artifact Registry repository name"
  type        = string
  default     = "daily-transcriber-repo"
}

