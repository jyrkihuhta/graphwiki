# GraphWiki

A modern wiki and collaboration platform inspired by MoinMoin, Graphingwiki, and Obsidian.

## Project Goals

1. **Infrastructure-first development** - Production-grade Kubernetes deployment with Rancher, Istio, Flux, and Terraform
2. **Modern wiki platform** - Plaintext-first editing, wiki linking, and eventually Metatables for structured data

## Project Structure

```
graphwiki/
├── docs/
│   ├── prd/              # Product requirements documents
│   ├── adr/              # Architecture decision records
│   ├── research/         # Background research and comparisons
│   └── runbooks/         # Operational documentation
├── infra/                # Terraform configurations
├── src/                  # Application source code
├── tests/                # Test suites
└── deploy/               # Kubernetes manifests, Helm charts, Flux configs
```

## Documentation

- **PRDs** define what we're building and why
- **ADRs** capture significant technical decisions
- **Research** contains background material and comparisons
- **Runbooks** document operational procedures

## Current Phase

**Phase 1: Infrastructure** - Setting up Kubernetes deployment pipeline

See [docs/prd/001-infrastructure.md](docs/prd/001-infrastructure.md) for current work.
