ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

# =============================================================================
# Stage 1 — Clone and build the mermaid-live-editor SvelteKit static site
# Node 22 is required (package.json engines: >=20.19.0)
# =============================================================================
FROM node:22-alpine AS builder

WORKDIR /build

RUN apk add --no-cache git

# Shallow clone — no history needed for a build
RUN git clone --depth 1 https://github.com/mermaid-js/mermaid-live-editor.git .

RUN corepack enable && \
    corepack prepare pnpm@10.10.0 --activate

# Patch svelte.config.js to use relative asset paths.
# Required for HA ingress: ingress proxies through /api/hassio_ingress/{token}/
# SvelteKit's default absolute paths (/_app/chunk.js) break under any path prefix.
# paths.relative = true emits relative URLs (../../_app/...) that resolve correctly
# regardless of what base path HA's ingress proxy introduces.
RUN sed -i 's/kit: {/kit: {\n    paths: { relative: true },/' svelte.config.js

# HUSKY=0 — skip git hooks (not applicable in Docker)
RUN HUSKY=0 pnpm install --frozen-lockfile

# Build static site → output to docs/
RUN pnpm build

# =============================================================================
# Stage 2 — Serve with nginx:alpine
#
# We do NOT use the HA base image here. The HA base image runs s6-overlay as
# its init system and requires PID 1 ownership. Inside HA Supervisor's container
# runtime this causes:
#   s6-overlay-suexec: fatal: can only run as pid 1
# nginx:alpine has no init system — nginx runs directly as PID 1, which is
# exactly what a static file server needs. It is also multi-arch (amd64,
# arm64, arm/v7) so it works on all HA hardware.
# =============================================================================
FROM nginx:alpine

# Copy built static files
COPY --from=builder /build/docs /usr/share/nginx/html

# Our nginx config: port 8099, SPA fallback to 404.html, caching, security headers
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8099

# nginx:alpine default CMD is ["nginx", "-g", "daemon off;"] — no override needed
