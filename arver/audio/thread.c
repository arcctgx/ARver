#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <stdint.h>

#define THREADS 4

typedef struct ChecksumResult {
    ssize_t offset;
    uint32_t checksum;
} ChecksumResult;

typedef struct WorkerParams {
    pthread_t tid;
    pthread_mutex_t *mutex;
    ssize_t start;
    ssize_t end;
    size_t *index;
    ChecksumResult *results;
} WorkerParams;

static void *checksum_worker(void *arg) {
    WorkerParams *wp = arg;
    ChecksumResult r;

    printf("I am worker %ld, my loop chunk is <%ld, %ld)\n",
        wp->tid, wp->start, wp->end);

    for (ssize_t offset = wp->start; offset < wp->end; offset++) {
        usleep(1000); // simulate doing work
        r.offset = offset;
        r.checksum = wp->tid;   // placeholder value

        pthread_mutex_lock(wp->mutex);
        wp->results[*(wp->index)] = r;
        (*wp->index)++;
        pthread_mutex_unlock(wp->mutex);
    }

    return NULL;
}

int main(void)
{
    const ssize_t radius_sectors = 5;
    const ssize_t frames_per_sector = 588;
    const ssize_t total_results = 2*radius_sectors*frames_per_sector + 1;

    const ssize_t chunk_size = total_results / THREADS;
    const ssize_t remainder = total_results % THREADS;

    printf("threads = %d, total_results = %ld, chunk_size = %ld, remainder = %ld\n",
        THREADS, total_results, chunk_size, remainder);

    pthread_t workers[THREADS];
    WorkerParams wp[THREADS];
    ChecksumResult results[total_results];

    size_t index = 0;
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

    for (int t=0; t < THREADS; t++) {
        ssize_t start = -radius_sectors*frames_per_sector + t*chunk_size;
        ssize_t end = start + chunk_size;
        if (t == THREADS-1) {
            end += remainder;
        }

        wp[t] = (WorkerParams) {
            .tid = t,
            .mutex = &mutex,
            .start = start,
            .end = end,
            .index = &index,
            .results = results
        };
        pthread_create(&workers[t], NULL, &checksum_worker, &wp[t]);
    }

    for (int t=0; t < THREADS; t++) {
        pthread_join(workers[t], NULL);
    }

    printf("All workers done.\n");

    for (int i = 0; i < total_results; i++) {
        printf("%4d: offset = %5ld, checksum = %2d\n",
            i, results[i].offset, results[i].checksum);
    }

    return 0;
}
