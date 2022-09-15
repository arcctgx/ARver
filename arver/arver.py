"""
Verify the set of WAV files ripped from CD.
"""

import sys

from arver.rip.rip import Rip


def main():
    print(Rip(sys.argv[1:]))


if __name__ == '__main__':
    main()
