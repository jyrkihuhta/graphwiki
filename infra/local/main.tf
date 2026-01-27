# Using null_resource + local-exec because the k3d Terraform provider
# has reliability issues. The k3d CLI is stable and well-maintained.

resource "null_resource" "k3d_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    servers      = var.servers
    agents       = var.agents
    http_port    = var.http_port
    https_port   = var.https_port
    k3s_image    = var.k3s_image
  }

  provisioner "local-exec" {
    command = <<-EOT
      k3d cluster create ${var.cluster_name} \
        --servers ${var.servers} \
        --agents ${var.agents} \
        --image ${var.k3s_image} \
        -p "${var.http_port}:80@loadbalancer" \
        -p "${var.https_port}:443@loadbalancer" \
        --k3s-arg "--disable=traefik@server:*" \
        --wait
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "k3d cluster delete ${self.triggers.cluster_name} || true"
  }
}

# Wait for cluster to be ready and get kubeconfig
resource "null_resource" "kubeconfig" {
  depends_on = [null_resource.k3d_cluster]

  provisioner "local-exec" {
    command = "k3d kubeconfig merge ${var.cluster_name} --kubeconfig-switch-context"
  }
}
