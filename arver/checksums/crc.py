#!/usr/bin/env python3

"""
Calculate CRC of a WAV file. The result is compatible with
file checksums reported by Whipper and EAC ("Copy CRC").
"""

import binascii
import wave


def copy_crc(wav_file):
    """
    Calculate copy CRC of ripped WAV file.
    Returns a hex string on success or None on error.
    """
    try:
        with wave.open(wav_file) as wav:
            nframes = wav.getnframes()
            data = wav.readframes(nframes)
            crc = binascii.crc32(data) & 0xffffffff
            return f'{crc:08X}'
    except (OSError, wave.Error):
        return None
