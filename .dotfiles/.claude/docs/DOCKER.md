## Dockerfile Security

### Base Images
- Use minimal base images: Alpine, distroless, or Chainguard
  - full Ubuntu/Debian only if absolutely necessary
- Pin base images by digest, not tag (`FROM node@sha256:abc...` not `FROM node:20`)

### Build
- Use multi-stage builds — build deps in a builder stage, copy only artifacts into a minimal runtime stage
- Never put secrets in `ENV`, `ARG`, or `COPY` — use BuildKit secret mounts (`RUN --mount=type=secret,...`)
- Combine `RUN` instructions to avoid leaking removed files in earlier layers
- Maintain a strict `.dockerignore` (exclude `.env*`, `.git`, `*.pem`, `*.key`, `node_modules`, `Dockerfile*`)

### Runtime User
- Always create and switch to a non-root user (`USER appuser`) — never run as root
- Set `--chown` on `COPY` instructions for app files

### Runtime Hardening (Compose / run flags)
- `read_only: true` + explicit `tmpfs` mounts for `/tmp` with `noexec,nosuid`
- `cap_drop: [ALL]`, add back only what's needed (e.g. `NET_BIND_SERVICE`)
- `security_opt: [no-new-privileges:true]`
- Bind host ports to `127.0.0.1` unless external access is required

### Network
- Isolate services into separate Docker networks
- Use `internal: true` on backend networks that don't need internet egress
- Never use `--net=host` without justification

### Secrets
- Inject secrets at runtime via mounted files or external secret manager (Vault, GCP Secret Manager)
- For build-time secrets (e.g. private registry auth), use `RUN --mount=type=secret`
- Never mount the Docker socket (`/var/run/docker.sock`) into containers

### Supply Chain
- Generate SBOMs (`trivy image --format spdx-json`)
- Sign images with Cosign
- Pin all base image references by digest
