#!/usr/bin/env python3
"""Post-install configuration for Claude Code devcontainer.

Runs on container creation to set up:
- Global CLAUDE.md and docs (from host ~/.claude)
- Claude settings (bypassPermissions mode)
- Git config (inlined host config, global gitignore, delta, credential helper)
- Tmux configuration (200k history, mouse support)
- Directory ownership fixes for mounted volumes
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

LOG_PREFIX = "[post_install]"


def log(msg: str) -> None:
    print(f"{LOG_PREFIX} {msg}", file=sys.stderr)


def log_warn(msg: str) -> None:
    print(f"{LOG_PREFIX} Warning: {msg}", file=sys.stderr)


def log_error(msg: str) -> None:
    print(f"{LOG_PREFIX} ERROR: {msg}", file=sys.stderr)

GITIGNORE_PATTERNS = """\
# Claude Code
.claude/

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# Python
*.pyc
*.pyo
__pycache__/
*.egg-info/
.eggs/
*.egg
.venv/
venv/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
.npm/

# Editors
*.swp
*.swo
*~
.idea/
.vscode/
*.sublime-*

# Devcontainer
.devcontainer
.devc.env

# Misc
*.log
.env.local
.env.*.local
"""


def setup_claude_settings():
    """Configure Claude Code with bypassPermissions enabled."""
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    settings_file = claude_dir / "settings.json"

    # Load existing settings or start fresh
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except json.JSONDecodeError as e:
            log_warn(f"corrupt {settings_file}, resetting: {e}")

    # Set bypassPermissions mode
    if "permissions" not in settings:
        settings["permissions"] = {}
    settings["permissions"]["defaultMode"] = "bypassPermissions"

    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    log(f"Claude settings configured: {settings_file}")


def setup_tmux_config():
    """Configure tmux with 200k history, mouse support, and vi keys."""
    tmux_conf = Path.home() / ".tmux.conf"

    if tmux_conf.exists():
        log("Tmux config exists, skipping")
        return

    config = """\
# 200k line scrollback history
set-option -g history-limit 200000

# Enable mouse support
set -g mouse on

# Use vi keys in copy mode
setw -g mode-keys vi

# Start windows and panes at 1, not 0
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Faster escape time for vim
set -sg escape-time 10

# True color support
set -g default-terminal "tmux-256color"
set -ag terminal-overrides ",xterm-256color:RGB"

# Terminal features (ghostty, cursor shape in vim)
set -as terminal-features ",xterm-ghostty:RGB"
set -as terminal-features ",xterm*:RGB"
set -ga terminal-overrides ",xterm*:colors=256"
set -ga terminal-overrides '*:Ss=\\E[%p1%d q:Se=\\E[ q'

