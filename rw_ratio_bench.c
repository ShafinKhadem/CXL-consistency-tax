// rw_ratio_bench.c
// Single-threaded random read/write benchmark with configurable write ratio.
// Fixed-operation version for gem5 SE mode.
//
// Build:
//   cc -static -O3 -std=c11 rw_ratio_bench.c -o rw_ratio_bench
//
// Example:
//   ./rw_ratio_bench --write-ratio 30 --elements 65536 --ops 100000 --seed 123

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
#include <stdatomic.h>

typedef struct
{
    uint64_t state;
} rng_t;

static inline uint64_t xorshift64star(rng_t *r)
{
    uint64_t x = r->state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    r->state = x;
    return x * 2685821657736338717ull;
}

static inline uint64_t now_ns(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    {
        perror("clock_gettime");
        exit(EXIT_FAILURE);
    }
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [--write-ratio PCT] [--elements N] [--ops N] [--seed SEED]\n"
            "\n"
            "Defaults:\n"
            "  --write-ratio 50\n"
            "  --elements 65536   (64K 64-bit elements)\n"
            "  --ops 100000       (100K operations)\n"
            "  --seed 1\n",
            prog);
}

static long parse_long(const char *s, const char *name)
{
    char *end = NULL;
    errno = 0;
    long v = strtol(s, &end, 10);
    if (errno != 0 || !end || *end != '\0')
    {
        fprintf(stderr, "Invalid %s: %s\n", name, s);
        exit(EXIT_FAILURE);
    }
    return v;
}

int main(int argc, char **argv)
{
    int write_ratio = 50;       // percent, 0..100
    size_t elements = 1u << 16; // 64K
    uint64_t ops = 100000ull;   // 100K ops
    uint64_t seed = 1;
    enum
    {
        ORDER_RELEASE,
        ORDER_RELAXED,
        ORDER_SEQUENTIAL
    } mem_order = ORDER_RELEASE; // Don't take this as input, otherwise the compiler might optimize away all atomics even in relaxed mode..

    memory_order store_order = mem_order == ORDER_RELEASE ? memory_order_release : mem_order == ORDER_SEQUENTIAL ? memory_order_seq_cst
                                                                                                                 : memory_order_relaxed;
    memory_order load_order = mem_order == ORDER_RELEASE ? memory_order_acquire : mem_order == ORDER_SEQUENTIAL ? memory_order_seq_cst
                                                                                                                : memory_order_relaxed;

    for (int i = 1; i < argc; ++i)
    {
        if (strcmp(argv[i], "--write-ratio") == 0 && i + 1 < argc)
        {
            write_ratio = (int)parse_long(argv[++i], "write-ratio");
        }
        else if (strcmp(argv[i], "--elements") == 0 && i + 1 < argc)
        {
            elements = (size_t)parse_long(argv[++i], "elements");
        }
        else if (strcmp(argv[i], "--ops") == 0 && i + 1 < argc)
        {
            ops = (uint64_t)parse_long(argv[++i], "ops");
        }
        else if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc)
        {
            seed = (uint64_t)parse_long(argv[++i], "seed");
        }
        else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0)
        {
            usage(argv[0]);
            return EXIT_SUCCESS;
        }
        else
        {
            usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    if (write_ratio < 0 || write_ratio > 100)
    {
        fprintf(stderr, "--write-ratio must be in [0, 100]\n");
        return EXIT_FAILURE;
    }
    if (elements < 1)
    {
        fprintf(stderr, "--elements must be at least 1\n");
        return EXIT_FAILURE;
    }
    if (ops < 1)
    {
        fprintf(stderr, "--ops must be positive\n");
        return EXIT_FAILURE;
    }

    size_t bytes = elements * sizeof(uint64_t);
    void *mem = NULL;
    int rc = posix_memalign(&mem, 64, bytes);
    if (rc != 0)
    {
        errno = rc;
        perror("posix_memalign");
        return EXIT_FAILURE;
    }

    atomic_uint_fast64_t *buf = (atomic_uint_fast64_t *)mem;

    rng_t rng = {.state = seed ? seed : 1ull};

    uint64_t read_ops = 0;
    uint64_t write_ops = 0;
    uint64_t read_sum = 0;
    uint64_t write_sum = 0;

    uint64_t t0 = now_ns();

    for (uint64_t i = 0; i < ops; ++i)
    {
        uint64_t r = xorshift64star(&rng);
        size_t idx = (size_t)(r % elements);

        uint64_t choice = xorshift64star(&rng) % 100ull;
        if ((int)choice < write_ratio)
        {
            uint64_t v = xorshift64star(&rng);
            atomic_store_explicit(&buf[idx], v, store_order);
            write_sum ^= v;
            ++write_ops;
        }
        else
        {
            uint64_t v = atomic_load_explicit(&buf[idx], load_order);
            read_sum += v;
            ++read_ops;
        }
    }

    uint64_t t1 = now_ns();
    double elapsed = (double)(t1 - t0) / 1e9;

    double read_mops = (double)read_ops / elapsed / 1e6;
    double write_mops = (double)write_ops / elapsed / 1e6;
    double total_mops = (double)(read_ops + write_ops) / elapsed / 1e6;

    printf("elements=%zu ops=%" PRIu64 " write_ratio=%d seed=%" PRIu64 " memory_order=%s\n",
           elements, ops, write_ratio, seed, mem_order == ORDER_RELEASE ? "release" : mem_order == ORDER_SEQUENTIAL ? "sequential"
                                                                                                                    : "relaxed");
    printf("elapsed=%.6f s\n", elapsed);
    printf("read_ops=%" PRIu64 " (%.3f Mop/s)\n", read_ops, read_mops);
    printf("write_ops=%" PRIu64 " (%.3f Mop/s)\n", write_ops, write_mops);
    printf("total_ops=%" PRIu64 " (%.3f Mop/s)\n", read_ops + write_ops, total_mops);
    printf("read_sum=%" PRIu64 "\n", read_sum);
    printf("write_sum=%" PRIu64 "\n", write_sum);

    free(mem);
    return EXIT_SUCCESS;
}
