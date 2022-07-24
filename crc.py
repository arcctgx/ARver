#!/usr/bin/env python3

"""
Calculate CRC of a WAV file. The result is compatible with
file checksums reported by Whipper and EAC ("Copy CRC").
"""

import binascii
import os
import sys
import wave


def _calculate_crc(wav_file):
    if not os.path.isfile(wav_file):
        return None

    try:
        with wave.open(wav_file) as wav:
            nframes = wav.getnframes()
            data = wav.readframes(nframes)
            crc = binascii.crc32(data) & 0xffffffff
            return f'{crc:08X}'
    except wave.Error:
        return None


def main():
    if len(sys.argv) == 1:
        print(f'usage: {os.path.basename(sys.argv[0])} <file.wav> [file2.wav] ...')
        sys.exit(1)

    for path in sys.argv[1:]:
        fname = os.path.basename(path)
        crc = _calculate_crc(path)
        if crc is None:
            print(f'{fname}: ERROR: failed to calculate CRC!')
        else:
            print(f'{fname}: {crc}')


if __name__ == '__main__':
    main()
