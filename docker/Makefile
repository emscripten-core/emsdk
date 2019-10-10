#!/usr/bin/env make

# Emscripten version to build: Should match the version that has been already released.
# i.e.:  1.38.45, 1.38.45-upstream
version =
alias =

.TEST:
ifndef version
	$(error argument 'version' is not set. Please call `make version=SOME_VERSION ...`)
endif

build: .TEST
	docker build --build-arg=EMSCRIPTEN_VERSION=${version} --tag emscripten/emscripten:${version} .

push: .TEST
	docker push emscripten/emscripten:${version}
ifdef alias
	docker tag emscripten/emscripten:${version} emscripten/emscripten:${alias}
	docker push emscripten/emscripten:${alias}
endif
