# TravelMate Ecosystem CLI & Agent Guide

This guide documents the developer ecosystem, command-line interfaces (CLIs), Model Context Protocol (MCP) integrations, and Agent Skills configured for the **TravelMate** project.

---

## 1. Quick Setup & Management

All ecosystem dependencies, MCP configurations, and Agent Skills can be provisioned and diagnosed via the unified `scripts/setup.sh` script:

```bash
# Full ecosystem provisioning (CLIs, MCP, skills sync, and diagnostics)
./scripts/setup.sh --all

# Health check & authentication status diagnostics
./scripts/setup.sh --check

# Re-generate canonical mcp.json and sync Codex/Antigravity/VS Code configs
./scripts/setup.sh --mcp

# Synchronize agent skills across project and global agent directories
./scripts/setup.sh --skills

# Install missing CLI binaries
./scripts/setup.sh --install
```

---

## 2. Core CLIs

| Tool | CLI Binary | Package / Source | Purpose |
| :--- | :--- | :--- | :--- |
| **Firebase** | `firebase` | `firebase-tools` (npm) | Project provisioning, auth, emulators, rules, FCM |
| **Agent Skills** | `skills` | `skills` (npm / skills.sh) | AI agent skill discovery, install, and synchronization |
| **GitHub** | `gh` | `gh` (apt) | GitHub PRs, issues, actions, and repo management |
| **Supabase** | `supabase` | `supabase` (npm) | Postgres schema, migrations, JWKS auth, storage |
| **MongoDB Atlas**| `atlas` | `mongodb-atlas-cli` (deb) | Atlas clusters, search indexes, database users |
| **Render** | `render` | `cli_linux_amd64` (binary) | Web service deployments, worker environments, logs |
| **Cloudflare** | `wrangler` | `wrangler` (npm) | Workers, Pages, CDN routing, KV, R2 storage |
| **Resend** | `resend` | `resend-cli` (npm) | Transactional email delivery, templates, domain keys |
| **Cloudinary** | `cld` | `cloudinary-cli` (pipx) | Media uploads, transformations, dynamic assets |
| **OpenAI Codex** | `codex` | `@openai/codex` (npm) | Codex agent CLI and terminal execution |
| **Bitwarden** | `bw` | `@bitwarden/cli` (npm) | Secret vault retrieval and secure credentials |
| **dotenvx** | `dotenvx` | `@dotenvx/dotenvx` (npm) | Encrypted environment variables (`.env.keys`) |
| **Antigravity** | `agy` | Native agent runtime | Primary agent IDE and terminal assistant |

---

## 3. Model Context Protocol (MCP) Architecture

TravelMate uses a **single source of truth** architecture for MCP configurations.

### Configuration Hierarchy
* **Canonical Root**: `mcp.json` at repository root.
* **Antigravity Workspace**: `.agents/mcp_config.json` -> Symlinked to `../mcp.json`.
* **Antigravity Global**: `~/.gemini/config/mcp_config.json` -> Synchronized copy.
* **VS Code / Cursor / Cline**: `.vscode/mcp.json` -> Symlinked to `../mcp.json`.
* **OpenAI Codex**: `~/.codex/config.toml` & `.codex/config.toml` -> Synchronized TOML format.

### Configured MCP Servers

| Server Name | Transport | Command / Endpoint | Description |
| :--- | :--- | :--- | :--- |
| `firebase` | stdio | `npx -y firebase-mcp-server` | Firestore, Auth, Storage, and service account bridge |
| `github` | stdio | `npx -y @modelcontextprotocol/server-github` | Repository inspection, PR reviews, issue management |
| `supabase` | sse / http | `https://mcp.supabase.com/mcp` | Remote Supabase project management and SQL queries |
| `cloudflare` | sse / http | `https://mcp.cloudflare.com/mcp` | Cloudflare infrastructure management |
| `cloudflare-docs` | sse / http | `https://docs.mcp.cloudflare.com/mcp` | Live Cloudflare technical documentation |
| `cloudflare-bindings` | sse / http | `https://bindings.mcp.cloudflare.com/mcp` | Worker bindings and resources |
| `cloudflare-builds` | sse / http | `https://builds.mcp.cloudflare.com/mcp` | Cloudflare Pages and Workers CI/CD builds |
| `cloudflare-observability` | sse / http | `https://observability.mcp.cloudflare.com/mcp` | Analytics, logs, and telemetry |
| `resend` | sse / http | `https://mcp.resend.com/mcp` | Email sending, templates, and analytics |
| `render` | stdio | `render-mcp-server` | Service logs, environment sync, and deploys |
| `mongodb` | stdio | `npx -y mongodb-mcp-server` | Atlas clusters, collections, queries, and aggregations |
| `cloudinary` | stdio | `npx -y @cloudinary/asset-management mcp start` | Media management, uploads, asset searching |
| `ponytail` | stdio | `node ~/.gemini/config/plugins/ponytail/ponytail-mcp/index.js` | Anti-overengineering review and code simplification |

---

## 4. Agent Skills Ecosystem

Agent skills provide procedural runbooks and specialized domain expertise directly to Antigravity and compatible AI coding agents.

### Installed Skills
Skills are located in `.agents/skills/` and mirrored to `~/.gemini/config/skills/` and `~/.agents/skills/`:

* `firebase-basics`: CLI setup, login, project switching, and configuration files.
* `firebase-auth-basics`: Authentication schemes, token handling, and security rules.
* `firebase-firestore`: Firestore queries, composite indexes, and data modeling.
* `firebase-crashlytics`: Crashlytics initialization, error logging, and stack traces.
* `firebase-security-rules-auditor`: Security audit rules for Firestore and Storage.
* `firebase-remote-config-basics`: Remote config templates, feature flags, and defaults.
* `firebase-app-hosting-basics`: App hosting and server-side rendering configurations.
* `firebase-data-connect`: Relational SQL data connect integration with PostgreSQL.
* `extension-to-functions-codebase`: Migration and conversion for Firebase Extensions.
* `firestore-rules-creation`: Production-grade Firestore security rules design.
* `xcode-project-setup`: iOS Swift packages and CocoaPods setup for Firebase SDK.

### Managing Skills with `skills` CLI

```bash
# Search public skills directory
skills find <keyword>

# Add a skill from GitHub or skills.sh
skills add <owner/repo@skill> -y

# List active project skills
skills list

# List active global skills
skills list -g

# Update installed skills
skills update
```

---

## 5. Firebase Setup & Authentication

### CLI Login
```bash
# Standard interactive login
firebase login

# Remote/headless environment (Codespaces/SSH)
firebase login --no-localhost
```

### Service Account Credentials
For backend workers, FCM push notifications, and the Firebase MCP server, service account credentials can be supplied via:
1. Environment variables: `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, and `FIREBASE_PRIVATE_KEY` in `.env`.
2. Local service account JSON: `.firebase/service-account.json`.
3. Standard Google environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`.
