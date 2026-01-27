# PRD: Infrastructure Foundation

**Status:** Complete
**Author:**
**Date:** 2026-01-27

## Problem

We need a development environment that mirrors production Kubernetes deployments. This serves two purposes:

1. Learn and practice with Rancher, Istio, Flux, and Terraform in a realistic setting
2. Establish CI/CD patterns that work identically for local development and AWS deployment

Without this foundation, we risk building an application that's difficult to deploy or operates differently across environments.

## Goals

- Reproducible Kubernetes environment that can run locally or on AWS
- GitOps workflow using Flux for all deployments
- Infrastructure as Code using Terraform
- Rancher for cluster management (matching work environment)
- Istio service mesh for traffic management and observability
- Simple test application to validate the pipeline before building GraphWiki

## Non-Goals

- Production hardening (security, HA, backup) - will address later
- Cost optimization for AWS - focus on functionality first
- Multi-cluster federation
- Comprehensive monitoring stack (basic observability only for now)

## Requirements

### Must Have

- Terraform configuration for local Kubernetes using k3d
- Terraform configuration for AWS EKS
- Rancher installation and basic configuration
- Istio installation with basic ingress
- Flux bootstrap and repository structure
- "Hello World" application deployed via Flux
- Documentation for spinning up either environment

### Should Have

- Shared Terraform modules between local and AWS
- Basic Istio traffic routing demonstration
- Flux image automation (auto-deploy on new container image)

### Nice to Have

- Terraform workspace or similar for environment switching
- Local container registry for faster iteration
- Basic observability (Kiali, Jaeger) via Istio

## Decisions

**Local Kubernetes: k3d**
- Lightweight and fast startup
- Multi-node clusters easy to configure
- Same ecosystem as Rancher (both SUSE/Rancher projects)

**AWS: EKS with managed node groups**
- Good balance of control vs operational convenience
- AWS handles node updates and scaling
- Fargate rejected: incompatible with Istio (no DaemonSets)

**Rancher: Single cluster (Rancher on workload cluster)**
- Simpler setup for development and learning
- Fewer resources required
- Can migrate to separate management cluster later if needed

**Flux: Monorepo approach**
- Single repository for app code, infra, and deploy manifests
- Simpler coordination, atomic changes
- Appropriate for single-developer project
- Structure: `deploy/` folder for Flux manifests

## Success Criteria

- Can run `terraform apply` to create a working local K8s cluster with Rancher and Istio
- Can run `terraform apply` (different workspace/config) to create equivalent AWS infrastructure
- Pushing to the Git repo triggers Flux to deploy/update the test application
- Test application is accessible via Istio ingress
- Another developer could follow the docs and reproduce the setup
