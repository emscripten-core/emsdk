#!/usr/bin/env make

# Emscripten version to build: Should match the version that has been already released.
# i.e.:  1.39.18
version =
alias =

.TEST:
ifndef version
	$(error argument 'version' is not set. Please call `make version=SOME_VERSION ...`)
endif

build: .TEST
	docker build --network host --build-arg=EMSCRIPTEN_VERSION=${version} --tag emscripten/emsdk:${version} .

test: .TEST
	# compilation as non-root
	docker run --rm -u `id -u`:`id -g` -v `pwd`:/src -w /src emscripten/emsdk:${version} \
		bash -c "\
			mkdir -p .test \
			&& echo 'int main() { return 0; }' > .test/main.c \
			&& emcc -c .test/main.c -o .test/main\
		"
	# artifact should be removable from host by non-root
	rm -fr .test

	# running as non-root and forcing downloading ports
	docker run --rm -u `id -u`:`id -g` --net=host emscripten/emsdk:${version} embuilder build zlib

	# compilation without entrypoint
	docker run --rm -e /bin/bash -v `pwd`:/src -w /src emscripten/emsdk:${version} \
		bash -c "\
			mkdir -p .test \
			&& echo 'int main() { return 0; }' > .test/main.c \
			&& emcc -c .test/main.c -o .test/main\
		"

	# artifact should be removable from host by non-root
	rm -fr .test

push: .TEST
	docker push emscripten/emsdk:${version}
ifdef alias
	docker tag emscripten/emsdk:${version} emscripten/emsdk:${alias}
	docker push emscripten/emsdk:${alias}
endif
