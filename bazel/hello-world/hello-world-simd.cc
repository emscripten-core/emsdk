#include <wasm_simd128.h>

void multiply_arrays(int* out, int* in_a, int* in_b, int size) {
  for (int i = 0; i < size; i += 4) {
    v128_t a = wasm_v128_load(&in_a[i]);
    v128_t b = wasm_v128_load(&in_b[i]);
    v128_t prod = wasm_i32x4_mul(a, b);
    wasm_v128_store(&out[i], prod);
  }
}

#ifdef __wasm_relaxed_simd__

float dot_product_accumulate(const float* A, const float* B, int len, float initial_sum) {
    int i = 0;

    // Initialize accumulator vector with the initial sum spread across all lanes
    // We will sum these lanes at the end.
    v128_t acc = wasm_f32x4_splat(initial_sum);

    // Main loop: process 4 elements at a time
    // Requires len to be at least 4. If len < 4, the loop is skipped.
    for (; i + 4 <= len; i += 4) {
        // Load 4 floats from A and B
        v128_t va = wasm_v128_load(&A[i]);
        v128_t vb = wasm_v128_load(&B[i]);

        // Fused Multiply-Add: acc = (va * vb) + acc
        // Uses relaxed rounding for performance
        acc = __builtin_wasm_relaxed_madd_f32x4(va, vb, acc);
    }

    // Horizontal add: sum the 4 lanes of the accumulator
    // acc = {s0, s1, s2, s3}
    // sum = s0 + s1 + s2 + s3
    v128_t sum1 = wasm_f32x4_add(acc, wasm_i32x4_shuffle(acc, acc, 1, 0, 3, 2)); // {s0+s1, s0+s1, s2+s3, s2+s3}
    v128_t sum2 = wasm_f32x4_add(sum1, wasm_i32x4_shuffle(sum1, sum1, 2, 3, 0, 1)); // {total, total, total, total}

    float result = wasm_f32x4_extract_lane(sum2, 0);

    // Handle remaining elements (tail loop)
    for (; i < len; i++) {
        result += A[i] * B[i];
    }

    return result;
}

#endif
