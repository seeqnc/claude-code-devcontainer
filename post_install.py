#!/usr/bin/env python3
"""Post-install configuration for Claude Code devcontainer.

Runs on container creation to set up:
- Global CLAUDE.md and docs (from host ~/.claude or workspace fallback)
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
            print(
                f"[post_install] Warning: corrupt {settings_file}, resetting: {e}",
                file=sys.stderr,
            )

    # Set bypassPermissions mode
    if "permissions" not in settings:
        settings["permissions"] = {}
    settings["permissions"]["defaultMode"] = "bypassPermissions"

    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(
        f"[post_install] Claude settings configured: {settings_file}", file=sys.stderr
    )


def setup_tmux_config():
    """Configure tmux with 200k history, mouse support, and vi keys."""
    tmux_conf = Path.home() / ".tmux.conf"

    if tmux_conf.exists():
        print("[post_install] Tmux config exists, skipping", file=sys.stderr)
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
    print(f"[post_install] Tmux configured: {tmux_conf}", file=sys.stderr)


def setup_global_claude_md():
    """Populate ~/.claude/CLAUDE.md and ~/.claude/docs from host or workspace fallback.

    The host's ~/.claude/CLAUDE.md and ~/.claude/docs are bind-mounted read-only
    to /opt/host-claude/ (staging). If the host file has content, it is copied to
    ~/.claude/CLAUDE.md (on the writable volume). If empty or missing, the
    workspace's .claude/CLAUDE.md is used as fallback — providing global development
    standards even when the host has no CLAUDE.md.

    Same logic applies to docs/: host docs win, workspace docs are the fallback.
    """
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    host_claude_md = Path("/opt/host-claude/CLAUDE.md")
    workspace_claude_md = Path("/workspace/.claude/CLAUDE.md")
    target_claude_md = claude_dir / "CLAUDE.md"

    # CLAUDE.md: prefer host, fall back to workspace
    source = None
    try:
        content = host_claude_md.read_text(encoding="utf-8").strip()
        if content:
            source = host_claude_md
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"[post_install] Warning: could not read {host_claude_md}: {e}",
            file=sys.stderr,
        )

    if source is None:
        try:
            content = workspace_claude_md.read_text(encoding="utf-8").strip()
            if content:
                source = workspace_claude_md
        except FileNotFoundError:
            pass
        except OSError as e:
            print(
                f"[post_install] Warning: could not read {workspace_claude_md}: {e}",
                file=sys.stderr,
            )

    if source is not None:
        try:
            shutil.copy2(source, target_claude_md)
            label = "host" if source == host_claude_md else "workspace"
            print(
                f"[post_install] Global CLAUDE.md installed from {label}: {source}",
                file=sys.stderr,
            )
        except OSError as e:
            print(
                f"[post_install] Warning: failed to copy CLAUDE.md: {e}",
                file=sys.stderr,
            )
    else:
        print(
            "[post_install] No CLAUDE.md found (checked host and workspace), skipping",
            file=sys.stderr,
        )

    # docs/: prefer host, fall back to workspace
    host_docs = Path("/opt/host-claude/docs")
    workspace_docs = Path("/workspace/.claude/docs")
    target_docs = claude_dir / "docs"

    docs_source = None
    try:
        if host_docs.is_dir() and any(host_docs.iterdir()):
            docs_source = host_docs
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"[post_install] Warning: could not read {host_docs}: {e}", file=sys.stderr
        )
    try:
        if (
            docs_source is None
            and workspace_docs.is_dir()
            and any(workspace_docs.iterdir())
        ):
            docs_source = workspace_docs
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"[post_install] Warning: could not read {workspace_docs}: {e}",
            file=sys.stderr,
        )

    if docs_source is not None:
        if target_docs.exists():
            try:
                shutil.rmtree(target_docs)
            except OSError as e:
                print(
                    f"[post_install] Warning: failed to clean docs dir: {e}",
                    file=sys.stderr,
                )
                return
        target_docs.mkdir(parents=True, exist_ok=True)
        for src_file in docs_source.rglob("*"):
            if src_file.is_symlink():
                continue
            if src_file.is_file():
                rel = src_file.relative_to(docs_source)
                dest = target_docs / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src_file, dest)
                except OSError as e:
                    print(
                        f"[post_install] Warning: failed to copy doc {rel}: {e}",
                        file=sys.stderr,
                    )
        label = "host" if docs_source == host_docs else "workspace"
        print(
            f"[post_install] Global docs installed from {label}: {docs_source}",
            file=sys.stderr,
        )


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
                    print(
                        f"[post_install] Fixed ownership: {dir_path}", file=sys.stderr
                    )
            except (PermissionError, subprocess.CalledProcessError) as e:
                print(
                    f"[post_install] Warning: Could not fix ownership of {dir_path}: {e}",
                    file=sys.stderr,
                )


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
    staged = Path("/opt/dotfiles-claude-settings.json")
    if not staged.exists():
        return

    override = {}
    try:
        override = json.loads(staged.read_text())
    except json.JSONDecodeError as e:
        print(
            f"[post_install] Warning: corrupt {staged}, skipping merge: {e}",
            file=sys.stderr,
        )

    if not override:
        return

    settings_file = Path.home() / ".claude" / "settings.json"
    existing = {}
    if settings_file.exists():
        try:
            existing = json.loads(settings_file.read_text())
        except json.JSONDecodeError as e:
            print(
                f"[post_install] Warning: corrupt {settings_file}, starting fresh: {e}",
                file=sys.stderr,
            )

    merged = deep_merge(existing, override)
    settings_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print("[post_install] Claude settings merged from dotfiles", file=sys.stderr)


def setup_claude_statusline():
    """Deploy statusline script from dotfiles into the volume-mounted Claude config."""
    staged = Path("/opt/dotfiles-claude-statusline.sh")
    if not staged.exists():
        return

    target = Path.home() / ".claude" / "statusline.sh"
    try:
        target.write_bytes(staged.read_bytes())
        target.chmod(0o755)
        print(f"[post_install] Claude statusline deployed: {target}", file=sys.stderr)
    except OSError as e:
        print(
            f"[post_install] Warning: failed to deploy statusline: {e}",
            file=sys.stderr,
        )


def setup_global_gitignore():
    """Set up global gitignore and local git config.

    Since ~/.gitconfig is mounted read-only from host, we create a local
    config file that includes the host config and adds container-specific
    settings like core.excludesfile and delta configuration.

    GIT_CONFIG_GLOBAL env var (set in devcontainer.json) points git to this
    local config as the "global" config.
    """
    home = Path.home()
    gitignore = home / ".gitignore_global"
    local_gitconfig = home / ".gitconfig.local"
    host_gitconfig = home / ".gitconfig"

    # Create global gitignore with common patterns
    patterns = """\
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
    # Preserve any patterns from .dotfiles (copied at build time)
    try:
        existing = gitignore.read_text(encoding="utf-8")
    except OSError:
        existing = ""
    if existing and "# Container defaults" not in existing:
        existing_patterns = {
            ln.strip()
            for ln in existing.splitlines()
            if ln.strip() and not ln.startswith("#")
        }
        new_patterns = [
            ln
            for ln in patterns.splitlines()
            if ln.strip()
            and not ln.startswith("#")
            and ln.strip() not in existing_patterns
        ]
        if new_patterns:
            combined = (
                existing.rstrip("\n")
                + "\n\n# Container defaults\n"
                + "\n".join(new_patterns)
                + "\n"
            )
        else:
            combined = existing
    elif not existing:
        combined = patterns
    else:
        combined = existing
    gitignore.write_text(combined, encoding="utf-8")
    print(f"[post_install] Global gitignore created: {gitignore}", file=sys.stderr)

    # Build local git config by prepending host config content, then appending
    # container-specific overrides. We avoid [include] because GIT_CONFIG_GLOBAL
    # pointing to this file + including ~/.gitconfig creates a circular include
    # (git recognizes ~/.gitconfig as the default global path and re-enters).
    try:
        host_raw = host_gitconfig.read_text(encoding="utf-8").rstrip("\n")
    except FileNotFoundError:
        host_raw = ""
    except OSError as e:
        print(
            f"[post_install] Warning: could not read host gitconfig {host_gitconfig}: {e}",
            file=sys.stderr,
        )
        host_raw = ""

    # Strip the self-referencing include of .gitconfig.local to prevent circular
    # include: host .gitconfig includes .gitconfig.local, which IS this file.
    # First remove just the path line, then clean up any empty [include] sections.
    host_content = re.sub(
        r'(?m)^\s*path\s*=\s*"?(?:~/?|(?:[./][^"]*/))?\.gitconfig\.local"?\s*$',
        "",
        host_raw,
    )
    host_content = re.sub(
        r"(?m)^\[include\]\s*\n(?=\[|\Z)",
        "",
        host_content,
    ).strip()

    # Build by concatenation — not f-string — because host_content may contain
    # curly braces (shell variables in git aliases, hook commands, etc.).
    host_section = host_content + "\n\n" if host_content else ""
    local_config = (
        f"# Container-local git config\n"
        f"# Host config (from {host_gitconfig}, mounted read-only) followed by container overrides\n\n"
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
    print(
        f"[post_install] Local git config created: {local_gitconfig}", file=sys.stderr
    )


def setup_gh_credential_helper():
    """Configure git to use gh as credential helper for GitHub HTTPS operations.

    Appends a credential helper block to ~/.gitconfig.local that delegates
    to `gh auth git-credential`. Works whether GH_TOKEN is set (uses the
    token) or not (falls back to ~/.config/gh/ volume auth).
    """
    local_gitconfig = Path.home() / ".gitconfig.local"
    if not local_gitconfig.exists():
        print(
            "[post_install] No .gitconfig.local found, skipping gh credential helper",
            file=sys.stderr,
        )
        return

    content = local_gitconfig.read_text(encoding="utf-8")
    marker = '[credential "https://github.com"]'
    if any(
        line.strip() == marker
        for line in content.splitlines()
        if not line.strip().startswith("#")
    ):
        print(
            "[post_install] gh credential helper already configured, skipping",
            file=sys.stderr,
        )
        return

    block = f"""
{marker}
    helper =
    helper = !/usr/bin/gh auth git-credential
"""
    local_gitconfig.write_text(content + block, encoding="utf-8")
    print(
        f"[post_install] gh credential helper configured: {local_gitconfig}",
        file=sys.stderr,
    )


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
        print("[post_install] Codex config exists, skipping", file=sys.stderr)
        return

    base_url = os.environ.get("CODEX_AZURE_BASE_URL")
    if not base_url:
        print(
            "[post_install] CODEX_AZURE_BASE_URL not set, skipping Codex config",
            file=sys.stderr,
        )
        return

    if '"' in base_url or "\n" in base_url or "\\" in base_url:
        print(
            "[post_install] Warning: CODEX_AZURE_BASE_URL contains invalid characters, skipping Codex config",
            file=sys.stderr,
        )
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
    print(f"[post_install] Codex config created: {config_file}", file=sys.stderr)


def setup_exa_mcp():
    """Register Exa AI as a Claude MCP server for web search.

    Requires EXA_API_KEY to be set. Skips silently if the key is missing.
    """
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        print(
            "[post_install] EXA_API_KEY not set, skipping Exa MCP setup",
            file=sys.stderr,
        )
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
        print("[post_install] Exa MCP server registered", file=sys.stderr)
    except FileNotFoundError:
        print(
            "[post_install] Warning: claude CLI not found, skipping Exa MCP setup",
            file=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        error_detail = e.stderr.strip() if e.stderr else f"exit code {e.returncode}"
        if "already exists" in error_detail:
            print(
                "[post_install] Info: Exa MCP server already registered, skipping",
                file=sys.stderr,
            )
        else:
            print(
                f"[post_install] Warning: Failed to register Exa MCP: {error_detail}",
                file=sys.stderr,
            )


def validate_git_worktree():
    """Check if workspace is a git worktree and verify the git dir is accessible."""
    git_file = Path("/workspace/.git")
    if not git_file.exists() or git_file.is_dir():
        return

    try:
        content = git_file.read_text(encoding="utf-8").strip()
    except OSError:
        return
    if not content.startswith("gitdir:"):
        return

    gitdir_path = Path(content.split(":", 1)[1].strip())
    if gitdir_path.exists():
        print(f"[post_install] Git worktree OK: {gitdir_path}", file=sys.stderr)
    else:
        print(
            f"[post_install] WARNING: Git worktree target not found: {gitdir_path}\n"
            f"[post_install] Git operations will fail. Run 'devc rebuild' to fix.",
            file=sys.stderr,
        )


def main():
    """Run all post-install configuration."""
    print("[post_install] Starting post-install configuration...", file=sys.stderr)

    setup_global_claude_md()
    setup_claude_settings()
    setup_claude_settings_from_dotfiles()
    setup_claude_statusline()
    setup_tmux_config()
    fix_directory_ownership()
    setup_global_gitignore()
    setup_gh_credential_helper()
    setup_codex_config()
    setup_exa_mcp()
    validate_git_worktree()

    print("[post_install] Configuration complete!", file=sys.stderr)


if __name__ == "__main__":
    main()