# Status bar
set -g status-style 'bg=#333333 fg=#ffffff'
set -g status-left '[#S] '
set -g status-right '%Y-%m-%d %H:%M'
"""
    tmux_conf.write_text(config, encoding="utf-8")
    log(f"Tmux configured: {tmux_conf}")


def setup_global_claude_md():
    """Copy host ~/.claude/CLAUDE.md and ~/.claude/docs into the container volume.

    The host's ~/.claude/CLAUDE.md and ~/.claude/docs are bind-mounted read-only
    to /opt/host-claude/. If present and non-empty, they are copied to ~/.claude/
    on the writable volume. If missing, nothing happens — users are expected to
    populate ~/.claude on the host.
    """
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    host_claude_md = Path("/opt/host-claude/CLAUDE.md")
    default_claude_md = Path("/opt/dotfiles/.claude/CLAUDE.md")
    target_claude_md = claude_dir / "CLAUDE.md"

    if not host_claude_md.is_file() and not default_claude_md.is_file():
        log_warn(f"No host or default CLAUDE.md found: {host_claude_md}, {default_claude_md}")
        return

    source_claude_md = host_claude_md if host_claude_md.is_file() else default_claude_md

    try:
        content = source_claude_md.read_text(encoding="utf-8").strip()
        if content:
            shutil.copy2(source_claude_md, target_claude_md)
            log(f"Global CLAUDE.md installed from {source_claude_md}")
        else:
            log(f"CLAUDE.md from {source_claude_md} is empty, using default from {default_claude_md}")
            if default_claude_md.is_file():
                shutil.copy2(default_claude_md, target_claude_md)
            else:
                log_warn(f"Default CLAUDE.md not found at {default_claude_md}")
    except OSError as e:
        log_warn(f"could not read/write CLAUDE.md: {e}")

    host_docs = Path("/opt/host-claude/docs")
    target_docs = claude_dir / "docs"

    if not host_docs.is_dir() or not any(host_docs.iterdir()):
        if target_docs.is_dir():
            shutil.rmtree(target_docs)
            log("Removed stale docs (host docs empty or missing)")
        return

    target_docs.mkdir(parents=True, exist_ok=True)
    for src_file in host_docs.rglob("*"):
        if src_file.is_symlink() or not src_file.is_file():
            continue
        rel = src_file.relative_to(host_docs)
        dest = target_docs / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_file, dest)
        except OSError as e:
            log_warn(f"failed to copy doc {rel}: {e}")
    log("Global docs installed from host")


def fix_directory_ownership():
    """Fix ownership of mounted volumes that may have root ownership."""
    uid = os.getuid()
    gid = os.getgid()

    dirs_to_fix = [
        Path.home() / ".claude",
        Path("/commandhistory"),
        Path.home() / ".config" / "gh",
    ]

    for dir_path in dirs_to_fix:
        if dir_path.exists():
            try:
                # Use sudo to fix ownership if needed
                stat_info = dir_path.stat()
                if stat_info.st_uid != uid:
                    subprocess.run(
                        ["sudo", "chown", "-R", f"{uid}:{gid}", str(dir_path)],
                        check=True,
                        capture_output=True,
                    )
                    log(f"Fixed ownership: {dir_path}")
            except (PermissionError, subprocess.CalledProcessError) as e:
                log_warn(f"Could not fix ownership of {dir_path}: {e}")


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts: dicts recurse, lists deduplicate-concatenate, scalars overwrite."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            merged = list(result[key])
            for item in val:
                if item not in merged:
                    merged.append(item)
            result[key] = merged
        else:
            result[key] = val
    return result


def setup_claude_settings_from_dotfiles():
    """Merge dotfiles settings.json into container Claude settings.

    The dotfiles settings are staged at /opt during build because ~/.claude/ is a
    Docker volume — files baked into the image layer are hidden by the volume mount.
    This function reads the staged copy and deep-merges it at runtime.
    """
    staged = Path("/opt/dotfiles/.claude/settings.json")
    if not staged.exists():
        return

    override = {}
    try:
        override = json.loads(staged.read_text())
    except json.JSONDecodeError as e:
        log_warn(f"corrupt {staged}, skipping merge: {e}")

    if not override:
        return

    settings_file = Path.home() / ".claude" / "settings.json"
    existing = {}
    if settings_file.exists():
        try:
            existing = json.loads(settings_file.read_text())
        except json.JSONDecodeError as e:
            log_warn(f"corrupt {settings_file}, starting fresh: {e}")

    merged = deep_merge(existing, override)
    settings_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    log("Claude settings merged from dotfiles")


def setup_claude_statusline():
    """Deploy statusline script from dotfiles into the volume-mounted Claude config."""
    staged = Path("/opt/dotfiles/.claude/statusline.sh")
    if not staged.exists():
        return

    target = Path.home() / ".claude" / "statusline.sh"
    try:
        target.write_bytes(staged.read_bytes())
        target.chmod(0o755)
        log(f"Claude statusline deployed: {target}")
    except OSError as e:
        log_warn(f"failed to deploy statusline: {e}")


def setup_global_gitignore():
    """Set up global gitignore and local git config.

    ~/.gitconfig is mounted read-only from host. GIT_CONFIG_GLOBAL (set in
    devcontainer.json) points git to ~/.gitconfig.local as the "global" config.
    We inline the host config into that file and append container overrides.
    """
    home = Path.home()
    gitignore = home / ".gitignore_global"
    local_gitconfig = home / ".gitconfig.local"
    host_gitconfig = home / ".gitconfig"

    gitignore.write_text(GITIGNORE_PATTERNS, encoding="utf-8")
    log(f"Global gitignore created: {gitignore}")

    try:
        host_raw = host_gitconfig.read_text(encoding="utf-8").rstrip("\n")
    except FileNotFoundError:
        host_raw = ""
    except OSError as e:
        log_warn(f"could not read {host_gitconfig}: {e}")
        host_raw = ""

    # Strip any include of .gitconfig.local — that file IS this file, so
    # including it would create a circular reference. Then remove empty [include] sections.
    host_content = re.sub(r"(?m)^\s*path\s*=\s*.*\.gitconfig\.local\s*$", "", host_raw)
    host_content = re.sub(r"(?m)^\[include\]\s*\n(?=\[|\Z)", "", host_content).strip()

    host_section = host_content + "\n\n" if host_content else ""
    # Concatenation (not f-string) because host_content may contain curly braces.
    local_config = (
        "# Container-local git config (host config + container overrides)\n\n"
        + host_section
        + "# --- Container overrides ---\n\n"
        + "[core]\n"
        + f"    excludesfile = {gitignore}\n"
        + "    pager = delta\n\n"
        + "[interactive]\n"
        + "    diffFilter = delta --color-only\n\n"
        + "[delta]\n"
        + "    navigate = true\n"
        + "    light = false\n"
        + "    line-numbers = true\n"
        + "    side-by-side = false\n\n"
        + "[merge]\n"
        + "    conflictstyle = diff3\n\n"
        + "[diff]\n"
        + "    colorMoved = default\n\n"
        + '[gpg "ssh"]\n'
        + "    program = /usr/bin/ssh-keygen\n"
    )
    local_gitconfig.write_text(local_config, encoding="utf-8")
    log(f"Local git config created: {local_gitconfig}")


def setup_gh_credential_helper():
    """Configure git to use gh as credential helper for GitHub HTTPS operations.

    Appends a credential helper block to ~/.gitconfig.local that delegates
    to `gh auth git-credential`. Works whether GH_TOKEN is set (uses the
    token) or not (falls back to ~/.config/gh/ volume auth).
    """
    local_gitconfig = Path.home() / ".gitconfig.local"
    if not local_gitconfig.exists():
        log("No .gitconfig.local found, skipping gh credential helper")
        return

    content = local_gitconfig.read_text(encoding="utf-8")
    marker = '[credential "https://github.com"]'
    if any(
        line.strip() == marker
        for line in content.splitlines()
        if not line.strip().startswith("#")
    ):
        log("gh credential helper already configured, skipping")
        return

    block = f"""
{marker}
    helper =
    helper = !/usr/bin/gh auth git-credential
