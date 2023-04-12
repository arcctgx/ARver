"""
Functions for calculating FreeDB and AccurateRip disc identifiers.

All functions return identifiers as hex strings, because they are
never used in any other form.
"""

from typing import Tuple

import discid

from arver.disc.utils import LEAD_IN_FRAMES

# TODO clarify usage of LBA addressing in docstrings.


def freedb_id(offsets, sectors) -> str:
    """Return FreeDB disc ID as 8-digit hex string."""
    disc = discid.put(1, len(offsets), sectors, offsets)
    return disc.freedb_id


def musicbrainz_id(offsets, sectors) -> str:
    """Return MusicBrainz Disc ID string."""
    disc = discid.put(1, len(offsets), sectors, offsets)
    return disc.id


def accuraterip_ids(offsets, leadout) -> Tuple[str, str]:
    """
    Calculate two AccureteRip disc IDs from CD TOC. Return a pair of
    disc IDs as 8-digit hex strings.

    The calculation is based on LSN offsets: lead in is not taken into
    account. The TOC passed as argument is based on LBA, so it must be
    adjusted by subtracting lead in sectors from all offsets.
    """
    lsn_offsets = [offset - LEAD_IN_FRAMES for offset in offsets]
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
