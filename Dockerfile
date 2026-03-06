# Claude Code Devcontainer
# Based on Microsoft devcontainer image for better devcontainer integration
ARG UV_VERSION=0.10.0
FROM ghcr.io/astral-sh/uv:${UV_VERSION}@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f AS uv
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04@sha256:d94c97dd9cacf183d0a6fd12a8e87b526e9e928307674ae9c94139139c0c6eae

ARG TZ
ENV TZ="$TZ"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install additional system packages (base image already includes git, curl, sudo, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
  # Sandboxing support for Claude Code
  bubblewrap \
  socat \
  # Modern CLI tools
  bat \
  eza \
  fd-find \
  ripgrep \
  tmux \
  zsh \
  # Build tools
  build-essential \
  # Utilities
  jq \
  nano \
  unzip \
  vim \
  # Network tools (for security testing)
  dnsutils \
  ipset \
  iptables \
  iproute2 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install git-delta
ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  curl -fsSL "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" -o /tmp/git-delta.deb && \
  dpkg -i /tmp/git-delta.deb && \
  rm /tmp/git-delta.deb

# Install uv (Python package manager) via multi-stage copy
COPY --from=uv /uv /usr/local/bin/uv

# Install fzf from GitHub releases (newer than apt, includes built-in shell integration)
ARG FZF_VERSION=0.67.0
RUN ARCH=$(dpkg --print-architecture) && \
  case "${ARCH}" in \
    amd64) FZF_ARCH="linux_amd64" ;; \
    arm64) FZF_ARCH="linux_arm64" ;; \
    *) echo "Unsupported architecture: ${ARCH}" && exit 1 ;; \
  esac && \
  curl -fsSL "https://github.com/junegunn/fzf/releases/download/v${FZF_VERSION}/fzf-${FZF_VERSION}-${FZF_ARCH}.tar.gz" | tar -xz -C /usr/local/bin

# Create symlinks for Ubuntu package names -> standard names
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd && \
  ln -sf /usr/bin/batcat /usr/local/bin/bat

# Create directories and set ownership (combined for fewer layers)
RUN mkdir -p /commandhistory /workspace /home/vscode/.claude /home/vscode/.config /opt && \
  touch /commandhistory/.bash_history && \
  touch /commandhistory/.zsh_history && \
  chown -R vscode:vscode /commandhistory /workspace /home/vscode/.claude /home/vscode/.config /opt

# Set environment variables
ENV DEVCONTAINER=true
ENV SHELL=/bin/zsh

WORKDIR /workspace

# Switch to non-root user for remaining setup
USER vscode

# Set PATH early so claude, deno, and other user-installed binaries are available
ENV PATH="/home/vscode/.deno/bin:/home/vscode/.local/bin:$PATH"

# Install Claude Code natively with marketplace plugins
RUN curl -fsSL https://claude.ai/install.sh | bash && \
  claude plugin marketplace add anthropics/skills && \
  claude plugin marketplace add trailofbits/skills && \
  claude plugin marketplace add trailofbits/skills-curated && \
  claude plugin marketplace add affaan-m/everything-claude-code && \
  claude plugin install everything-claude-code@everything-claude-code

# Install Python 3.13 via uv (fast binary download, not source compilation)
RUN uv python install 3.13 --default

# Install ast-grep (AST-based code search)
RUN uv tool install ast-grep-cli

# Install fnm (Fast Node Manager) and Node 22
ARG NODE_VERSION=22
ENV FNM_DIR="/home/vscode/.fnm"
RUN curl -fsSL https://fnm.vercel.app/install | bash -s -- --install-dir "$FNM_DIR" --skip-shell && \
  export PATH="$FNM_DIR:$PATH" && \
  eval "$(fnm env)" && \
  fnm install ${NODE_VERSION} && \
  fnm default ${NODE_VERSION}

# Install starship prompt
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- --yes -b /home/vscode/.local/bin

# Install zoxide (smart cd)
RUN curl -fsSL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash

# Install lazygit
ARG LAZYGIT_VERSION=0.44.1
RUN ARCH=$(dpkg --print-architecture) && \
  case "${ARCH}" in \
    amd64) LG_ARCH="x86_64" ;; \
    arm64) LG_ARCH="arm64" ;; \
  esac && \
  curl -fsSL "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_Linux_${LG_ARCH}.tar.gz" | tar -xz -C /home/vscode/.local/bin lazygit

# Install deno
RUN curl -fsSL https://deno.land/install.sh | sh

# Install Oh My Zsh
ARG ZSH_IN_DOCKER_VERSION=1.2.1
RUN sh -c "$(curl -fsSL https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -x

# Copy dotfiles into image (selective — no macOS configs, no install.sh)
COPY --chown=vscode:vscode .dotfiles/.aliases /home/vscode/.aliases
COPY --chown=vscode:vscode .dotfiles/.exports /home/vscode/.exports
COPY --chown=vscode:vscode .dotfiles/.functions /home/vscode/.functions
COPY --chown=vscode:vscode .dotfiles/.vimrc /home/vscode/.vimrc
COPY --chown=vscode:vscode .dotfiles/starship.toml /home/vscode/.config/starship.toml
COPY --chown=vscode:vscode .dotfiles/.claude/settings.local.json /opt/dotfiles-claude-settings.local.json

# Copy shell configurations
COPY --chown=vscode:vscode .bashrc /home/vscode/.bashrc
COPY --chown=vscode:vscode .zshrc /home/vscode/.zshrc.custom

# Append custom zshrc to the main one
RUN echo 'source ~/.zshrc.custom' >> /home/vscode/.zshrc

# Copy post_install script
COPY --chown=vscode:vscode post_install.py /opt/post_install.py
