.DEFAULT_GOAL := build

# Update GoFrame and its CLI to latest stable version.
.PHONY: up
up: cli.install
	@gf up -a

# Build binary using configuration from hack/config.yaml.
.PHONY: build
build: cli.install
	@gf build -ew

# Parse api and generate controller/sdk.
.PHONY: ctrl
ctrl: cli.install
	@gf gen ctrl

# Generate Go files for DAO/DO/Entity.
.PHONY: dao
dao: cli.install
	@gf gen dao

# Parse current project go files and generate enums go file.
.PHONY: enums
enums: cli.install
	@gf gen enums


# Build docker image.
.PHONY: image
image: cli.install build
	$(eval DEFAULT_TAG  = $(shell git rev-parse --short HEAD))
ifneq (, $(shell git status --porcelain 2>/dev/null))
	$(eval DEFAULT_TAG  = $(DEFAULT_TAG).dirty)
endif
	$(eval TAG  = $(if ${t}, ${t}, ${DOCKER_TAG}))
	@bash manifest/docker/docker.sh
	@echo "docker build --push --load --platform linux/amd64 -f manifest/docker/Dockerfile -t loads/$(DOCKER_NAME):$(TAG) ."
	@docker build --push --load --platform linux/amd64 \
	   -f manifest/docker/Dockerfile \
	   -t loads/$(DOCKER_NAME):$(TAG) .

# Deploy image and yaml to current kubectl environment.
.PHONY: deploy
deploy: cli.install
	$(eval ENV  = $(if ${e}, ${e}, develop))

	@set -e; \
	mkdir -p $(ROOT_DIR)/temp/kustomize;\
	cd $(ROOT_DIR)/manifest/deploy/kustomize/overlays/${ENV};\
	kustomize build > $(ROOT_DIR)/temp/kustomize.yaml;\
	kubectl   apply -f $(ROOT_DIR)/temp/kustomize.yaml; \
	if [ $(DEPLOY_NAME) != "" ]; then \
		kubectl patch \
		-n $(NAMESPACE) deployment/$(DEPLOY_NAME) \
		-p "{\"spec\":{\"template\":{\"metadata\":{\"labels\":{\"date\":\"$(shell date +%s)\"}}}}}"; \
	fi;


# Parsing protobuf files and generating go files.
.PHONY: pb
pb: cli.install
	@gf gen pb

