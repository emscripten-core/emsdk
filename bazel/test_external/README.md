```bash
# Native
bazel run :hello-world

# Build wasm
bazel build --config=wasm :hello-world
bazel build :hello-world-wasm
```