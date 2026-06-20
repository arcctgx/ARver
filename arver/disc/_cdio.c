#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <cdio/cdio.h>
#include <cdio/cdio_config.h>
#include <cdio/logging.h>

typedef struct {
    PyObject_HEAD
    CdIo_t *device;
} DeviceObject;

static int Device_init(DeviceObject *self, PyObject *args, PyObject *Py_UNUSED(kwds))
{
    cdio_loglevel_default = CDIO_LOG_ASSERT;
    const char *device_path = NULL;
    self->device = NULL;

    if (!PyArg_ParseTuple(args, "|z", &device_path)) {
        return -1;
    }

    if ((self->device = cdio_open(device_path, DRIVER_DEVICE)) == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Failed to open %s",
            device_path == NULL ? "the default device" : device_path);
        return -1;
    }

    if (cdio_get_last_track_num(self->device) == CDIO_INVALID_TRACK) {
        PyErr_Format(PyExc_RuntimeError, "Failed to read the CD in %s",
            device_path == NULL ? "the default device" : device_path);
        return -1;
    }

    return 0;
}

static void Device_dealloc(DeviceObject *self)
{
    if (self->device != NULL) {
        cdio_destroy(self->device);
        self->device = NULL;
    }

    PyTypeObject *tp = Py_TYPE(self);
    freefunc tp_free = PyType_GetSlot(tp, Py_tp_free);
    tp_free(self);
    Py_DECREF(tp);
}

static PyObject *Device_last_session_lsn(DeviceObject *self, PyObject *Py_UNUSED(args))
{
    lsn_t last_session_lsn = -1;
    cdio_get_last_session(self->device, &last_session_lsn);
    return PyLong_FromLong(last_session_lsn);
}

static PyObject *Device_lead_out_lba(DeviceObject *self, PyObject *Py_UNUSED(args))
{
    lba_t lead_out_lba = cdio_get_track_lba(self->device, CDIO_CDROM_LEADOUT_TRACK);
    return PyLong_FromLong(lead_out_lba);
}

static PyObject *Device_track_listing(DeviceObject *self, PyObject *Py_UNUSED(args))
{
    PyObject *list = NULL;
    PyObject *tuple = NULL;
    track_t first_track_num = cdio_get_first_track_num(self->device);
    track_t last_track_num = cdio_get_last_track_num(self->device);

    if (first_track_num == CDIO_INVALID_TRACK || last_track_num == CDIO_INVALID_TRACK) {
        PyErr_Format(PyExc_RuntimeError, "Failed to read the CD TOC");
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
            track_last_lsn = cdio_get_track_last_lsn(self->device, num);
        } else {
            track_last_lsn = cdio_get_track_lsn(self->device, CDIO_CDROM_LEADOUT_TRACK) - 1;
        }

        lsn_t frames = track_last_lsn - cdio_get_track_lsn(self->device, num) + 1;
        lba_t lba = cdio_get_track_lba(self->device, num);
        track_format_t format = cdio_get_track_format(self->device, num);

        if ((tuple = Py_BuildValue("Biis", num, lba, frames, track_format2str[format])) == NULL) {
            goto error;
        }

        if (PyList_Append(list, tuple) == -1) {
            goto error;
        }

        Py_DECREF(tuple);
    }

    return list;

error:
    Py_XDECREF(tuple);
    Py_XDECREF(list);
    return NULL;
}

static PyMethodDef Device_methods[] = {
    { "last_session_lsn", (PyCFunction)Device_last_session_lsn, METH_NOARGS, PyDoc_STR("Return the LSN of the first track in the last CD session.") },
    { "lead_out_lba", (PyCFunction)Device_lead_out_lba, METH_NOARGS, PyDoc_STR("Return the LBA of the lead out track.") },
    { "track_listing", (PyCFunction)Device_track_listing, METH_NOARGS, PyDoc_STR("Return CD track listing as a list of (num, lba, frames, type) tuples.") },
    { NULL, NULL, 0, NULL },
};

static PyType_Slot Device_slots[] = {
    {Py_tp_doc, PyDoc_STR("Representation of an optical drive with readable, non-blank medium.")},
    {Py_tp_new, PyType_GenericNew},
    {Py_tp_init, Device_init},
    {Py_tp_dealloc, Device_dealloc},
    {Py_tp_methods, Device_methods},
    {0, NULL}
};

static PyType_Spec Device_spec = {
    .name = "_cdio.Device",
    .basicsize = sizeof(DeviceObject),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT,
    .slots = Device_slots,
};

static PyObject *libcdio_version(PyObject *self, PyObject *Py_UNUSED(args))
{
    return PyUnicode_FromString("libcdio-"CDIO_VERSION);
}

static PyMethodDef _cdio_methods[] = {
    { "libcdio_version", libcdio_version, METH_NOARGS, PyDoc_STR("Return libcdio version string.") },
    { NULL, NULL, 0, NULL },
};

static int _cdio_modexec(PyObject *m)
{
    PyObject *Device_Type = PyType_FromSpec(&Device_spec);
    if (Device_Type == NULL) {
        return -1;
    }

    if (PyModule_AddObject(m, "Device", Device_Type) < 0) {
        Py_DECREF(Device_Type);
        return -1;
    }

    return 0;
}

static PyModuleDef_Slot _cdio_slots[] = {
    {Py_mod_exec, _cdio_modexec},
    {0, NULL}
};

static struct PyModuleDef _cdio_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_cdio",
    .m_doc = PyDoc_STR("Minimal libcdio bindings for getting CD TOC information."),
    .m_methods = _cdio_methods,
    .m_size = 0,
    .m_slots = _cdio_slots
};

PyMODINIT_FUNC PyInit__cdio(void)
{
    return PyModuleDef_Init(&_cdio_module);
}
