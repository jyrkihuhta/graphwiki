# PRD: Infrastructure Foundation

**Status:** Draft
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

- Terraform configuration for local Kubernetes (k3d or kind)
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

## Open Questions

- Local K8s: k3d vs kind vs minikube? (k3d is lightweight and works well with Rancher)
- AWS: EKS managed node groups vs self-managed vs Fargate?
- Rancher: Install on the cluster or separate management cluster?
- Do we need a separate Flux repo or monorepo approach?

## Success Criteria

- Can run `terraform apply` to create a working local K8s cluster with Rancher and Istio
- Can run `terraform apply` (different workspace/config) to create equivalent AWS infrastructure
- Pushing to the Git repo triggers Flux to deploy/update the test application
- Test application is accessible via Istio ingress
- Another developer could follow the docs and reproduce the setup
