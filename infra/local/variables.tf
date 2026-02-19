variable "cluster_name" {
  description = "Name of the k3d cluster"
  type        = string
  default     = "meshwiki"
}

variable "servers" {
  description = "Number of server (control plane) nodes"
  type        = number
  default     = 1
}

variable "agents" {
  description = "Number of agent (worker) nodes"
  type        = number
  default     = 2
}

variable "http_port" {
  description = "Host port for HTTP ingress"
  type        = number
  default     = 8080
}

variable "https_port" {
  description = "Host port for HTTPS ingress"
  type        = number
  default     = 8443
}

variable "k3s_image" {
  description = "K3s image to use"
  type        = string
  default     = "docker.io/rancher/k3s:v1.33.6-k3s1"
}

# -----------------------------------------------------------------------------
# Rancher
# -----------------------------------------------------------------------------

variable "cert_manager_version" {
  description = "cert-manager Helm chart version"
  type        = string
  default     = "v1.17.2"
}

variable "rancher_version" {
  description = "Rancher Helm chart version"
  type        = string
  default     = "2.13.1"
}

variable "rancher_hostname" {
  description = "Hostname for Rancher UI"
  type        = string
  default     = "rancher.localhost"
}

variable "rancher_bootstrap_password" {
  description = "Initial admin password for Rancher"
  type        = string
  default     = "admin"
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Istio
# -----------------------------------------------------------------------------

variable "istio_version" {
  description = "Istio Helm chart version"
  type        = string
  default     = "1.24.2"
}
