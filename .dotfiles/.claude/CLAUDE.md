# Global Development Standards

Global instructions for all projects. Project-specific CLAUDE.md files override these defaults.

- Prefer Exa AI (`mcp__exa__web_search_exa`) over `WebSearch` for all web searches
- Use skills proactively when they match the task — suggest relevant ones, don't block on them

## Philosophy

- **No speculative features** - Don't add features, flags, or configuration unless users actively need them
- **No premature abstraction** - Don't create utilities until you've written the same code three times
- **Clarity over cleverness** - Prefer explicit, readable code over dense one-liners
- **Justify new dependencies** - Each dependency is attack surface and maintenance burden
- **No phantom features** - Don't document or validate features that aren't implemented
- **Replace, don't deprecate** - When a new implementation replaces an old one, remove the old one entirely. No backward-compatible shims, dual config formats, or migration paths. Proactively flag dead code — it adds maintenance burden and misleads both developers and LLMs.
- **Verify at every level** - Set up automated guardrails (linters, type checkers, pre-commit hooks, tests) as the first step, not an afterthought. Prefer structure-aware tools (ast-grep, LSPs, compilers) over text pattern matching. Review your own output critically. Every layer catches what the others miss.
- **Bias toward action** - Decide and move for anything easily reversed; state your assumption so the reasoning is visible. Ask before committing to interfaces, data models, architecture, or destructive/write operations on external services.
- **Finish the job** - Don't stop at the minimum that technically satisfies the request. Handle the edge cases you can see. Clean up what you touched. If something is broken adjacent to your change, flag it. But don't invent new scope — there's a difference between thoroughness and gold-plating.
- **Agent-native by default** - Design so agents can achieve any outcome users can. Tools are atomic primitives; features are outcomes described in prompts. Prefer file-based state for transparency and portability. When adding UI capability, ask: can an agent achieve this outcome too?

## Code Quality

### Hard limits

1. ≤100 lines/function, cyclomatic complexity ≤8
2. ≤5 positional params
3. 120-char line length
4. Absolute imports only — no relative (`..`) paths
5. Google-style docstrings on non-trivial public APIs

### Zero warnings policy

Fix every warning from every tool — linters, type checkers, compilers, tests. If a warning truly can't be fixed, add an inline ignore with a justification comment. Never leave warnings unaddressed; a clean output is the baseline, not the goal.

### Comments

Code should be self-documenting. No commented-out code—delete it. If you need a comment to explain WHAT the code does, refactor the code instead.

### Error handling

- Fail fast with clear, actionable messages
- Never swallow exceptions silently
- Include context (what operation, what input, suggested fix)

### Reviewing code

Evaluate in order: architecture → code quality → tests → performance. Before reviewing, sync to latest remote (`git fetch origin`).

For each issue: describe concretely with file:line references, present options with tradeoffs when the fix isn't obvious, recommend one, and ask before proceeding.

### Testing

**Test behavior, not implementation.** Tests should verify what code does, not how. If a refactor breaks your tests but not your code, the tests were wrong.

**Test edges and errors, not just the happy path.** Empty inputs, boundaries, malformed data, missing files, network failures — bugs live in edges. Every error path the code handles should have a test that triggers it.

**Mock boundaries, not logic.** Only mock things that are slow (network, filesystem), non-deterministic (time, randomness), or external services you don't control.

**Verify tests catch failures.** Break the code, confirm the test fails, then fix. Use mutation testing (`cargo-mutants`, `mutmut`) to verify systematically. Use property-based testing (`proptest`, `hypothesis`) for parsers, serialization, and algorithms.

## Development

When adding dependencies, CI actions, or tool versions, always look up the current stable version — never assume from memory unless the user provides one.

### CLI tools

