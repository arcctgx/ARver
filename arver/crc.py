"""
Calculate CRC of a WAV file. The result is compatible with
file checksums reported by Whipper and EAC ("Copy CRC").
"""

import os
import sys

from arver.checksum import checksum

def main():
    if len(sys.argv) == 1:
        print(f'usage: {os.path.basename(sys.argv[0])} <file.wav> [file2.wav] ...')
        sys.exit(1)

    for path in sys.argv[1:]:
        fname = os.path.basename(path)
        crc = checksum.copy_crc(path)
        if crc is None:
            print(f'{fname}: ERROR: failed to calculate CRC!')
        else:
            print(f'{fname}: {crc:08x}')


if __name__ == '__main__':
    main()
