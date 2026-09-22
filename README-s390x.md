# Emscripten SDK for s390x (IBM Z Architecture)

## Overview

This guide provides instructions for setting up Emscripten SDK on s390x (IBM Z) architecture with big-endian support.

## Prerequisites

### System Requirements
- **Architecture**: s390x (IBM Z)
- **OS**: RHEL 9 or compatible Linux distribution
- **Endianness**: Big-endian (native s390x)

### Required Packages

```bash
# Install LLVM/Clang 20
sudo dnf install -y llvm20 llvm20-devel clang20

# Install lld (WebAssembly linker)
sudo dnf install -y lld lld-libs

# Create symlink for wasm-ld
sudo ln -sf /usr/bin/wasm-ld /usr/lib64/llvm20/bin/wasm-ld

# Install Python 3.11 (required by Emscripten)
sudo dnf install -y python3.11 python3.11-pip

# Set Python 3.11 as default
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo alternatives --set python3 /usr/bin/python3.11

# Install Node.js
sudo dnf install -y nodejs npm
```

### Build Binaryen from Source

Binaryen must be built from source on s390x:

```bash
# Clone Binaryen
git clone https://github.com/WebAssembly/binaryen.git
cd binaryen
git checkout version_133

# Build with warnings disabled
mkdir build && cd build
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DBUILD_TESTS=OFF \
  -DCMAKE_CXX_FLAGS="-Wno-error -Wno-restrict" \
  -DCMAKE_C_FLAGS="-Wno-error -Wno-restrict"

cmake --build . -j$(nproc)
sudo cmake --install .

# Configure library path
echo "/usr/local/lib64" | sudo tee /etc/ld.so.conf.d/binaryen.conf
sudo ldconfig
```

## Installation

### 1. Clone Emscripten

```bash
git clone https://github.com/emscripten-core/emscripten.git
cd emscripten
git checkout 5.0.7  # Tested version for s390x
```

### 2. Bootstrap Emscripten

```bash
python3 bootstrap.py
```

### 3. Configure Emscripten

Create `~/.emscripten` configuration file:

```python
import os
LLVM_ROOT = '/usr/lib64/llvm20/bin'
BINARYEN_ROOT = '/usr/local'
NODE_JS = '/usr/bin/node'
TEMP_DIR = '/tmp'
COMPILER_ENGINE = NODE_JS
JS_ENGINES = [NODE_JS]
```

## Usage

### Compiling for s390x Big-Endian

**IMPORTANT**: Always use `-sSUPPORT_BIG_ENDIAN` flag when compiling on s390x:

```bash
# Basic compilation
python3 emcc.py hello.c -o hello.html -sSUPPORT_BIG_ENDIAN

# With optimization
python3 emcc.py hello.c -o hello.html -sSUPPORT_BIG_ENDIAN -O3

# Running the output
node hello.js
```

### Example Program

```c
// hello.c
#include <stdio.h>

int main() {
    printf("Hello from WebAssembly on s390x!\n");
    return 0;
}
```

Compile and run:
```bash
python3 emcc.py hello.c -o hello.html -sSUPPORT_BIG_ENDIAN
node hello.js
```

## Toolchain Versions (Tested)

| Component | Version | Notes |
|-----------|---------|-------|
| LLVM/Clang | 20.1.8 | From EPEL repository |
| Binaryen | 133 | Built from source |
| lld (wasm-ld) | 21.1.8 | From RHEL repos |
| Node.js | v22.23.1 | From RHEL repos |
| Python | 3.11.13 | Required by Emscripten |
| Emscripten | 5.0.7 | Tested and working |

## Known Limitations

1. **Big-Endian Support**: The `-sSUPPORT_BIG_ENDIAN` flag is **experimental** in Emscripten
2. **LLVM Version Warning**: Emscripten expects LLVM 23, but LLVM 20 works with warnings
3. **Node.js Version**: Emscripten expects Node.js 18.3.0+, but v16.20.2+ works
4. **Feature Compatibility**: Not all Emscripten features are fully tested on big-endian systems

## Troubleshooting

### Error: "expected the system to be little-endian"
**Solution**: Add `-sSUPPORT_BIG_ENDIAN` flag to your compilation command.

### Error: "wasm-ld: undefined symbol: _emscripten_memcpy_bulkmem"
**Solution**: Clear Emscripten cache and rebuild:
```bash
rm -rf cache/*
python3 emcc.py your_file.c -o output.html -sSUPPORT_BIG_ENDIAN
```

### Error: "emscripten requires python 3.10 or above"
**Solution**: Ensure Python 3.11 is set as default:
```bash
python3 --version  # Should show 3.11.x
```

## Performance Considerations

- WebAssembly on s390x uses big-endian byte order
- Some operations may have different performance characteristics
- Test thoroughly for your specific use case

## Contributing

This s390x port is community-maintained. Contributions welcome!

## References

- [Emscripten Documentation](https://emscripten.org/)
- [WebAssembly Specification](https://webassembly.github.io/spec/)
- [IBM Z Architecture](https://www.ibm.com/z)

## License

Same as Emscripten SDK (MIT/Apache 2.0)
