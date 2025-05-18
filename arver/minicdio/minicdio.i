%module minicdio

%{
#include <cdio/cdio.h>
%}

// device.h
%constant long int DRIVER_UNKNOWN          = DRIVER_UNKNOWN;
%constant long int DRIVER_DEVICE           = DRIVER_DEVICE;
%constant long int DRIVER_OP_SUCCESS       = DRIVER_OP_SUCCESS;
%constant long int DRIVER_OP_ERROR         = DRIVER_OP_ERROR;
%constant long int DRIVER_OP_UNSUPPORTED   = DRIVER_OP_UNSUPPORTED;
%constant long int DRIVER_OP_UNINIT        = DRIVER_OP_UNINIT;
%constant long int DRIVER_OP_NOT_PERMITTED = DRIVER_OP_NOT_PERMITTED;
%constant long int DRIVER_OP_BAD_PARAMETER = DRIVER_OP_BAD_PARAMETER;
%constant long int DRIVER_OP_BAD_POINTER   = DRIVER_OP_BAD_POINTER;
%constant long int DRIVER_OP_NO_DRIVER     = DRIVER_OP_NO_DRIVER;

// track.h
%constant long int CDROM_LEADOUT_TRACK = CDIO_CDROM_LEADOUT_TRACK;
%constant long int INVALID_TRACK       = CDIO_INVALID_TRACK;

// types.h
%constant long int INVALID_LBA = CDIO_INVALID_LBA;
%constant long int INVALID_LSN = CDIO_INVALID_LSN;

void cdio_destroy(CdIo_t *p_cdio);
