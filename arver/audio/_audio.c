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

static bool check_fileformat(const SF_INFO *sfinfo)
{
#ifdef DEBUG
    printf("Channels: %i\n", sfinfo->channels);
    printf("Format: %X\n", sfinfo->format);
    printf("Frames: %li\n", sfinfo->frames);
    printf("Samplerate: %i\n", sfinfo->samplerate);
    printf("Sections: %i\n", sfinfo->sections);
    printf("Seekable: %i\n", sfinfo->seekable);
#endif

    switch (sfinfo->format & SF_FORMAT_TYPEMASK) {
    case SF_FORMAT_WAV:
    case SF_FORMAT_FLAC:
        return (sfinfo->channels == 2) &&
               (sfinfo->samplerate == 44100) &&
               ((sfinfo->format & SF_FORMAT_SUBMASK) == SF_FORMAT_PCM_16);
    }

    return false;
}

static uint16_t *load_samples(SNDFILE *sndfile, SF_INFO info, size_t *size)
{
    size_t samples = info.frames * info.channels;
    uint16_t *audio = calloc(samples, sizeof(uint16_t));

    if (audio == NULL) {
        return NULL;
    }

    if (sf_readf_short(sndfile, (short*)audio, info.frames) != info.frames) {
        free(audio);
        return NULL;
    }

    *size = samples;
    return audio;
}

static void compute_checksums(const uint16_t *audio, size_t samples, size_t track_number, size_t total_tracks, uint32_t *v1, uint32_t *v2)
{
    uint32_t csum_hi = 0;
    uint32_t csum_lo = 0;
    uint32_t AR_CRCPosCheckFrom = 0;
    uint32_t *audio_data = (uint32_t*)audio;
    size_t Datauint32_tSize = samples / 2;
    uint32_t AR_CRCPosCheckTo = Datauint32_tSize;
    const size_t SectorBytes = 2352;        // each sector
    uint32_t MulBy = 1;
    size_t i;

    if (track_number == 1)          // first?
        AR_CRCPosCheckFrom += ((SectorBytes * 5) / sizeof(uint32_t));
    if (track_number == total_tracks)       // last?
        AR_CRCPosCheckTo -= ((SectorBytes * 5) / sizeof(uint32_t));

    for (i = 0; i < Datauint32_tSize; i++) {
        if (MulBy >= AR_CRCPosCheckFrom && MulBy <= AR_CRCPosCheckTo) {
            uint64_t product = (uint64_t)audio_data[i] * (uint64_t)MulBy;
            csum_hi += (uint32_t)(product >> 32);
            csum_lo += (uint32_t)(product);
        }
        MulBy++;
    }

    *v1 = csum_lo;
    *v2 = csum_lo + csum_hi;
}

static PyObject *accuraterip_compute(PyObject *self, PyObject *args)
{
    const char *filename;
    unsigned int track_number;
    unsigned int total_tracks;
    uint32_t v1, v2;
    uint16_t *audio_data;
    size_t size;
    SF_INFO sfinfo = {0};
    SNDFILE *sndfile = NULL;

    if (!PyArg_ParseTuple(args, "sII", &filename, &track_number, &total_tracks)) {
        return NULL;
    }

    if (total_tracks < 1 || total_tracks > 99) {
        return PyErr_Format(PyExc_ValueError, "Invalid total_tracks: %d", total_tracks);
    }

    if (track_number < 1 || track_number > total_tracks) {
        return PyErr_Format(PyExc_ValueError, "Invalid track_number: %d/%d", track_number, total_tracks);
    }

#ifdef DEBUG
    printf("Reading %s\n", filename);
#endif

    sndfile = sf_open(filename, SFM_READ, &sfinfo);
    if (sndfile == NULL) {
        PyErr_SetString(PyExc_OSError, sf_strerror(NULL));
        return NULL;
    }

    if (!check_fileformat(&sfinfo)) {
        sf_close(sndfile);
        PyErr_SetString(PyExc_TypeError, "check_fileformat failed!");
        return NULL;
    }

    size = 0;
    audio_data = load_samples(sndfile, sfinfo, &size);
    sf_close(sndfile);

    if (audio_data == NULL) {
        PyErr_SetString(PyExc_OSError, "load_samples failed!");
        return NULL;
    }

    compute_checksums(audio_data, size, track_number, total_tracks, &v1, &v2);
    free(audio_data);

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
    fprintf(stderr, "frames: %ld\n", info.frames);
    fprintf(stderr, "CDDA sectors: %ld\n", info.frames/588);
    fprintf(stderr, "length: %.1f seconds\n", (double)info.frames/588/75);
    fprintf(stderr, "channels: %d\n", info.channels);
    fprintf(stderr, "sampling rate: %d Hz\n", info.samplerate);
    int swab = sf_command(file, SFC_RAW_DATA_NEEDS_ENDSWAP, NULL, 0);
    fprintf(stderr, "endianness swapped: %s\n", swab ? "yes" : "no");
#endif

    if (!check_fileformat(&info)) {
        sf_close(file);
        PyErr_SetString(PyExc_TypeError, "Unsupported audio format.");
        return NULL;
    }

    size_t samples = 0;
    uint16_t *audio = load_samples(file, info, &samples);
    sf_close(file);

    if (audio == NULL) {
        PyErr_SetString(PyExc_OSError, "Failed to load audio samples.");
        return NULL;
    }

    uint32_t crc = crc32(0L, Z_NULL, 0);
    crc = crc32(crc, (uint8_t*)audio, 2*samples);
    free(audio);

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

    if (!check_fileformat(&info)) {
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
