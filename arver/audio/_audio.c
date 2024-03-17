/* This file is part of ARver.
 *
 * ARver is free software: you can redistribute it and/or modify it under the terms
 * of the GNU General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * ARver is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * ARver. If not, see <https://www.gnu.org/licenses/>.
 */

/* A Python C extension to compute the AccurateRip checksums of WAV or FLAC tracks,
 * implemented according to <https://hydrogenaud.io/index.php/topic,97603.0.html>.
 *
 * Authors: Leo Bogert <http://leo.bogert.de>, Andreas Oberritter, arcctgx.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sndfile.h>
#include <zlib.h>

typedef uint16_t sample_t;  // CDDA 16-bit sample (single channel)
typedef uint32_t frame_t;   // CDDA stereo frame (a pair of 16-bit samples)

static bool check_format(SF_INFO info)
{
#ifdef DEBUG
    fprintf(stderr, "format: 0x%08x\n", info.format);
    fprintf(stderr, "frames: %ld\n", info.frames);
    fprintf(stderr, "CDDA sectors: %ld\n", info.frames/588);
    fprintf(stderr, "length: %.1f seconds\n", (double)info.frames/588/75);
    fprintf(stderr, "channels: %d\n", info.channels);
    fprintf(stderr, "sampling rate: %d Hz\n", info.samplerate);
#endif

    switch (info.format & SF_FORMAT_TYPEMASK) {
    case SF_FORMAT_WAV:
    case SF_FORMAT_FLAC:
        return (info.channels == 2) &&
               (info.samplerate == 44100) &&
               ((info.format & SF_FORMAT_SUBMASK) == SF_FORMAT_PCM_16);
    }

    return false;
}

static sample_t *load_audio_data(SNDFILE *file, SF_INFO info, size_t *size)
{
    size_t nsamples = info.frames * info.channels;
    sample_t *data = calloc(nsamples, sizeof(sample_t));

    if (data == NULL) {
        return NULL;
    }

    if (sf_readf_short(file, (short*)data, info.frames) != info.frames) {
        free(data);
        return NULL;
    }

    *size = nsamples;
    return data;
}

static void compute_checksums(const sample_t *data, size_t size, size_t track, size_t total_tracks, uint32_t *v1, uint32_t *v2)
{
    const frame_t *frames = (const frame_t*)data;
    const size_t nframes = size / 2;    // 2 samples per CDDA frame
    const size_t skip_frames = 5 * 588; // 5 CDDA sectors * 588 audio frames per sector

    uint32_t sum_from = 0;
    if (track == 1) {
        sum_from += skip_frames;
    }

    uint32_t sum_to = nframes;
    if (track == total_tracks) {
        sum_to -= skip_frames;
    }

    uint32_t csum_hi = 0;
    uint32_t csum_lo = 0;
    uint32_t multiplier = 1;
    for (size_t i = 0; i < nframes; i++) {
        if (multiplier >= sum_from && multiplier <= sum_to) {
            uint64_t product = (uint64_t)frames[i] * (uint64_t)multiplier;
            csum_hi += (uint32_t)(product >> 32);
            csum_lo += (uint32_t)(product);
        }
        multiplier++;
    }

    *v1 = csum_lo;
    *v2 = csum_lo + csum_hi;
}

static PyObject *accuraterip_compute(PyObject *self, PyObject *args)
{
    const char *path;
    unsigned int track;
    unsigned int total_tracks;
    uint32_t v1, v2;
    SF_INFO info = {0};
    SNDFILE *file = NULL;

    if (!PyArg_ParseTuple(args, "sII", &path, &track, &total_tracks)) {
        return NULL;
    }

    if (total_tracks < 1 || total_tracks > 99) {
        return PyErr_Format(PyExc_ValueError, "Invalid total_tracks: %d", total_tracks);
    }

    if (track < 1 || track > total_tracks) {
        return PyErr_Format(PyExc_ValueError, "Invalid track: %d/%d", track, total_tracks);
    }

    file = sf_open(path, SFM_READ, &info);
    if (file == NULL) {
        PyErr_SetString(PyExc_OSError, sf_strerror(NULL));
        return NULL;
    }

#ifdef DEBUG
    fprintf(stderr, "path: %s\n", path);
    int swab = sf_command(file, SFC_RAW_DATA_NEEDS_ENDSWAP, NULL, 0);
    fprintf(stderr, "endianness swapped: %s\n", swab ? "yes" : "no");
#endif

    if (!check_format(info)) {
        sf_close(file);
        PyErr_SetString(PyExc_TypeError, "check_format failed!");
        return NULL;
    }

    size_t size = 0;
    sample_t *data = load_audio_data(file, info, &size);
    sf_close(file);

    if (data == NULL) {
        PyErr_SetString(PyExc_OSError, "load_audio_data failed!");
        return NULL;
    }

    compute_checksums(data, size, track, total_tracks, &v1, &v2);
    free(data);

    return Py_BuildValue("II", v1, v2);
}

static PyObject *crc32_compute(PyObject *self, PyObject *args)
{
    const char *path = NULL;
    SNDFILE *file = NULL;
    SF_INFO info = {0};

    if (!PyArg_ParseTuple(args, "s", &path)) {
        return NULL;
    }

    if ((file = sf_open(path, SFM_READ, &info)) == NULL) {
        PyErr_SetString(PyExc_OSError, sf_strerror(file));
        return NULL;
    }

#ifdef DEBUG
    fprintf(stderr, "path: %s\n", path);
    int swab = sf_command(file, SFC_RAW_DATA_NEEDS_ENDSWAP, NULL, 0);
    fprintf(stderr, "endianness swapped: %s\n", swab ? "yes" : "no");
#endif

    if (!check_format(info)) {
        sf_close(file);
        PyErr_SetString(PyExc_TypeError, "Unsupported audio format.");
        return NULL;
    }

    size_t size = 0;
    sample_t *data = load_audio_data(file, info, &size);
    sf_close(file);

    if (data == NULL) {
        PyErr_SetString(PyExc_OSError, "Failed to load audio samples.");
        return NULL;
    }

    uint32_t crc = crc32(0L, Z_NULL, 0);
    crc = crc32(crc, (uint8_t*)data, 2*size);   // 2 bytes per CDDA sample
    free(data);

    return PyLong_FromUnsignedLong(crc);
}

static PyObject *get_nframes(PyObject *self, PyObject *args)
{
    const char *path = NULL;
    SNDFILE *file = NULL;
    SF_INFO info = {0};

    if (!PyArg_ParseTuple(args, "s", &path)) {
        return NULL;
    }

    if ((file = sf_open(path, SFM_READ, &info)) == NULL) {
        PyErr_SetString(PyExc_OSError, sf_strerror(file));
        return NULL;
    }
    sf_close(file);

    if (!check_format(info)) {
        PyErr_SetString(PyExc_TypeError, "Unsupported audio format.");
        return NULL;
    }

    return PyLong_FromLong(info.frames);
}

static PyObject *libsndfile_version(PyObject *self, PyObject *args)
{
    return PyUnicode_FromString(sf_version_string());
}

static PyMethodDef accuraterip_methods[] = {
    { "compute", accuraterip_compute, METH_VARARGS, PyDoc_STR("Calculate AccurateRip v1 and v2 checksums.") },
    { "crc32", crc32_compute, METH_VARARGS, PyDoc_STR("Calculate CRC32 checksum of an audio file.") },
    { "nframes", get_nframes, METH_VARARGS, PyDoc_STR("Get the number of frames in an audio file.") },
    { "libsndfile_version", libsndfile_version, METH_VARARGS,  PyDoc_STR("Get libsndfile version string.") },
    { NULL, NULL, 0, NULL },
};

static struct PyModuleDef accuraterip_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "accuraterip",
    .m_methods = accuraterip_methods,
};

PyMODINIT_FUNC PyInit_accuraterip(void)
{
    return PyModule_Create(&accuraterip_module);
}