"""
    local_gitconfig.write_text(content + block, encoding="utf-8")
    log(f"gh credential helper configured: {local_gitconfig}")


SIGNING_KEY_PATH = Path("/home/vscode/.ssh/signing_key")


def setup_git_signing():
    """Configure git commit and tag signing if a signing key is mounted."""
    if not SIGNING_KEY_PATH.is_file():
        log("No signing key mounted, skipping git signing setup")
        return

    local_gitconfig = Path.home() / ".gitconfig.local"
    if not local_gitconfig.exists():
        log("No .gitconfig.local found, skipping signing setup")
        return

    content = local_gitconfig.read_text(encoding="utf-8")
    if "gpg.format" in content:
        log("Git signing already configured, skipping")
        return

    block = f"""
[gpg]
    format = ssh

[user]
    signingkey = {SIGNING_KEY_PATH}

[commit]
    gpgsign = true

[tag]
    gpgsign = true
"""
    local_gitconfig.write_text(content + block, encoding="utf-8")
    log(f"Git signing configured with {SIGNING_KEY_PATH}")


def setup_codex_config():
    """Configure OpenAI Codex CLI to use Azure OpenAI endpoint.

    Reads CODEX_AZURE_BASE_URL from environment (defaulting to the seeqnc
    Azure endpoint) so the API endpoint can be changed without rebuilding
    the container.
    """
    codex_dir = Path.home() / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)

    config_file = codex_dir / "config.toml"
    if config_file.exists():
        log("Codex config exists, skipping")
        return

    base_url = os.environ.get("CODEX_AZURE_BASE_URL")
    if not base_url:
        log("CODEX_AZURE_BASE_URL not set, skipping Codex config")
        return

    if '"' in base_url or "\n" in base_url or "\\" in base_url:
        log_warn("CODEX_AZURE_BASE_URL contains invalid characters, skipping Codex config")
        return

    config = f"""\
