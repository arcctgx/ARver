"""
Function for calculating AccurateRip disc IDs.
"""

def calculate_ids(offsets, leadout):
    """
    Calculate two AccureteRip disc IDs from CD TOC. Return a pair of
    disc IDs as 8-digit hex strings.

    The calculation is based on LBA offsets: lead-in is not taken into
    account. The TOC passed as argument is not based on LBA, so it must
    be adjusted by subtracting 150 sectors from all offsets.

    TODO make sure CDs with data tracks are handled correctly.
    """
    shift = 150
    lba_offsets = [offset - shift for offset in offsets]
    lba_leadout = leadout - shift

    id1 = 0
    id2 = 0

    for track_num, offset in enumerate(lba_offsets, start=1):
        id1 += offset
        id2 += (offset or 1)*track_num

    id1 += lba_leadout
    id2 += lba_leadout*(len(lba_offsets) + 1)

    id1 &= 0xffffffff
    id2 &= 0xffffffff

    return f'{id1:08x}', f'{id2:08x}'
