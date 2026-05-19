# Load .env if present — values can be overridden by environment variables
ifneq (,$(wildcard .env))
    include .env
    export
endif

IMAGE_NAME     := gnmibuddy-mcp
CONTAINER_NAME := gnmibuddy-mcp
IMAGE_TAG      := $(shell awk -F'"' '/^version/{print $$2}' pyproject.toml)
HOST_PORT      := $(or $(GNMIBUDDY_PORT),8000)

# INVENTORY_FILE defaults to NETWORK_INVENTORY so the .env value is reused automatically
INVENTORY_FILE ?= $(NETWORK_INVENTORY)

.PHONY: build run stop restart logs shell clean fresh dev dev-http help

## build INVENTORY_FILE=/path/to/inventory.json — build the container image
build:
ifndef INVENTORY_FILE
	$(error INVENTORY_FILE is required. Usage: make build INVENTORY_FILE=/path/to/inventory.json)
endif
	cp $(INVENTORY_FILE) .build_inventory.json
	podman build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	rm -f .build_inventory.json

## run — start the container in detached mode
run:
	podman run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):8000 \
		$(IMAGE_NAME):$(IMAGE_TAG)

## stop — stop and remove the running container
stop:
	podman rm -f $(CONTAINER_NAME) 2>/dev/null || true

## restart — stop then start the container
restart: stop run

## logs — tail the container logs
logs:
	podman logs -f $(CONTAINER_NAME)

## shell — open a shell in the running container
shell:
	podman exec -it $(CONTAINER_NAME) /bin/bash

## clean — stop the container and remove the image
clean: stop
	podman rmi -f $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	rm -f .build_inventory.json

## fresh INVENTORY_FILE=/path/to/inventory.json — delete existing container/image, rebuild, and run
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
