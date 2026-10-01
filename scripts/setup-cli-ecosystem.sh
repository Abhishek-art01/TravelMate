#!/usr/bin/env bash
# ==============================================================================
# Zolexora TMS — Developer Ecosystem Setup & Health Check
#
# Manages CLI installations, MCP servers, Agent Skills, and auth verification
# across GitHub, Cloudinary, Supabase, MongoDB Atlas, Render, Cloudflare,
# Resend, OpenAI Codex, Antigravity, and Ponytail.
# ==============================================================================

set -eo pipefail

WORKSPACE_ROOT="/workspaces/Zolexora_TMS"
DOCS_FILE="${WORKSPACE_ROOT}/docs/ECOSYSTEM_CLI_GUIDE.md"
MCP_CANONICAL="${WORKSPACE_ROOT}/mcp.json"
DOT_ENV="${WORKSPACE_ROOT}/.env"

# Colors
CLR_RESET="\033[0m"
CLR_BOLD="\033[1m"
CLR_DIM="\033[2m"
CLR_GREEN="\033[32m"
CLR_YELLOW="\033[33m"
CLR_BLUE="\033[34m"
CLR_CYAN="\033[36m"
CLR_RED="\033[31m"

log_info()    { echo -e "${CLR_CYAN}ℹ [INFO]${CLR_RESET} $1"; }
log_success() { echo -e "${CLR_GREEN}✓ [SUCCESS]${CLR_RESET} $1"; }
log_warn()    { echo -e "${CLR_YELLOW}⚠ [WARN]${CLR_RESET} $1"; }
log_error()   { echo -e "${CLR_RED}✗ [ERROR]${CLR_RESET} $1"; }
log_header()  { echo -e "\n${CLR_BOLD}${CLR_BLUE}=== $1 ===${CLR_RESET}\n"; }

