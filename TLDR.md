# Getting started

How to get Claude Code running in a sandboxed devcontainer. The full [README](README.md) covers edge cases if you get stuck.

## 1. Install the devc CLI

You need Docker running (Docker Desktop, OrbStack, or Colima all work) and Node.js for the devcontainer CLI.

```bash
# Install the devcontainer CLI (one-time)
npm install -g @devcontainers/cli

# Clone this repo and install the devc helper
git clone https://github.com/seeqnc/claude-code-devcontainer ~/.claude-devcontainer
~/.claude-devcontainer/install.sh self-install
```

Make sure `~/.local/bin` is in your PATH. If `devc` doesn't work after install, add this to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 2. Set up a project

Go to the repo you want to work in and run:

```bash
cd ~/Projects/sandbox-seeqnc-world-domination
devc .
```

This copies the devcontainer template into `.devcontainer/` and starts the container. Done.

**When do you need `devc rebuild`?** Any time you change an environment variable (API keys, tokens), update the Dockerfile, or modify `devcontainer.json`. The container reads env vars at creation time, so changes won't take effect until you rebuild:

```bash
devc rebuild
```

Your shell history, Claude settings, and GitHub auth survive rebuilds. They live in Docker volumes.

## 3. Create a GitHub personal access token

The `GH_TOKEN` is a fine-grained PAT scoped to the repos you're working on. This means you have to generate one token per repo. This is deliberate: a scoped token limits the blast radius if something goes wrong inside the container.

### Step by step

