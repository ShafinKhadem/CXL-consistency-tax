/*
 * stream_read.c — Bandwidth-sensitive streaming read benchmark
 *
 * Reads from S independent arrays in an interleaved round-robin pattern.
 * Each array is large enough to blow through L2, so every access is a
 * cache miss to main memory. With S streams, the O3 CPU can have up to
 * S independent loads in flight simultaneously, stressing bandwidth.
 *
 * Usage: ./stream_read [iterations] [num_streams]
 *   iterations  — number of read rounds (default 50000)
 *   num_streams — number of independent arrays (default 16)
 *
 * Each stream is 512KB (larger than 256KB L2), total footprint = S * 512KB.
 * Access is sequential within each stream to avoid prefetcher confusion
 * but interleaved across streams to maximize outstanding requests.
 */

#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STREAM_SIZE (512 * 1024 / sizeof(uint64_t))  /* 512KB per stream = 65536 uint64s */
#define CACHE_LINE  64

int main(int argc, char **argv) {
    size_t iters   = (argc > 1) ? strtoull(argv[1], NULL, 10) : 50000;
    int nstreams   = (argc > 2) ? atoi(argv[2]) : 16;

    /* Allocate streams, each cache-line aligned */
    volatile uint64_t **streams = malloc(sizeof(uint64_t *) * nstreams);
    for (int s = 0; s < nstreams; s++) {
        streams[s] = aligned_alloc(CACHE_LINE, STREAM_SIZE * sizeof(uint64_t));
        /* Initialize to avoid page faults during measurement */
        memset((void *)streams[s], 0xAB, STREAM_SIZE * sizeof(uint64_t));
    }

    /*
     * Main loop: interleave reads across all streams.
     * Each iteration reads one element from each stream, advancing the
     * index. This creates nstreams independent load misses per iteration.
     */
    volatile uint64_t sink = 0;  /* prevent optimization */
    for (size_t i = 0; i < iters; i++) {
        size_t idx = i % STREAM_SIZE;
        for (int s = 0; s < nstreams; s++) {
            sink += streams[s][idx];
        }
    }

    printf("done iters=%zu streams=%d sink=%lu\n", iters, nstreams, (unsigned long)sink);

    for (int s = 0; s < nstreams; s++)
        free((void *)streams[s]);
    free(streams);

    return 0;
}
