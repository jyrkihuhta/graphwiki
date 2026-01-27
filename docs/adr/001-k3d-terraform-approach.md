# ADR-001: Use k3d CLI via Terraform null_resource

**Status:** Accepted
**Date:** 2026-01-27

## Context

We needed to provision local Kubernetes clusters using k3d through Terraform for infrastructure-as-code benefits.

The Terraform Registry has several k3d providers:
- pvotal-tech/k3d
- nikhilsbhat/k3d
- SneakyBugs/k3d

Testing revealed that the pvotal-tech/k3d provider fails silently during cluster creation, even with valid configurations that work when using the k3d CLI directly.

## Decision

Use Terraform's `null_resource` with `local-exec` provisioner to invoke the k3d CLI directly, rather than using a dedicated Terraform provider.

```hcl
resource "null_resource" "k3d_cluster" {
  provisioner "local-exec" {
    command = "k3d cluster create ..."
  }
  provisioner "local-exec" {
    when    = destroy
    command = "k3d cluster delete ..."
  }
}
```

## Consequences

### Positive

- Reliable: k3d CLI is stable and well-maintained
- Full feature access: all k3d options available
- Debuggable: clear error messages from CLI
- Still IaC: reproducible, version-controlled

### Negative

- Requires k3d CLI installed on the machine running Terraform
- Less "pure" Terraform - mixing CLI tools
- Terraform state doesn't fully track cluster details

### Neutral

- Destroy still works via the `when = destroy` provisioner
- Changes to cluster config require `terraform taint` to recreate
