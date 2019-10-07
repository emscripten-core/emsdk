### Building

This image requires to specify following build arguments:

| arg | description |
| --- | --- |
| `EMSCRIPTEN_VERSION` | One of released version of Emscripten. For example `1.38.45`<br/> Can be used with `-upstream` variant like: `1.38.45-upstream`<br /> Minimal supported version is **1.38.40**|

```bash
docker build \
    --build-arg=EMSCRIPTEN_VERSION=1.38.43-upstream \
    --tag test \
    .
```
