# Load .env if present — values can be overridden by environment variables
ifneq (,$(wildcard .env))
    include .env
    export
endif

IMAGE_NAME     := gnmibuddy-mcp
CONTAINER_NAME := gnmibuddy-mcp
IMAGE_TAG      := $(shell awk -F'"' '/^version/{print $$2}' pyproject.toml)
HOST_PORT      := $(or $(GNMIBUDDY_PORT),8000)

# Auto-detect container engine (Docker preferred, then Podman).
# Override explicitly with: make <target> CONTAINER_ENGINE=docker|podman
ifndef CONTAINER_ENGINE
  ifneq ($(shell command -v docker 2>/dev/null),)
    CONTAINER_ENGINE := docker
  else ifneq ($(shell command -v podman 2>/dev/null),)
    CONTAINER_ENGINE := podman
  endif
endif

.PHONY: build run stop restart logs shell clean fresh dev dev-http help

## build — build the container image (auto-detects Docker or Podman)
build:
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
	$(CONTAINER_ENGINE) build -t $(IMAGE_NAME):$(IMAGE_TAG) .

## run — start the container in detached mode (requires NETWORK_INVENTORY, mounted read-only into the container)
run:
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
ifndef NETWORK_INVENTORY
	$(error NETWORK_INVENTORY is required. Set it in .env or as: make run NETWORK_INVENTORY=/path/to/inventory.json)
endif
	$(CONTAINER_ENGINE) run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):8000 \
		-v $(abspath $(NETWORK_INVENTORY)):/app/inventory.json:ro \
		$(IMAGE_NAME):$(IMAGE_TAG)

## stop — stop and remove the running container
stop:
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
	@if $(CONTAINER_ENGINE) inspect $(CONTAINER_NAME) >/dev/null 2>&1; then \
		$(CONTAINER_ENGINE) rm -f $(CONTAINER_NAME); \
	else \
		echo "No container named $(CONTAINER_NAME) to stop."; \
	fi

## restart — stop then start the container
restart: stop run

## logs — tail the container logs
logs:
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
	$(CONTAINER_ENGINE) logs -f $(CONTAINER_NAME)

## shell — open a shell in the running container
shell:
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
	$(CONTAINER_ENGINE) exec -it $(CONTAINER_NAME) /bin/bash

## clean — stop the container and remove the image
clean: stop
ifeq ($(CONTAINER_ENGINE),)
	$(error Neither Docker nor Podman was found. Install one of them, or set CONTAINER_ENGINE=docker|podman explicitly)
endif
	@if $(CONTAINER_ENGINE) image inspect $(IMAGE_NAME):$(IMAGE_TAG) >/dev/null 2>&1; then \
		$(CONTAINER_ENGINE) rmi -f $(IMAGE_NAME):$(IMAGE_TAG); \
	else \
		echo "No image $(IMAGE_NAME):$(IMAGE_TAG) to remove."; \
	fi

## fresh — delete existing container/image, rebuild, and run (requires NETWORK_INVENTORY)
fresh: clean build run

## dev — run the MCP server locally using stdio transport (for VS Code / Claude Desktop)
dev:
	uv run gnmibuddy-mcp

## dev-http — run the MCP server locally using HTTP streamable transport
dev-http:
	GNMIBUDDY_TRANSPORT=http uv run gnmibuddy-mcp

## help — show available targets
help:
	@grep -E '^## ' Makefile | sed 's/^## /  /'