model = "gpt-5.3-codex"
model_provider = "azure"

[model_providers.azure]
name = "Azure OpenAI"
base_url = "{base_url}"
env_key = "OPENAI_API_KEY"
wire_api = "responses"

[projects."/workspace"]
trust_level = "trusted"

[notice.model_migrations]
"gpt-5.3-codex" = "gpt-5.4"
"""
    config_file.write_text(config, encoding="utf-8")
    log(f"Codex config created: {config_file}")


def setup_exa_mcp():
    """Register Exa AI as a Claude MCP server for web search.

    Requires EXA_API_KEY to be set. Skips silently if the key is missing.
    """
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        log("EXA_API_KEY not set, skipping Exa MCP setup")
        return

    # API key is passed as a URL query parameter — visible in /proc/<pid>/cmdline
    # during registration and persisted in Claude's MCP config. This is inherent
    # to the HTTP MCP transport; acceptable risk in a single-user devcontainer.
    url = f"https://mcp.exa.ai/mcp?exaApiKey={api_key}"
    try:
        subprocess.run(
            ["claude", "mcp", "add", "--transport", "http", "exa", url],
            check=True,
            capture_output=True,
            text=True,
        )
        log("Exa MCP server registered")
    except FileNotFoundError:
        log_warn("claude CLI not found, skipping Exa MCP setup")
    except subprocess.CalledProcessError as e:
        error_detail = e.stderr.strip() if e.stderr else f"exit code {e.returncode}"
        if "already exists" in error_detail:
            log("Exa MCP server already registered, skipping")
        else:
            log_warn(f"Failed to register Exa MCP: {error_detail}")


def setup_ngrok():
    """Configure ngrok auth token if NGROK_AUTH_TOKEN is set."""
    token = os.environ.get("NGROK_AUTH_TOKEN")
    if not token:
        log("NGROK_AUTH_TOKEN not set, skipping ngrok setup")
        return

    try:
        subprocess.run(
            ["ngrok", "config", "add-authtoken", token],
            check=True,
            capture_output=True,
            text=True,
        )
        log("ngrok auth token configured")
    except FileNotFoundError:
        log_warn("ngrok not found, skipping auth token setup")
    except subprocess.CalledProcessError as e:
        error_detail = e.stderr.strip() if e.stderr else f"exit code {e.returncode}"
        log_warn(f"Failed to configure ngrok auth token: {error_detail}")


def validate_git_worktree():
    """Check if workspace is a git worktree and verify the git dir is accessible."""
    git_file = Path("/workspace/.git")
    if not git_file.exists() or git_file.is_dir():
        return

    try:
        content = git_file.read_text(encoding="utf-8").strip()
    except OSError as e:
        log_warn(f"could not read {git_file}: {e}")
        return
    if not content.startswith("gitdir:"):
        return

    gitdir_path = Path(content.split(":", 1)[1].strip())
    if gitdir_path.exists():
        log(f"Git worktree OK: {gitdir_path}")
    else:
        log_error(f"Git worktree target not found: {gitdir_path}")
        log_error("Git operations will fail. Run 'devc rebuild' to fix.")


def main():
    """Run all post-install configuration."""
    log("Starting post-install configuration...")

    setup_global_claude_md()
    setup_claude_settings()
    setup_claude_settings_from_dotfiles()
    setup_claude_statusline()
    setup_tmux_config()
    fix_directory_ownership()
    setup_global_gitignore()
    setup_gh_credential_helper()
    setup_git_signing()
    setup_codex_config()
    setup_exa_mcp()
    setup_ngrok()
    validate_git_worktree()

    log("Configuration complete!")


if __name__ == "__main__":
    main()
