# Domain: Infrastructure

**Owner:** TBD
**Status:** Complete (Phase 1)
**Language:** Terraform, YAML

## Scope

Kubernetes infrastructure and deployment:
- k3d cluster management
- Istio service mesh
- Rancher cluster UI
- Flux GitOps
- Container builds

**Not in scope:** Application code, business logic

## Current State

Infrastructure is complete:
- [x] k3d cluster (1 server, 2 agents)
- [x] Istio ingress gateway
- [x] Rancher management UI
- [x] Flux GitOps deployment
- [x] GraphWiki Kubernetes manifests

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    k3d Load Balancer                             │
│                   (localhost:8080/8443)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Istio Ingress Gateway                           │
├─────────────────────────────────────────────────────────────────┤
│  wiki.localhost:8080  →  graphwiki service                       │
│  rancher.localhost:8443  →  rancher service                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  GraphWiki  │  │   Rancher   │  │  Test App   │
│   (Pod)     │  │   (Pods)    │  │   (Pod)     │
└──────┬──────┘  └─────────────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│     PVC     │
│ (wiki data) │
└─────────────┘
```

## Project Structure

```
infra/local/
├── main.tf           # k3d cluster (null_resource + CLI)
├── istio.tf          # Istio service mesh
├── rancher.tf        # Rancher installation
├── variables.tf      # Input variables
└── outputs.tf        # Output values

deploy/
├── flux/
│   └── flux-system/
│       ├── gotk-components.yaml
│       ├── gotk-sync.yaml
│       ├── kustomization.yaml
│       └── apps.yaml
└── apps/
    ├── kustomization.yaml
    ├── test-app/
    └── graphwiki/
        ├── namespace.yaml
        ├── deployment.yaml
        ├── service.yaml
        ├── pvc.yaml
        └── virtualservice.yaml
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| k3d Terraform | `null_resource` + CLI | Provider unreliable (ADR-001) |
| Istio CRDs | `kubectl apply` via null_resource | Terraform CRD validation issues |
| Ingress | Istio (not Traefik) | Service mesh features, observability |
| GitOps | Flux | Lightweight, good Kustomize support |
| Storage | Local PVC | Simple for development |

## Common Commands

```bash
# Terraform (infrastructure)
cd infra/local && terraform apply

# Build and deploy
cd src && docker build -t graphwiki:latest .
k3d image import graphwiki:latest -c graphwiki
kubectl rollout restart deployment/graphwiki -n graphwiki

# Check deployment
kubectl get pods -n graphwiki
kubectl logs -f deployment/graphwiki -n graphwiki

# Flux (force sync)
flux reconcile kustomization apps --with-source
```

## URLs

| URL | Service |
|-----|---------|
| http://wiki.localhost:8080 | GraphWiki |
| https://rancher.localhost:8443 | Rancher |
| http://test.localhost:8080 | Test app |

Requires `/etc/hosts` entries for `*.localhost` domains.

## Future Enhancements

### Production Readiness
- [ ] External container registry (not k3d import)
- [ ] TLS certificates (cert-manager + Let's Encrypt)
- [ ] Resource limits and requests
- [ ] Horizontal pod autoscaling
- [ ] Network policies

### Multi-Environment
- [ ] Staging environment
- [ ] Production cluster (managed k8s)
- [ ] Environment-specific configs

### Backup & Recovery
- [ ] PVC backup strategy
- [ ] Disaster recovery plan

## Gotchas

1. **k3d image import required** - Local images must be imported to k3d cluster
2. **Traefik disabled** - Using Istio ingress instead
3. **Flux deploys from Git** - Local changes need commit+push (or manual kubectl apply)
4. **/etc/hosts required** - Add entries for *.localhost domains

## Integration Points

| Component | Integration |
|-----------|-------------|
| Graph engine | Will need Rust build in container |
| Observability | Istio provides metrics/tracing hooks |
| Testing | CI/CD pipeline for automated tests |
