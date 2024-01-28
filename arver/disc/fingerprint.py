"""Functions for calculating disc fingerprints (disc IDs) from CD TOC."""

from typing import List, Tuple

from discid import put

from arver.disc.utils import LEAD_IN_FRAMES


def freedb_id(offsets: List[int], leadout: int) -> str:
    """
    Return FreeDB disc ID as 8-digit hex string.

    The first argument is the list of LBA offsets of all tracks from all CD
    sessions, regardless of their types. Specifically, for Enhanced CDs the
    list MUST include the offset of the data track from the second session.

    Including the track from the second session is crucial. discid module
    ignores the second session when reading a physical CD, and returns a
    FreeDB ID incompatible with one used by AccurateRip database.

    The second argument is the LBA offset of the lead out track.
    """
    disc = put(1, len(offsets), leadout, offsets)
    return disc.freedb_id


def musicbrainz_id(offsets: List[int], sectors: int) -> str:
    """
    Return MusicBrainz disc ID as a string.

    The first argument is the list of LBA offsets of all tracks in the first
    CD session. This means that for Mixed Mode CDs the data track offset MUST
    be included, but in Enhanced CDs it MUST NOT, because it belongs to the
    second session. For Enhanced CDs this will effectively be the list of all
    audio track offsets, just like for regular Audio CDs.

    The second argument is the total length of the first CD session in sectors,
    including lead in. This is equivalent to LBA lead out offset in Audio and
    Mixed Mode CDs, but not in Enhanced CDs.
    """
    disc = put(1, len(offsets), sectors, offsets)
    return disc.id


def accuraterip_ids(audio_offsets: List[int], leadout: int) -> Tuple[str, str]:
    """
    Return a pair of AccurateRip disc IDs as 8-digit hex strings.

    The first argument is the list of LBA offsets of audio tracks only. In case
    of Mixed Mode and Enhanced CDs it MUST NOT contain offsets of data tracks
    from any session.

    The second argument is the LBA offset of the lead out track.

    This function is an exception because it internally works on LSN offsets.
    It accepts LBA offsets as arguments to make interfaces of all functions
    defined here consistent. LBA offsets are converted to LSN internally.
    """
    lsn_offsets = [offset - LEAD_IN_FRAMES for offset in audio_offsets]
    lsn_leadout = leadout - LEAD_IN_FRAMES

    id1 = 0
    id2 = 0

    for track_num, offset in enumerate(lsn_offsets, start=1):
        id1 += offset
        id2 += (offset or 1) * track_num

    id1 += lsn_leadout
    id2 += lsn_leadout * (len(lsn_offsets) + 1)

    id1 &= 0xffffffff
    id2 &= 0xffffffff

    return f'{id1:08x}', f'{id2:08x}'
