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
	docker build --network host --build-arg=EMSCRIPTEN_VERSION=${version}-upstream --tag emscripten/emsdk:${version} .

test: .TEST
	# compilation without root
	docker run --rm -u 1000:1000 -v `pwd`:/src -w /src emscripten/emsdk:${version} emcc -c main.c -o main
	# artifact should be removable from host by non-root
	rm -fr main

	# running as non-root and forcing downloading ports
	docker run --rm -u 1000:1000 --net=host emscripten/emsdk:${version} embuilder build zlib

	# compilation without entrypoint
	docker run --rm -e /bin/bash -v `pwd`:/src -w /src emscripten/emsdk:${version} emcc -c main.c -o main
	# artifact should be removable from host by non-root
	rm -fr main

push: .TEST
	docker push emscripten/emsdk:${version}
ifdef alias
	docker tag emscripten/emsdk:${version} emscripten/emsdk:${alias}
	docker push emscripten/emsdk:${alias}
endif
