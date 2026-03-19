ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

# =============================================================================
# Stage 1 — Clone and build the mermaid-live-editor SvelteKit static site
# Node 22 is required (package.json engines: >=20.19.0)
# No Java, no other runtimes needed — pure JavaScript/TypeScript build
# =============================================================================
FROM node:22-alpine AS builder

WORKDIR /build

# Install git for cloning
RUN apk add --no-cache git

# Clone the official mermaid-live-editor source
# Using --depth 1 for a fast, shallow clone (no history needed for a build)
RUN git clone --depth 1 https://github.com/mermaid-js/mermaid-live-editor.git .

# Activate corepack and prepare the exact pnpm version specified in package.json
# (packageManager: pnpm@10.10.0)
RUN corepack enable && \
    corepack prepare pnpm@10.10.0 --activate

# Patch svelte.config.js to use relative asset paths.
#
# Why: HA ingress proxies the addon through /api/hassio_ingress/{token}/
# SvelteKit by default builds with absolute paths (/_app/chunk.js etc.).
# Absolute paths break when served under a path prefix because the browser
# requests them at the root (/_app/chunk.js) instead of through the ingress URL.
# Setting paths.relative = true makes SvelteKit emit relative URLs (../../_app/...)
# which resolve correctly regardless of what base path the proxy introduces.
RUN sed -i 's/kit: {/kit: {\n    paths: { relative: true },/' svelte.config.js

# Install all dependencies
# HUSKY=0 — disables git hooks (not applicable in Docker)
# --frozen-lockfile — ensures reproducible install from pnpm-lock.yaml
RUN HUSKY=0 pnpm install --frozen-lockfile

# Build the SvelteKit static site
# Output lands in docs/ (configured in svelte.config.js)
RUN pnpm build

# =============================================================================
# Stage 2 — Serve the static site with nginx on the HA base image
# HA base images are Alpine-based; apk is available
# =============================================================================
FROM ${BUILD_FROM}

# Install nginx
RUN apk add --no-cache nginx

# Copy the built static files from the builder stage
COPY --from=builder /build/docs /var/www/mermaid

# Copy config and startup files
COPY nginx.conf /etc/nginx/nginx.conf
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8099

CMD ["/run.sh"]