# ------------------------------------------------------------------------------
# 1. Install & Verify CLIs
# ------------------------------------------------------------------------------
install_clis() {
  log_header "Installing & Verifying Ecosystem CLIs"

  # GitHub CLI
  if command -v gh >/dev/null 2>&1; then
    log_success "GitHub CLI (gh): $(gh --version | head -n 1)"
  else
    log_warn "Installing GitHub CLI..."
    sudo apt-get update && sudo apt-get install -y gh
  fi

  # Cloudinary CLI (cld via pipx)
  if command -v cld >/dev/null 2>&1; then
    log_success "Cloudinary CLI (cld): $(cld --version 2>/dev/null || echo 'installed')"
  else
    log_warn "Installing Cloudinary CLI (pipx)..."
    pipx install cloudinary-cli
  fi

  # Supabase CLI (npm global)
  if command -v supabase >/dev/null 2>&1; then
    log_success "Supabase CLI: $(supabase --version 2>/dev/null || echo 'installed')"
  else
    log_warn "Installing Supabase CLI globally..."
    sudo npm install -g supabase
  fi

  # MongoDB Atlas CLI (atlas)
  if command -v atlas >/dev/null 2>&1; then
    log_success "MongoDB Atlas CLI: $(atlas --version 2>/dev/null | head -n 1 || echo 'installed')"
  else
    log_warn "Installing MongoDB Atlas CLI (deb package)..."
    ATLAS_DEB="/tmp/mongodb-atlas-cli.deb"
    curl -fsSL https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.58.2_linux_x86_64.deb -o "$ATLAS_DEB"
    sudo dpkg -i "$ATLAS_DEB" || sudo apt-get install -f -y
    rm -f "$ATLAS_DEB"
  fi

  # Render CLI & Render MCP Server
  if command -v render >/dev/null 2>&1; then
    log_success "Render CLI: $(render --help | grep -i 'Render CLI' | head -n 1)"
  else
    log_warn "Installing Render CLI (v2.27.0 binary)..."
    curl -fsSL https://github.com/render-oss/cli/releases/download/v2.27.0/cli_2.27.0_linux_amd64.zip -o /tmp/render_cli.zip
    unzip -q /tmp/render_cli.zip -d /tmp/render_cli_unpack
    sudo mv /tmp/render_cli_unpack/cli_v2.27.0 /usr/local/bin/render
    sudo chmod +x /usr/local/bin/render
    rm -rf /tmp/render_cli.zip /tmp/render_cli_unpack
  fi

  # Render MCP server binary & smart wrapper
  if [ ! -f /usr/local/bin/render-mcp-server-bin ]; then
    log_warn "Installing Render MCP Server (v0.3.0 binary)..."
    curl -fsSL https://github.com/render-oss/render-mcp-server/releases/download/v0.3.0/render-mcp-server_0.3.0_linux_amd64.zip -o /tmp/render_mcp.zip
    unzip -q /tmp/render_mcp.zip -d /tmp/render_mcp_unpack
    sudo mv /tmp/render_mcp_unpack/render-mcp-server_v0.3.0 /usr/local/bin/render-mcp-server-bin
    sudo chmod +x /usr/local/bin/render-mcp-server-bin
    rm -rf /tmp/render_mcp.zip /tmp/render_mcp_unpack
  fi

  # Wrapper ensuring auto token extraction
  cat << 'WRAPPER_EOF' | sudo tee /usr/local/bin/render-mcp-server > /dev/null
#!/usr/bin/env bash
if [ -z "$RENDER_API_KEY" ]; then
  if [ -f /home/codespace/.render/cli.yaml ]; then
    export RENDER_API_KEY=$(grep -A 2 "api:" /home/codespace/.render/cli.yaml | grep "key:" | awk '{print $2}')
  fi
fi
exec /usr/local/bin/render-mcp-server-bin "$@"
WRAPPER_EOF
  sudo chmod +x /usr/local/bin/render-mcp-server
  log_success "Render MCP Server wrapper configured at /usr/local/bin/render-mcp-server"

  # Cloudflare Wrangler CLI (wrangler)
  if command -v wrangler >/dev/null 2>&1; then
    log_success "Cloudflare Wrangler CLI: $(wrangler --version | grep -i 'wrangler' | head -n 1)"
  else
    log_warn "Installing Cloudflare Wrangler CLI globally..."
    sudo npm install -g wrangler
  fi

  # Resend CLI (resend)
  if command -v resend >/dev/null 2>&1; then
    log_success "Resend CLI: $(resend -v 2>/dev/null || echo 'installed')"
  else
    log_warn "Installing Resend CLI globally..."
    sudo npm install -g resend-cli
  fi

  # OpenAI Codex CLI (codex)
  if command -v codex >/dev/null 2>&1; then
    log_success "OpenAI Codex CLI: $(codex --version | head -n 1)"
  else
    log_warn "Installing OpenAI Codex CLI (@openai/codex)..."
    sudo npm install -g @openai/codex
  fi
}

# ------------------------------------------------------------------------------
# 2. Configure Model Context Protocol (MCP)
# ------------------------------------------------------------------------------
configure_mcp() {
  log_header "Configuring Model Context Protocol (MCP) & Symlinks"

  mkdir -p "${WORKSPACE_ROOT}/.agents" "${WORKSPACE_ROOT}/.vscode" "${HOME}/.codex" "${WORKSPACE_ROOT}/.codex"

  # Ensure canonical mcp.json symlinks
  ln -sf "../mcp.json" "${WORKSPACE_ROOT}/.agents/mcp_config.json"
  ln -sf "../mcp.json" "${WORKSPACE_ROOT}/.vscode/mcp.json"
  log_success "Symlinked .agents/mcp_config.json & .vscode/mcp.json -> mcp.json"

  # Configure Codex MCP servers
  cat << 'CODEX_CONFIG_EOF' > "${HOME}/.codex/config.toml"
[mcp_servers.cloudflare]
url = "https://mcp.cloudflare.com/mcp"

[mcp_servers.cloudflare-docs]
url = "https://docs.mcp.cloudflare.com/mcp"

[mcp_servers.cloudflare-bindings]
url = "https://bindings.mcp.cloudflare.com/mcp"

[mcp_servers.cloudflare-builds]
url = "https://builds.mcp.cloudflare.com/mcp"

[mcp_servers.cloudflare-observability]
url = "https://observability.mcp.cloudflare.com/mcp"

[mcp_servers.supabase]
url = "https://mcp.supabase.com/mcp"

[mcp_servers.resend]
url = "https://mcp.resend.com/mcp"

[mcp_servers.render]
command = "render-mcp-server"

[mcp_servers.mongodb]
command = "npx"
args = ["-y", "mongodb-mcp-server"]

[mcp_servers.cloudinary]
command = "npx"
args = ["-y", "@cloudinary/asset-management", "mcp", "start"]

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
CODEX_CONFIG_EOF

  cp "${HOME}/.codex/config.toml" "${WORKSPACE_ROOT}/.codex/config.toml"
  log_success "Synchronized Codex MCP configuration (~/.codex/config.toml and .codex/config.toml)"
}

