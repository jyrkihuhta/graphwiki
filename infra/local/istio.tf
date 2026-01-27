# Istio service mesh installation
# Provides: ingress gateway, traffic management, observability

# -----------------------------------------------------------------------------
# Istio Base (CRDs and cluster-wide resources)
# -----------------------------------------------------------------------------

resource "helm_release" "istio_base" {
  depends_on = [null_resource.kubeconfig]

  name             = "istio-base"
  namespace        = "istio-system"
  create_namespace = true
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "base"
  version          = var.istio_version

  wait = true
}

# -----------------------------------------------------------------------------
# Istiod (control plane)
# -----------------------------------------------------------------------------

resource "helm_release" "istiod" {
  depends_on = [helm_release.istio_base]

  name       = "istiod"
  namespace  = "istio-system"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  version    = var.istio_version

  wait = true
}

# -----------------------------------------------------------------------------
# Istio Ingress Gateway
# -----------------------------------------------------------------------------

resource "helm_release" "istio_ingress" {
  depends_on = [helm_release.istiod]

  name       = "istio-ingress"
  namespace  = "istio-system"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  version    = var.istio_version

  # Use DaemonSet with fixed NodePorts for k3d compatibility
  # k3d loadbalancer is configured to route to these NodePorts
  values = [<<-EOT
    kind: DaemonSet
    autoscaling:
      enabled: false
    service:
      type: NodePort
      ports:
      - name: status-port
        port: 15021
        protocol: TCP
        targetPort: 15021
        nodePort: 31021
      - name: http2
        port: 80
        protocol: TCP
        targetPort: 80
        nodePort: 30080
      - name: https
        port: 443
        protocol: TCP
        targetPort: 443
        nodePort: 30443
  EOT
  ]

  wait = true
}

# Configure k3d loadbalancer to route to Istio NodePorts
resource "null_resource" "k3d_loadbalancer_config" {
  depends_on = [helm_release.istio_ingress]

  provisioner "local-exec" {
    command = <<-EOT
      docker exec k3d-${var.cluster_name}-serverlb sh -c 'cat > /etc/nginx/nginx.conf << "NGINX_CONF"
error_log stderr notice;
worker_processes auto;
events {
  multi_accept on;
  use epoll;
  worker_connections 1024;
}
stream {
  upstream https_tcp {
    server k3d-${var.cluster_name}-agent-0:30443 max_fails=1 fail_timeout=10s;
    server k3d-${var.cluster_name}-agent-1:30443 max_fails=1 fail_timeout=10s;
    server k3d-${var.cluster_name}-server-0:30443 max_fails=1 fail_timeout=10s;
  }
  server {
    listen 443;
    proxy_pass https_tcp;
    proxy_timeout 600;
    proxy_connect_timeout 2s;
  }
  upstream http_tcp {
    server k3d-${var.cluster_name}-agent-0:30080 max_fails=1 fail_timeout=10s;
    server k3d-${var.cluster_name}-agent-1:30080 max_fails=1 fail_timeout=10s;
    server k3d-${var.cluster_name}-server-0:30080 max_fails=1 fail_timeout=10s;
  }
  server {
    listen 80;
    proxy_pass http_tcp;
    proxy_timeout 600;
    proxy_connect_timeout 2s;
  }
  upstream kube_api {
    server k3d-${var.cluster_name}-server-0:6443 max_fails=1 fail_timeout=10s;
  }
  server {
    listen 6443;
    proxy_pass kube_api;
    proxy_timeout 600;
    proxy_connect_timeout 2s;
  }
}
NGINX_CONF
nginx -s reload'
    EOT
  }
}

# -----------------------------------------------------------------------------
# Gateway and VirtualService for Rancher (applied via kubectl)
# -----------------------------------------------------------------------------

resource "null_resource" "istio_rancher_routing" {
  depends_on = [helm_release.istio_ingress, helm_release.rancher]

  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -f - <<EOF
      apiVersion: networking.istio.io/v1beta1
      kind: Gateway
      metadata:
        name: main-gateway
        namespace: istio-system
      spec:
        selector:
          istio: ingress
        servers:
        - port:
            number: 80
            name: http
            protocol: HTTP
          hosts:
          - "*"
        - port:
            number: 443
            name: https
            protocol: HTTPS
          hosts:
          - "*"
          tls:
            mode: PASSTHROUGH
      ---
      apiVersion: networking.istio.io/v1beta1
      kind: VirtualService
      metadata:
        name: rancher
        namespace: cattle-system
      spec:
        hosts:
        - "${var.rancher_hostname}"
        gateways:
        - istio-system/main-gateway
        tls:
        - match:
          - port: 443
            sniHosts:
            - "${var.rancher_hostname}"
          route:
          - destination:
              host: rancher.cattle-system.svc.cluster.local
              port:
                number: 443
      EOF
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete gateway main-gateway -n istio-system --ignore-not-found && kubectl delete virtualservice rancher -n cattle-system --ignore-not-found"
  }
}
