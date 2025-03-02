#include <stdio.h>
#include <stdlib.h>
#include <sndfile.h>

int main(void)
{
    const char *path = "track01.cdda.flac";
    //const sf_count_t frames = 2940;
    const sf_count_t frames = 160000000;

    SF_INFO info = {0};

    SNDFILE *file = sf_open(path, SFM_READ, &info);
    printf("frames: %ld\n", info.frames);

    sf_count_t position = sf_seek(file, -frames, SEEK_END);
    printf("position: %ld\n", position);

    short *audio = calloc(frames*info.channels, sizeof(short));

    sf_count_t frames_read = sf_readf_short(file, audio, frames);
    printf("frames read: %ld\n", frames_read);

    sf_close(file);
    free(audio);

    return 0;
}