1. Go to [https://github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)

2. Click **Generate new token**

   > ![Screenshot: Generate new token button](docs/screens/gh-pat-01-generate.png)

3. Give it a descriptive name (e.g., `claude-devcontainer`) and set an expiration

   > ![Screenshot: Token name and expiration](docs/screens/gh-pat-02-name.png)

4. Under **Repository access**, select the specific repo you'll be working on

   > ![Screenshot: Repository access selection](docs/screens/gh-pat-03-repos.png)

5. Under **Permissions**, grant the following (all need both **Read** and **Write**):

   | Permission       | Why                              |
   |------------------|----------------------------------|
   | **Contents**     | Push commits, read files         |
   | **Pull requests**| Create and edit PRs              |
   | **Issues**       | Create and comment on issues     |

   > ![Screenshot: Permission settings](docs/screens/gh-pat-04-permissions.png)

6. Click **Generate token** and copy it immediately. You won't see it again.

7. Message Oliver or someone who has admin access to the Seeqnc organization to approve your token.

## 4. Get the OpenAI API key from Azure portal

The Codex CLI uses an Azure-hosted OpenAI endpoint. You need an API key from the Azure portal.

> **Portal link:** Go to the [Azure portal](https://portal.azure.com/azureseeqnc.onmicrosoft.com), navigate to your Azure OpenAI resource, then **Keys and Endpoint**.
>
> ![Screenshot: Azure portal Keys and Endpoint page](docs/screens/azure-openai-key.png)

Copy either `KEY 1` or `KEY 2`.

You also need the Azure endpoint URL. It's on the same Keys and Endpoint page in the portal — copy the **Endpoint** value.

## 5. Export env vars and rebuild

Now that you have your tokens, navigate to the repo you are working on and fill in the `.devc.env` file. If you ran `devc .` in step 2 and have a `.devc.env.template` in `~/.claude-devcontainer/`, it was already copied as `.devc.env`. Otherwise, create one from the example:

```bash
cd $YOUR_REPO
cp ~/.claude-devcontainer/.devc.env.example .devc.env
$EDITOR .devc.env
```

Key variables:

```bash
# Required
GH_TOKEN=github_pat_...
OPENAI_API_KEY=...
CODEX_AZURE_BASE_URL=https://your-endpoint.openai.azure.com/openai/v1/

# Required — commit signing (see section 11)
GIT_SIGNING_KEY=~/.ssh/github_signing

# Optional
ANTHROPIC_API_KEY=...          # skip interactive `claude login`
CLAUDE_CODE_OAUTH_TOKEN=...    # skip onboarding wizard (see section 8)
EXA_API_KEY=...                # Exa AI search
GEMINI_API_KEY=...             # Gemini CLI for /review-pr
```

Then rebuild:

```bash
devc rebuild
```

The `.devc.env` file is gitignored and never enters the container — Claude cannot read it. If you change a key later, edit `.devc.env` and run `devc rebuild` again.

**Tip:** Create `~/.claude-devcontainer/.devc.env.template` with your keys pre-filled. On each `devc .`, it's automatically copied as `.devc.env` if one doesn't exist yet.

## 6. Ignore the dev container files

So that your local environment is more clean, you can add `.devcontainer` to your `.gitignore` file.

## 7. Start the container

```bash
devc shell
```

You're inside the devcontainer now. Your project files are mounted at `/workspace`.

## 8. Run Claude Code

First time? Log in with your subscription account:

```bash
claude login
```

This opens a browser flow. Your login persists across rebuilds (stored in a Docker volume), so you only do this once.

Alternatively, you can skip the login wizard with an OAuth token:

```bash
claude setup-token                          # run on host, one-time — prints the token
```

Add the token to `.devc.env`:

```bash
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
```

Then `devc rebuild`. On container creation, `post_install.py` runs a one-shot auth handshake so `claude` starts without the login wizard. Workaround for [#8938](https://github.com/anthropics/claude-code/issues/8938).

If you don't set a token, the interactive login flow works as before.

Normal mode, where Claude asks before running commands:

```bash
claude
```

Yolo mode, where Claude runs everything without asking:

```bash
claude-yolo
```

That's shorthand for `claude --dangerously-skip-permissions`. Sounds scary. It isn't. Keep reading.

## 9. Why yolo mode is safe here

On your actual machine, `--dangerously-skip-permissions` is exactly what it sounds like. Claude can delete files, run arbitrary commands, do whatever it wants.

Inside this devcontainer, that's fine.

Claude can only see `/workspace`. Your home directory, SSH keys, cloud credentials, and other projects don't exist in here.

The `.devcontainer/` directory is mounted read-only inside the container, so a compromised process can't modify the Dockerfile or `devcontainer.json` to inject commands that run on your host during the next rebuild. Your fine-grained PAT only has access to the repos you selected. Claude's config and shell history live in Docker volumes, not on your host filesystem.

The container is the sandbox. Yolo mode gives you unrestricted Claude that can't reach anything that matters.

In short you can yolo through your day without worrying about security. Ok don't take that too seriously.

## 10. Codex CLI and /review-pr

The container comes with [OpenAI Codex CLI](https://github.com/openai/codex) pre-installed and configured to use the Azure OpenAI endpoint. You don't need to set anything up beyond the `OPENAI_API_KEY` and `CODEX_AZURE_BASE_URL` from step 4.

When you run `/review-pr` in Claude, it uses Codex as an independent reviewer. If you also have `GEMINI_API_KEY` set, Gemini CLI adds a third opinion on the same diff.

Verify Codex is working:

```bash
which codex      # should print a path
codex --help     # should show usage
```

You can also run Codex directly from the container.

**Note:** Codex CLI is a separate product from Claude. It doesn't have the same guardrails, so be careful if you run it directly. Don't run `codex --dangerously-bypass-approvals-and-sandbox` in this container. We might implement something similar to the guardrails for Claude later for Codex if there is demand for it.

## 11. Signed commits

All commits made inside the devcontainer must be signed. Follow the steps below to create a key, register it, and configure both your host and the devcontainer.

### Create a signing key

```bash
ssh-keygen -t ed25519 -a 32 -C "your-email@seeqnc.com" -f ~/.ssh/github_signing
```

A passphrase is **required** — enter one when prompted. You can name the key anything you like.

### Register on GitHub

1. Go to [GitHub SSH keys settings](https://github.com/settings/keys)
2. Click **New SSH key**
3. Set **Key type** to **Signing Key**
4. Paste the contents of `~/.ssh/github_signing.pub` into the **Key** field
5. Give it a title you'll recognize and save

### Configure git on your host

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/github_signing.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

To avoid entering the passphrase on every commit on your **host** (macOS):

```bash
ssh-add --apple-use-keychain ~/.ssh/github_signing
```

### Point the devcontainer at your key

```bash
# In .devc.env
GIT_SIGNING_KEY=~/.ssh/github_signing
```

This key is only used for signing. Push/pull access is handled by `GH_TOKEN` via the `gh` credential helper — no SSH key needed for transport.

### How it works inside the container

1. Container starts a local ssh-agent (fixed socket at `/tmp/ssh-agent-vscode.sock`)
2. On first shell, the agent auto-loads the signing key and prompts for the passphrase
3. All subsequent `git commit` and `git tag` operations use the cached key — no more prompts
4. The agent persists across terminal sessions within the same container
5. The host's ssh-agent is never forwarded — only the mounted signing key is available

## 12. Tailscale networking (optional)

The devcontainer can join your Tailscale network via a sidecar container. This gives the container a stable hostname on your tailnet — useful for exposing dev servers, webhooks, or APIs without port forwarding.

### Setup

1. Create a [Tailscale OAuth client](https://login.tailscale.com/admin/settings/oauth) with the `devices` scope and the tag `tag:dev-container`.

2. Find the image SHA for your architecture from the [tailscale/tailscale](https://hub.docker.com/r/tailscale/tailscale/tags) Docker Hub page.

3. Add to `.devc.env`:

```bash
TS_CLIENT_ID=<your-client-id>
TS_CLIENT_SECRET=<your-client-secret>
TS_HOSTNAME=ts-devc-yourname
TS_IMAGE_SHA=sha256:<arch-specific-sha>
```

4. Run `devc rebuild`. The tailscale sidecar starts first, the devcontainer shares its network stack.

### How it works

When `TS_CLIENT_ID` and `TS_CLIENT_SECRET` are set, `devc` adds a `docker-compose.tailscale.yml` overlay that starts a Tailscale sidecar alongside the devcontainer. The devcontainer shares the sidecar's network via `network_mode: service:tailscale`.

Services listening inside the container are reachable from your tailnet at `http://<TS_HOSTNAME>:<port>`.

### Customization

| Variable | Default | Purpose |
|----------|---------|---------|
| `TS_CLIENT_ID` | (required) | Tailscale OAuth client ID |
| `TS_CLIENT_SECRET` | (required) | Tailscale OAuth client secret |
| `TS_HOSTNAME` | `ts-devc` | Device hostname on your tailnet |
| `TS_IMAGE_SHA` | (required) | Architecture-specific image digest |
| `TS_EXTRA_ARGS` | `--advertise-tags=tag:dev-container` | Additional `tailscaled` arguments |

### Without Tailscale

Comment out or remove `TS_CLIENT_ID` and `TS_CLIENT_SECRET` from `.devc.env`, then `devc rebuild`. The devcontainer runs standalone without the sidecar.

## 13. Extra packages and mounts

### Extra apt packages

Create `.devc.packages` in your project root (one package per line):

```
ffmpeg
libpq-dev
# This is a comment
```

Packages are installed during `devc rebuild` in a cached Dockerfile layer.

### Extra bind mounts

Create `.devc.mounts` in your project root (`hostPath=containerPath`, one per line):

```
~/datasets=/data
/opt/models=/models
```

Host paths must exist. `~` is expanded. Mounts are injected on `devc up`/`rebuild`.

### GPU passthrough

Set `DEVC_GPU` in `.devc.env`:

```bash
DEVC_GPU=all        # all GPUs
DEVC_GPU=2          # specific count (1-128)
```

Requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). A `docker-compose.gpu.yml` overlay is generated automatically.

## 14. Quick reference

| What                            | Command                                    |
|---------------------------------|--------------------------------------------|
| Start container                 | `devc up`                                  |
| Open shell                      | `devc shell`                               |
| Rebuild (after env changes)     | `devc rebuild`                             |
| Stop container                  | `devc down`                                |
| Run Claude                      | `claude`                                   |
| Run Claude (yolo)               | `claude-yolo`                              |
| Upgrade Claude to latest        | `devc upgrade`                             |
| Show container env vars         | `devc env`                                 |
| Mount host dir into container   | `devc mount ~/data /data`                  |
| Update devc itself              | `devc update`                              |
| Check GitHub auth               | `gh auth status`                           |