| tool | replaces | usage |
|------|----------|-------|
| `rg` (ripgrep) | grep | `rg "pattern"` - 10x faster regex search |
| `fd` | find | `fd "*.py"` - fast file finder |
| `ast-grep` | - | `ast-grep --pattern '$FUNC($$$)' --lang py` - AST-based code search |
| `shellcheck` | - | `shellcheck script.sh` - shell script linter |
| `shfmt` | - | `shfmt -i 2 -w script.sh` - shell formatter |
| `actionlint` | - | `actionlint .github/workflows/` - GitHub Actions linter |
| `zizmor` | - | `zizmor .github/workflows/` - Actions security audit |
| `prek` | pre-commit | `prek run` - fast git hooks (Rust, no Python) |
| `wt` | git worktree | `wt switch branch` - manage parallel worktrees |
| `trash` | rm | `trash file` - moves to macOS Trash (recoverable). **Never use `rm -rf`** |

Prefer `ast-grep` over ripgrep when searching for code structure (function calls, class definitions, imports, pattern matching across arguments). Use ripgrep for literal strings and log messages.

### Python

**Runtime:** 3.13 with `uv venv`

| purpose | tool |
|---------|------|
| deps & venv | `uv` |
| lint & format | `ruff check` · `ruff format` |
| static types | `ty check` |
| tests | `pytest -q` |
| api | 'FastAPI' |


**Always use uv, ruff, and ty** over pip/poetry, black/pylint/flake8, and mypy/pyright — they're faster and stricter. Configure `ty` strictness via `[tool.ty.rules]` in pyproject.toml. Use `uv_build` for pure Python, `hatchling` for extensions.

Tests in `tests/` directory mirroring package structure. Supply chain: `pip-audit` before deploying, pin exact versions (`==` not `>=`), verify hashes with `uv pip install --require-hashes`.

### Deno

**Always use Deno and Typescript for new services** unless there's a compelling reason to use Node.js.

- Runtime `deno latest`
- Frontend framework: `Fresh 2.x` **DO NOT use Fresh 1.7.x**
- Database: `PostgreSQL`
- Cache: `Redis`
- Queue: `BullMQ`
- Use builtin tools for linting and formatting.
- Use `pino` for logging.
- Use a LogContext to store request-scoped state.
- Use Deno APIs, **DO NOT use Node.js APIs**
- Use `jsr:`, `npm:`, or `https:` specifiers (no `npm install`)
- Web standard APIs (fetch, Request, Response) are available
- Top-level await is supported
- File extensions required in imports

**Imports**

- Use import maps in `deno.json`
- Prefer `jsr:` imports, use `npm:` when needed
- Always include `.ts` extension in relative imports

**Naming**

- Files: `snake_case.ts`
- Tests: `*_test.ts`
- Classes/Types: `PascalCase`
- Functions/Variables: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE`

**Logging (pino)**

```typescript
// Short event-like messages with structured context
logger.debug({ query, results, count: results.length }, 'search finished');

// Use 'err' key for exceptions (pino special handling)
logger.error({ err }, 'search failed');
```

**Formatting**
- Tabs for indentation
- Line width: 120
- Single quotes


### Node/TypeScript

**Runtime:** Node 22 LTS, ESM only (`"type": "module"`)

| purpose | tool |
|---------|------|
| lint | `oxlint` |
| format | `oxfmt` |
| test | `vitest` |
| types | `tsc --noEmit` |

**Always use oxlint and oxfmt** over eslint/prettier — they're faster and stricter. Enable `typescript`, `import`, `unicorn` plugins.

**tsconfig.json strictness** — enable all of these:
```jsonc
"strict": true,
"noUncheckedIndexedAccess": true,
"exactOptionalPropertyTypes": true,
"noImplicitOverride": true,
"noPropertyAccessFromIndexSignature": true,
"verbatimModuleSyntax": true,
"isolatedModules": true
```

Colocated `*.test.ts` files. Supply chain: `pnpm audit --audit-level=moderate` before installing, pin exact versions (no `^` or `~`), enforce 24-hour publish delay (`pnpm config set minimumReleaseAge 1440`), block postinstall scripts (`pnpm config set ignore-scripts true`).

### Bash

All scripts must start with `set -euo pipefail`. Lint: `shellcheck script.sh && shfmt -d script.sh`

### GitHub Actions

Pin actions to SHA hashes with version comments: `actions/checkout@<full-sha>  # vX.Y.Z` (use `persist-credentials: false`). Scan workflows with `zizmor` before committing. Configure Dependabot with 7-day cooldowns and grouped updates. Use `uv` ecosystem (not `pip`) for Python projects so Dependabot updates `uv.lock`.

