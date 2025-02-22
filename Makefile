DOCKER ?= docker
HOST_IP ?= 127.0.0.1
HOST_PORT ?= 8080
DEBUG ?= 0

.PHONY: build start test clean


start: build
	$(DOCKER) run -p $(HOST_IP):$(HOST_PORT):8080 -e MAIN_BRANCH="master" -e DEBUG=0 wenote-api &

start_debug: build
	$(DOCKER) run -p $(HOST_IP):$(HOST_PORT):8080 -it -e MAIN_BRANCH="master" -e DEBUG=1 wenote-api

test: build start
	sleep 2
	$(DOCKER) exec -it $$( $(DOCKER) ps -q -f "ancestor=wenote-api" ) pytest

build:
	$(DOCKER) build . -t wenote-api

clean:
	$(DOCKER) rm -f $$( $(DOCKER) ps -q -f "ancestor=wenote-api" ) 2> /dev/null || true

