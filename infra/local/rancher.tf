# Rancher installation
# Requires: cert-manager for TLS certificate management

# -----------------------------------------------------------------------------
# cert-manager (Rancher dependency)
# -----------------------------------------------------------------------------

resource "helm_release" "cert_manager" {
  depends_on = [null_resource.kubeconfig]

  name             = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = var.cert_manager_version

  set {
    name  = "installCRDs"
    value = "true"
  }

  wait = true
}

# Wait for cert-manager webhook to be ready
resource "time_sleep" "wait_for_cert_manager" {
  depends_on      = [helm_release.cert_manager]
  create_duration = "30s"
}

# -----------------------------------------------------------------------------
# Rancher
# -----------------------------------------------------------------------------

resource "helm_release" "rancher" {
  depends_on = [time_sleep.wait_for_cert_manager]

  name             = "rancher"
  namespace        = "cattle-system"
  create_namespace = true
  repository       = "https://releases.rancher.com/server-charts/latest"
  chart            = "rancher"
  version          = var.rancher_version

  set {
    name  = "hostname"
    value = var.rancher_hostname
  }

  set {
    name  = "bootstrapPassword"
    value = var.rancher_bootstrap_password
  }

  set {
    name  = "replicas"
    value = "1"
  }

  # For local development, use Rancher's self-signed certs
  set {
    name  = "ingress.tls.source"
    value = "rancher"
  }

  wait    = true
  timeout = 600
}
