#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>

static atomic_flag lock = ATOMIC_FLAG_INIT;

static inline void lock_acq(void) {
    while (atomic_flag_test_and_set_explicit(&lock, memory_order_acquire)) {}
}

static inline void lock_rel(void) {
    atomic_flag_clear_explicit(&lock, memory_order_release);
}

static long iters = 1000000;
static long shared = 0;

void *worker(void *arg) {
    (void)arg;
    for (long i = 0; i < iters; i++) {
        lock_acq();
        shared++;
        lock_rel();
    }
    return NULL;
}

int main(int argc, char **argv) {
    int t = (argc > 1) ? atoi(argv[1]) : 2;
    iters  = (argc > 2) ? atol(argv[2]) : iters;

    pthread_t *th = malloc(sizeof(pthread_t) * t);
    for (int i = 0; i < t; i++)
        pthread_create(&th[i], NULL, worker, NULL);
    for (int i = 0; i < t; i++)
        pthread_join(th[i], NULL);

    printf("threads=%d iters=%ld shared=%ld\n", t, iters, shared);
    return 0;
}
