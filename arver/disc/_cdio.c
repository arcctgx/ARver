#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <cdio/cdio.h>
#include <cdio/cdio_config.h>
#include <cdio/logging.h>

static int have_disc(CdIo_t *device)
{
    if (cdio_get_last_track_num(device) == CDIO_INVALID_TRACK) {
        return 0;
    }

    return 1;
}

static PyObject *last_session_lsn(PyObject *self, PyObject *args)
{
    const char *device_path = NULL;
    CdIo_t *device = NULL;
    lsn_t last_session_lsn = -1;

    if (!PyArg_ParseTuple(args, "|z", &device_path)) {
        return NULL;
    }

    if ((device = cdio_open(device_path, DRIVER_DEVICE)) == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Failed to open %s",
            device_path == NULL ? "the default device" : device_path);
        return NULL;
    }

    if (!have_disc(device)) {
        PyErr_Format(PyExc_RuntimeError, "Failed to read the CD in %s",
            device_path == NULL ? "the default device" : device_path);
        cdio_destroy(device);
        return NULL;
    }

    cdio_get_last_session(device, &last_session_lsn);
    cdio_destroy(device);

    return PyLong_FromLong(last_session_lsn);
}

static PyObject *lead_out_lba(PyObject *self, PyObject *args)
{
    const char *device_path = NULL;
    CdIo_t *device = NULL;

    if (!PyArg_ParseTuple(args, "|z", &device_path)) {
        return NULL;
    }

    if ((device = cdio_open(device_path, DRIVER_DEVICE)) == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Failed to open %s",
            device_path == NULL ? "the default device" : device_path);
        return NULL;
    }

    if (!have_disc(device)) {
        PyErr_Format(PyExc_RuntimeError, "Failed to read the CD in %s",
            device_path == NULL ? "the default device" : device_path);
        cdio_destroy(device);
        return NULL;
    }

    lba_t lead_out_lba = cdio_get_track_lba(device, CDIO_CDROM_LEADOUT_TRACK);
    cdio_destroy(device);

    return PyLong_FromLong(lead_out_lba);
}

static PyObject *track_listing(PyObject *self, PyObject *args)
{
    const char *device_path = NULL;
    CdIo_t *device = NULL;
    PyObject *list = NULL;
    PyObject *tuple = NULL;

    if (!PyArg_ParseTuple(args, "|z", &device_path)) {
        return NULL;
    }

    if ((device = cdio_open(device_path, DRIVER_DEVICE)) == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Failed to open %s",
            device_path == NULL ? "the default device" : device_path);
        return NULL;
    }

    track_t first_track_num = cdio_get_first_track_num(device);
    track_t last_track_num = cdio_get_last_track_num(device);

    if (first_track_num == CDIO_INVALID_TRACK || last_track_num == CDIO_INVALID_TRACK) {
        PyErr_Format(PyExc_RuntimeError, "Failed to read the CD in %s",
            device_path == NULL ? "the default device" : device_path);
        goto error;
    }

    if ((list = PyList_New(0)) == NULL) {
        goto error;
    }

    for (track_t num = first_track_num; num <= last_track_num; num++) {
        lsn_t track_last_lsn = -1;

        // cdio_get_track_last_lsn() returns CDIO_INVALID_LSN for track 99. This
        // looks like a bug in libcdio. Track 99 must be the last track on the CD,
        // so we can use the lead out LSN to calculate the last LSN of track 99.
        if (num < 99) {
            track_last_lsn = cdio_get_track_last_lsn(device, num);
        } else {
            track_last_lsn = cdio_get_track_lsn(device, CDIO_CDROM_LEADOUT_TRACK) - 1;
        }

        lsn_t frames = track_last_lsn - cdio_get_track_lsn(device, num) + 1;
        lba_t lba = cdio_get_track_lba(device, num);
        track_format_t format = cdio_get_track_format(device, num);

        if ((tuple = Py_BuildValue("Biis", num, lba, frames, track_format2str[format])) == NULL) {
            goto error;
        }

        if (PyList_Append(list, tuple) == -1) {
            goto error;
        }

        Py_DECREF(tuple);
    }

    cdio_destroy(device);
    return list;

error:
    cdio_destroy(device);
    Py_XDECREF(tuple);
    Py_XDECREF(list);
    return NULL;
}

static PyObject *libcdio_version(PyObject *self, PyObject *Py_UNUSED(args))
{
    return PyUnicode_FromString("libcdio-"CDIO_VERSION);
}

static PyMethodDef _cdio_methods[] = {
    { "last_session_lsn", last_session_lsn, METH_VARARGS, PyDoc_STR("Return the LSN of the first track in the last CD session.") },
    { "lead_out_lba", lead_out_lba, METH_VARARGS, PyDoc_STR("Return the LBA of the lead out track.") },
    { "track_listing", track_listing, METH_VARARGS, PyDoc_STR("Return CD track listing as a list of (num, lba, frames, type) tuples.") },
    { "libcdio_version", libcdio_version, METH_NOARGS, PyDoc_STR("Return libcdio version string.") },
    { NULL, NULL, 0, NULL },
};

static struct PyModuleDef _cdio_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_cdio",
    .m_doc = PyDoc_STR("Minimal libcdio bindings for getting CD TOC information."),
    .m_methods = _cdio_methods,
    .m_size = 0
};

PyMODINIT_FUNC PyInit__cdio(void)
{
    cdio_loglevel_default = CDIO_LOG_ASSERT;
    return PyModule_Create(&_cdio_module);
}
