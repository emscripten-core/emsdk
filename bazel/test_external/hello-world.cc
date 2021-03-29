#include <iostream>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/bind.h>
using namespace emscripten;
#endif

void sayHello() {
  std::cout << "hello" << std::endl;
}

#ifdef __EMSCRIPTEN__
EMSCRIPTEN_BINDINGS(hello) {
  function("sayHello", &sayHello);
}
#endif

int main(int argc, char** argv) {
  std::cout << "hello world!" << std::endl;
  return 0;
}
