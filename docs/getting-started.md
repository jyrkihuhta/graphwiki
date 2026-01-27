# Getting Started

This guide covers setting up GraphWiki for local development and deploying to Kubernetes.

## Prerequisites

Install these tools:

- [Docker](https://docs.docker.com/get-docker/) - Container runtime
- [k3d](https://k3d.io/) - Local Kubernetes in Docker
- [kubectl](https://kubernetes.io/docs/tasks/tools/) - Kubernetes CLI
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [Flux CLI](https://fluxcd.io/flux/installation/) - GitOps toolkit
- [Python](https://www.python.org/) >= 3.12 - For local development
- [uv](https://github.com/astral-sh/uv) (optional) - Fast Python package manager

## Quick Start (Local Development)

Run GraphWiki directly without Kubernetes:

```bash
# Clone the repository
git clone https://github.com/jyrkihuhta/graphwiki.git
cd graphwiki

# Install dependencies
cd src
pip install -e .
# Or with uv: uv pip install -e .

# Create data directory
mkdir -p data/pages

# Run the application
uvicorn graphwiki.main:app --reload --host 0.0.0.0 --port 8000
```

Access at http://localhost:8000

## Full Kubernetes Deployment

### Step 1: Create k3d Cluster

```bash
cd infra/local

# Initialize Terraform
terraform init

# Create cluster with Rancher and Istio
terraform apply
```

This creates:
- k3d cluster with 1 server + 2 agents
- Istio service mesh
- Rancher cluster management
- cert-manager for TLS

Wait for all pods to be ready:

```bash
kubectl get pods -A
```

### Step 2: Configure /etc/hosts

Add these entries to `/etc/hosts`:

```
127.0.0.1 rancher.localhost
127.0.0.1 wiki.localhost
127.0.0.1 test.localhost
```

### Step 3: Bootstrap Flux

Set up GitOps with your GitHub repository:

```bash
# Export GitHub token
export GITHUB_TOKEN=<your-token>

# Bootstrap Flux
flux bootstrap github \
  --owner=<your-github-username> \
  --repository=graphwiki \
  --branch=main \
  --path=deploy/flux \
  --personal
```

Flux will now automatically deploy applications from `deploy/apps/`.

### Step 4: Build and Deploy GraphWiki

```bash
# Build Docker image
cd src
docker build -t graphwiki:latest .

# Import to k3d cluster
k3d image import graphwiki:latest -c graphwiki

# Restart deployment to pick up new image
kubectl rollout restart deployment/graphwiki -n graphwiki

# Watch rollout
kubectl rollout status deployment/graphwiki -n graphwiki
```

### Step 5: Verify

- **GraphWiki:** http://wiki.localhost:8080
- **Rancher:** https://rancher.localhost:8443
- **Test App:** http://test.localhost:8080

## Development Workflow

### Making Code Changes

1. Edit code in `src/graphwiki/`
2. For local development: uvicorn auto-reloads
3. For k8s deployment:

```bash
# Rebuild and redeploy
cd src && docker build -t graphwiki:latest . && \
k3d image import graphwiki:latest -c graphwiki && \
kubectl rollout restart deployment/graphwiki -n graphwiki
```

### Making Kubernetes Changes

1. Edit manifests in `deploy/apps/graphwiki/`
2. Commit and push to GitHub
3. Flux automatically applies changes (within ~1 minute)

Or apply manually:

```bash
kubectl apply -k deploy/apps/graphwiki/
```

### Viewing Logs

```bash
# GraphWiki logs
kubectl logs -f deployment/graphwiki -n graphwiki

# Istio ingress logs
kubectl logs -f deployment/istio-ingress -n istio-ingress

# Flux logs
kubectl logs -f deployment/source-controller -n flux-system
```

## Troubleshooting

### Cluster Won't Start

```bash
# Check Docker is running
docker ps

# Delete and recreate cluster
k3d cluster delete graphwiki
terraform apply
```

### Can't Access Services

1. Check pods are running:
   ```bash
   kubectl get pods -A
   ```

2. Check Istio gateway:
   ```bash
   kubectl get gateway -A
   kubectl get virtualservice -A
   ```

3. Check k3d load balancer:
   ```bash
   docker ps | grep k3d
   ```

### Flux Not Deploying

```bash
# Check Flux status
flux get all

# Check kustomization
flux get kustomization

# Force reconciliation
flux reconcile kustomization apps --with-source
```

### Image Not Updating

```bash
# Verify image is in k3d
docker exec k3d-graphwiki-server-0 crictl images | grep graphwiki

# Force pod recreation
kubectl delete pod -l app=graphwiki -n graphwiki
```

## Cleanup

```bash
# Delete everything
cd infra/local
terraform destroy

# Or just delete the cluster
k3d cluster delete graphwiki
```

## Project Structure

```
graphwiki/
├── docs/                    # Documentation
│   ├── prd/                 # Product requirements
│   ├── adr/                 # Architecture decisions
│   └── research/            # Background research
├── infra/
│   └── local/               # Terraform for k3d + Rancher + Istio
├── src/
│   ├── graphwiki/           # Python application
│   ├── pyproject.toml       # Dependencies
│   └── Dockerfile           # Container build
├── deploy/
│   ├── flux/                # Flux GitOps configuration
│   └── apps/                # Application manifests
│       ├── graphwiki/       # GraphWiki k8s resources
│       └── test-app/        # Test application
├── data/
│   └── pages/               # Wiki content (gitignored)
└── tests/                   # Test suites
```

## Next Steps

- Read the [Architecture](architecture.md) document for system design details
- Check [PRD-002](prd/002-graphwiki-mvp.md) for feature status
- Explore [Graphingwiki features](research/graphingwiki-features.md) for future plans
