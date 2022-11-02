"""
Display properties of a set of WAV files, including copy CRCs and
two types of AccurateRip checksums.
"""

import os
import sys

from arver.rip.rip import Rip


def main():
    if len(sys.argv) < 2:
        print(f'usage: {os.path.basename(sys.argv[0])} <file> [file ...]')
        sys.exit(1)

    rip = Rip(sys.argv[1:])
    rip.calculate_checksums()
    print(rip)


if __name__ == '__main__':
    main()
