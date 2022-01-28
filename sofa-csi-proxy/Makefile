GO111MODULE = on
GOPATH ?= $(shell go env GOPATH)
GOBIN ?= $(GOPATH)/bin
DOCKER_CLI_EXPERIMENTAL = enabled
export GOPATH GOBIN GO111MODULE DOCKER_CLI_EXPERIMENTAL
IMAGE_VERSION = v1.0.0
LDFLAGS = 
EXT_LDFLAGS = -s -w -extldflags "-static"


TOOL_DIR := ./tool
GOLANGCI_VERSION := v1.43.0
GOLANGCI_BIN := $(TOOL_DIR)/golangci-lint

all: sofa-storage-csi

install-go:
#	wget https://golang.org/dl/go1.17.3.linux-amd64.tar.gz
	mkdir -p .local
	tar -xf go1.17.3.linux-amd64.tar.gz -C ./.local

install-protoc:
#	wget https://github.com/protocolbuffers/protobuf/releases/download/v3.19.1/protoc-3.19.1-linux-x86_64.zip
	mkdir -p .local/protoc
	unzip protoc-3.19.1-linux-x86_64.zip -d ./.local/protoc

.PHONY: sofa-storage-csi
sofa-storage-csi:
	CGO_ENABLED=0 GOOS=linux GOARCH=$(ARCH) go build -a -ldflags "${LDFLAGS} ${EXT_LDFLAGS}" -o build/${ARCH}/sofa-storage-csi ./cmd

.PHONY: golangci
golangci: $(GOLANGCI_BIN)
	@echo === running golangci-lint
	@$(TOOL_DIR)/golangci-lint run ./...

$(GOLANGCI_BIN):
	@echo === installing golangci-lint
	@curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | bash -s -- -b $(TOOL_DIR) $(GOLANGCI_VERSION)

docker:
	docker build -t sofa-csi:latest .
