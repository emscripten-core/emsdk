#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/bind.h>
using namespace emscripten;
#endif

#include <iostream>

void sayHello() {
  std::cout << "hello" << std::endl;
}

#ifdef __EMSCRIPTEN__
EMSCRIPTEN_BINDINGS(aa) {
  function("sayHello", &sayHello);
}
#else
int main(int argc, char** argv) {
  std::cout << "start main function" << std::endl;
  sayHello();
  std::cout << "end main function" << std::endl;
  return 0;
}
#endif
