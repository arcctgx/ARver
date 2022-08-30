"""Python wrapper for checksum C extension."""

from arver.checksums.accuraterip import compute

def accuraterip_checksums(wav_file, track_no, total_tracks):
    """
    Calculate AccurateRip v1 and v2 checksums of specified file.
    WAV and FLAC formats are supported.

    The track_no and total_tracks arguments are used to recognize
    if the track is the first or the last one on CD. These two
    tracks are treated specially by AccurateRip checksum algorithm.

    Return a pair of checksums (v1, v2) as unsigned integers.
    """
    return compute(wav_file, track_no, total_tracks)
