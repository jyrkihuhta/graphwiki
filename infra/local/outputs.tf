output "cluster_name" {
  description = "Name of the k3d cluster"
  value       = var.cluster_name
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "k3d kubeconfig get ${var.cluster_name}"
}

output "api_endpoint" {
  description = "Kubernetes API endpoint"
  value       = "https://127.0.0.1:6443"
}

output "http_endpoint" {
  description = "HTTP ingress endpoint"
  value       = "http://localhost:${var.http_port}"
}

output "https_endpoint" {
  description = "HTTPS ingress endpoint"
  value       = "https://localhost:${var.https_port}"
}

output "rancher_url" {
  description = "Rancher UI URL (after adding /etc/hosts entry)"
  value       = "https://${var.rancher_hostname}:${var.https_port}"
}

output "rancher_setup_instructions" {
  description = "Instructions to access Rancher"
  value       = <<-EOT
    1. Add to /etc/hosts: 127.0.0.1 ${var.rancher_hostname}
    2. Open: https://${var.rancher_hostname}:${var.https_port}
    3. Login with username: admin, password: admin
    4. Accept the self-signed certificate warning in your browser
  EOT
}
