output "service_url" {
  description = "Cloud Run's service URL"
  value       = google_cloud_run_v2_service.transcriber_app.uri
}

output "service_location" {
  description = "Cloud Run's service location"
  value       = google_cloud_run_v2_service.transcriber_app.location
}
