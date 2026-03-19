#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Mermaid Live Editor..."
bashio::log.info "Web interface available at: http://homeassistant.local:8099"

# Run nginx in the foreground to keep the container alive
exec nginx -g "daemon off;"
