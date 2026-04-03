## Kubernetes

### API & Structure
- Use `kubectl api-resources` to check stable API versions
- YAML only, no JSON
- One manifest per resource, organized: `k8s/base/`, `k8s/overlays/{dev,test,prod}/`
- Use Kustomize for environment variations; avoid copy-pasting manifests
- Pin image tags to immutable versions (SHA digests or semver), never `latest`

### Labels & Metadata
- Always set: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of`, `app.kubernetes.io/managed-by`
- Add `kubernetes.io/description` annotation on every resource
- Add `owner` annotation with team contact

### Resource Management
- Always set `requests` for both CPU and memory
- Always set memory `limits` (OOM-kill is the only safe guardrail)
- **Do not set CPU limits** — rely on CPU requests for scheduling and let pods burst
- Start requests at observed p95 usage; adjust via Prometheus/VPA recommendations
- Use `LimitRange` and `ResourceQuota` per namespace as cluster-level guardrails

### Security Context (every container)
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 3000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```
- Never use `privileged: true`
- Never use `hostNetwork` or `hostPort` unless building a network plugin

### Workload Controllers
- Never create naked Pods — always use Deployment, StatefulSet, or Job
- Use `PodDisruptionBudget` for anything with `replicas > 1`
- Set `topologySpreadConstraints` or pod anti-affinity for HA workloads

### Config & Secrets
- Externalize config into ConfigMaps
- Never commit plaintext Secrets to git — assume GCP Secrets Manager or Hashicorp Vault is in place
- Use `envFrom` to inject full ConfigMaps; prefer volume mounts for large configs

### Networking
- Provide an Ingress for API / UI services
- Assume TLS termination is handled by a load balancer – NEVER add any TLS annotations to the application
- Assume DNS is handled by external-dns - NEVER add any external-dns annotations to the application