## Architecture

- *Use latest stable API versions for all services and tools*
- Avoid deprecated APIs and features

### APIs
Always provide an OpenAPI Spec.

Key conventions:

- Every endpoint MUST have a descriptive `operationId` (verb-noun, e.g. `getTrackMetadata`) and a `description`.
- Reuse schemas via `$ref` under `components/schemas`. Never inline the same model twice.
- Include realistic `examples` on all request/response bodies.

### Configuration
- Assume `.env` file based config
- If the service supports a database or cache, support config overrides
- Always use a consistent naming scheme for environment variables and config keys

### Docker

See [DOCKER.md](./docs/DOCKER.md) for detailed Docker guidelines.
Key principles (always apply):
- Assume `docker-compose` for local development setup;
- Assume `docker buildx` for multi-arch builds;
- Always pin base images by digest, not tag (`FROM node@sha256:abc...` not `FROM node:20`)
- Always use `COPY --from=...` to avoid unnecessary layers
- Always make sure to have multi-arch support for AMD64 and ARM64

### Kubernetes

See [K8S.md](./docs/K8S.md) for detailed Kubernetes guidelines.

Key principles (always apply):
- Assume *GCP* for hyperscaler, GKE for managed Kubernetes
- Assume `kustomize` and `helm` for deployment
- Assume `argocd` for CI/CD
- Assume `traefik` for ingress

### Docker Compose
- Use `docker-compose` CLI, not `docker compose` if `docker compose` is not available
- Provide a `docker-compose.dev.yml` for local development setup
- Provide a `Grafana` `Prometheus` `Loki` setup in docker compose **production** setup
- Configure docker compose services to use `Loki` for logging in **production** setup

### CI/CD
- Assume `github-actions` for main CI/CD
- Assume `argocd` for GitOps CI/CD

### Observability
- Assume `prometheus` for monitoring
- Assume `grafana` for observability
- Assume `Google Cloud Logging` for logging, support `loki` optionally for self-hosted

## Corporate Identity / Brand Guidelines

When working on any UI, frontend, marketing material, or branded content,
read the full CI guidelines before starting:

See [CI.md](./docs/CI.md)

Key principles (always apply):
- Brand name is always lowercase: `seeqnc`
- Dark theme is the default
- Primary font: PP Neue Machina
- Accent color: seeqnc Yellow (use sparingly)

## Workflow

**Before committing:**
1. Re-read your changes for unnecessary complexity, redundant code, and unclear naming
2. Run relevant tests — not the full suite
3. Run linters and type checker — fix everything before committing

**Commits:**
- Imperative mood, ≤72 char subject line, one logical change per commit
- Never amend/rebase commits already pushed to shared branches
- Never push directly to main — use feature branches and PRs
- Never commit secrets, API keys, or credentials — use `.env` files (gitignored) and environment variables
- Never create a PR towards an upstream project

**Hooks and worktrees:**
- Install prek in every repo (`prek install`). Run `prek run` before committing. Configure auto-updates: `prek auto-update --cooldown-days 7`
- Parallel subagents require worktrees. Each subagent MUST work in its own worktree (`wt switch <branch>`), not the main repo. Never share working directories.

**Pull requests:**
Describe what the code does now — not discarded approaches, prior iterations, or alternatives. Only describe what's in the diff.

Use plain, factual language. A bug fix is a bug fix, not a "critical stability improvement." Avoid: critical, crucial, essential, significant, comprehensive, robust, elegant.
