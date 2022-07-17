"""
Function for calculating AccurateRip disc IDs.
"""

def calculate_ids(toc):
    """
    Calculate two AccureteRip disc IDs from CD TOC. Returns a pair of
    disc IDs as 8-digit hex strings.

    The calculation is based on LBA offsets: lead-in is not taken into
    account, the offset of the first track is zero. The TOC passed as
    argument in not based on LBA, so it must be adjusted by subtracting
    the offset of the first track from all offsets.

    TODO make sure CDs with data tracks are handled correctly.
    """
    shift = toc['offset-list'][0]
    lba_offsets = [offset - shift for offset in toc['offset-list']]
    lba_leadout_offset = toc['sectors'] - shift

    arid1 = 0
    arid2 = 0

    for track_num, offset in enumerate(lba_offsets, start=1):
        arid1 += offset
        arid2 += (offset or 1)*track_num

    arid1 += lba_leadout_offset
    arid2 += lba_leadout_offset*(len(lba_offsets) + 1)

    arid1 &= 0xffffffff
    arid2 &= 0xffffffff

    return f'{arid1:08x}', f'{arid2:08x}'
