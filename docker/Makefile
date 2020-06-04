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
	docker build --network host --build-arg=EMSCRIPTEN_VERSION=${version} --tag emscripten/emsdk:${version} .

push: .TEST
	docker push emscripten/emsdk:${version}
ifdef alias
	docker tag emscripten/emsdk:${version} emscripten/emsdk:${alias}
	docker push emscripten/emsdk:${alias}
endif
