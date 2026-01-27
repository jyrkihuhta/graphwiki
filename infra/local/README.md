# Local Kubernetes (k3d)

Terraform configuration for local Kubernetes development using k3d.

> **Note:** We use `null_resource` with `local-exec` to invoke the k3d CLI rather than
> a dedicated Terraform provider, due to reliability issues with available providers.
> See [ADR-001](../../docs/adr/001-k3d-terraform-approach.md) for details.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) - k3d runs K8s in Docker containers
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [kubectl](https://kubernetes.io/docs/tasks/tools/) - for interacting with the cluster
- [k3d](https://k3d.io/) - required for cluster management

## Usage

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Create the cluster
terraform apply

# Verify cluster is running
kubectl get nodes
kubectl get pods -A
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| cluster_name | graphwiki | Name of the k3d cluster |
| servers | 1 | Control plane nodes |
| agents | 2 | Worker nodes |
| http_port | 8080 | Host port for HTTP |
| https_port | 8443 | Host port for HTTPS |

## Cluster Details

- **API Server:** https://127.0.0.1:6443
- **HTTP Ingress:** http://localhost:8080
- **HTTPS Ingress:** https://localhost:8443
- **Traefik:** Disabled (we'll use Istio instead)

## Cleanup

```bash
terraform destroy
```