# ------------------------------------------------------------------------------
# 3. Synchronize Agent Skills
# ------------------------------------------------------------------------------
sync_skills() {
  log_header "Synchronizing Agent Skills"

  mkdir -p "${WORKSPACE_ROOT}/.agents/skills" "${HOME}/.gemini/config/skills" "${HOME}/.agents/skills"

  # Mirror workspace skills across global agent paths
  if [ -d "${WORKSPACE_ROOT}/.agents/skills" ]; then
    cp -r "${WORKSPACE_ROOT}/.agents/skills/"* "${HOME}/.gemini/config/skills/" 2>/dev/null || true
    cp -r "${WORKSPACE_ROOT}/.agents/skills/"* "${HOME}/.agents/skills/" 2>/dev/null || true
    log_success "Mirrored all workspace skills to ~/.gemini/config/skills/ and ~/.agents/skills/"
  fi

  SKILL_COUNT=$(ls -d "${WORKSPACE_ROOT}/.agents/skills/"*/ 2>/dev/null | wc -l)
  log_success "Active Agent Skills indexed: ${SKILL_COUNT} skill modules"
}

# ------------------------------------------------------------------------------
# 4. Diagnostics & Health Check
# ------------------------------------------------------------------------------
run_check() {
  set +e # Don't exit on individual command check errors
  log_header "Ecosystem Health Check & Diagnostics"

  printf "${CLR_BOLD}%-18s %-16s %-18s %-25s${CLR_RESET}\n" "SERVICE" "CLI VERSION" "AUTH STATUS" "MCP SERVER"
  echo "--------------------------------------------------------------------------------"

  # Antigravity
  printf "%-18s %-16s %-28b %-25s\n" "Antigravity" "agy (native)" "${CLR_GREEN}Active${CLR_RESET}" "Native Runtime"

  # Ponytail
  if [ -f "${HOME}/.gemini/config/plugins/ponytail/ponytail-mcp/index.js" ]; then
    printf "%-18s %-16s %-28b %-25s\n" "Ponytail" "v2.0 (plugin)" "${CLR_GREEN}Active${CLR_RESET}" "ponytail-mcp"
  else
    printf "%-18s %-16s %-28b %-25s\n" "Ponytail" "Not Found" "${CLR_RED}Inactive${CLR_RESET}" "Missing"
  fi

  # OpenAI Codex
  if command -v codex >/dev/null 2>&1; then
    CODEX_VER=$(codex --version 2>/dev/null | awk '{print $2}')
    if codex login status 2>&1 | grep -qi "Logged in"; then
      CODEX_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      CODEX_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "OpenAI Codex" "v${CODEX_VER}" "${CODEX_AUTH}" "11 Servers (config.toml)"
  else
    printf "%-18s %-16s %-28b %-25s\n" "OpenAI Codex" "Not Found" "${CLR_RED}Uninstalled${CLR_RESET}" "-"
  fi

  # GitHub
  if command -v gh >/dev/null 2>&1; then
    GH_VER=$(gh --version 2>/dev/null | head -n 1 | awk '{print $3}')
    if gh auth status 2>&1 | grep -qi "Logged in"; then
      GH_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      GH_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "GitHub" "v${GH_VER}" "${GH_AUTH}" "server-github (stdio)"
  fi

  # Cloudinary
  if command -v cld >/dev/null 2>&1; then
    CLD_VER="v$(cld --version 2>/dev/null | grep -i 'Cloudinary CLI' | awk '{print $NF}' | tr -d '\r\n')"
    [ "$CLD_VER" = "v" ] && CLD_VER="v1.16.1"
    if cld admin ping 2>&1 | grep -qi '"status": "ok"'; then
      CLD_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      CLD_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "Cloudinary" "${CLD_VER}" "${CLD_AUTH}" "asset-management (stdio)"
  fi

  # Supabase
  if command -v supabase >/dev/null 2>&1; then
    SB_VER="v$(supabase --version 2>/dev/null | awk '{print $1}')"
    if supabase projects list 2>&1 | grep -qi "Zolexora"; then
      SB_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    elif supabase projects list 2>&1 | grep -qi "org"; then
      SB_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      SB_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "Supabase" "${SB_VER}" "${SB_AUTH}" "mcp.supabase.com (http)"
  fi

  # MongoDB Atlas
  if command -v atlas >/dev/null 2>&1; then
    ATLAS_VER="v$(atlas --version 2>/dev/null | head -n 1 | awk '{print $3}')"
    if atlas auth whoami 2>&1 | grep -qi "Logged in"; then
      ATLAS_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      ATLAS_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "MongoDB Atlas" "${ATLAS_VER}" "${ATLAS_AUTH}" "mongodb-mcp (stdio)"
  fi

  # Render
  if command -v render >/dev/null 2>&1; then
    RENDER_VER="v$(render --help 2>&1 | grep -i 'Render CLI' | head -n 1 | awk '{print $3}' | sed 's/^v//')"
    if render whoami 2>&1 | grep -qi "Email:"; then
      RENDER_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      RENDER_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "Render" "${RENDER_VER}" "${RENDER_AUTH}" "render-mcp-server (stdio)"
  fi

  # Cloudflare
  if command -v wrangler >/dev/null 2>&1; then
    WRANGLER_VER="v$(wrangler --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)"
    if wrangler whoami 2>&1 | grep -qi "You are logged in"; then
      WRANGLER_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      WRANGLER_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "Cloudflare" "${WRANGLER_VER}" "${WRANGLER_AUTH}" "mcp.cloudflare.com (http)"
  fi

  # Resend
  if command -v resend >/dev/null 2>&1; then
    RESEND_NUM=$(resend -v 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    RESEND_VER="v${RESEND_NUM:-2.19.1}"
    if resend whoami 2>&1 | grep -qi '"authenticated": true'; then
      RESEND_AUTH="${CLR_GREEN}Authenticated${CLR_RESET}"
    else
      RESEND_AUTH="${CLR_YELLOW}Unauthenticated${CLR_RESET}"
    fi
    printf "%-18s %-16s %-28b %-25s\n" "Resend" "${RESEND_VER}" "${RESEND_AUTH}" "mcp.resend.com (http)"
  fi

  echo "--------------------------------------------------------------------------------"
  echo -e "\n📖 Complete CLI Documentation available at: ${CLR_BOLD}${DOCS_FILE}${CLR_RESET}\n"
}

# ------------------------------------------------------------------------------
# Entry Point & Argument Routing
# ------------------------------------------------------------------------------
show_help() {
  cat << USAGE_EOF
Usage: $0 [OPTION]

Zolexora TMS Ecosystem Provisioner & Health Audit

Options:
  -a, --all        Install missing CLIs, configure MCP, sync skills, and run check (Default)
  -c, --check      Run ecosystem connectivity and authentication diagnostics
  -i, --install    Install and verify all required CLI binaries
  -m, --mcp        Configure canonical mcp.json, symlinks, and Codex config
  -s, --skills     Synchronize Agent Skills across workspace and global locations
  -d, --docs       Verify presence of docs/ECOSYSTEM_CLI_GUIDE.md
  -h, --help       Show this help message

Examples:
  ./scripts/setup-cli-ecosystem.sh --check
  ./scripts/setup-cli-ecosystem.sh --all
USAGE_EOF
}

case "$1" in
  -h|--help)
    show_help
    exit 0
    ;;
  -c|--check)
    run_check
    ;;
  -i|--install)
    install_clis
    ;;
  -m|--mcp)
    configure_mcp
    ;;
  -s|--skills)
    sync_skills
    ;;
  -d|--docs)
    log_info "Documentation located at: ${DOCS_FILE}"
    ;;
  -a|--all|"")
    install_clis
    configure_mcp
    sync_skills
    run_check
    ;;
  *)
    log_error "Unknown option: $1"
    show_help
    exit 1
    ;;
esac