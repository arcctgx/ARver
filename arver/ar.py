"""
Calculate AccurateRip v1 and v2 checksums from WAV
files in specified directory.
"""

import glob
import os
import sys

from arver.checksums.wrapper import accuraterip_checksums


def _get_wav_files(path):
    if not os.path.isdir(path):
        print(f'Error: {path} is not a directory!')
        return []

    wav_files = glob.glob(path + '/*.wav')
    if not wav_files:
        print(f'No .wav files were found in {path}')
        return []

    # Filter out track 0 if it exists.
    wav_filtered = [wav for wav in wav_files if 'track00' not in wav]

    return sorted(wav_filtered)


def _display_checksums(wavs):
    total_tracks = len(wavs)

    for track, wav in enumerate(wavs, start=1):
        ar1, ar2 = accuraterip_checksums(wav, track, total_tracks)
        print(f'{wav}\tv1 {ar1:08x}\tv2 {ar2:08x}')


def main():
    if len(sys.argv) != 2:
        print(f'usage: {os.path.basename(sys.argv[0])} <directory>')
        sys.exit(1)

    wavs = _get_wav_files(sys.argv[1])
    if wavs:
        _display_checksums(wavs)


if __name__ == '__main__':
    main()
