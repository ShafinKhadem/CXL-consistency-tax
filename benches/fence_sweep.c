#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <x86intrin.h>

static inline void mfence(void) { _mm_mfence(); }

int main(int argc, char **argv) {
    size_t n = (argc > 1) ? strtoull(argv[1], NULL, 10) : 1000000;
    size_t K = (argc > 2) ? strtoull(argv[2], NULL, 10) : 16;

    volatile uint64_t *a = aligned_alloc(64, n * sizeof(uint64_t));
    for (size_t i = 0; i < n; i++) {
        a[i] = i;
        if ((i % K) == 0) mfence();
    }

    printf("done n=%zu K=%zu last=%lu\n", n, K, a[n - 1]);
    return 0;
}
