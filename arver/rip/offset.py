"""ARver offset detection module."""

from collections import OrderedDict

from arver.audio.checksums import get_frame450_checksums
from arver.disc.info import DiscInfo
from arver.rip.rip import Rip


def find_pressing_offset(disc: DiscInfo, rip: Rip) -> None:
    """Offset detection starts here."""

    disc_frame450_checksums = disc.accuraterip_data.make_dict(frame450=True)

    results = OrderedDict()

    for num, track in enumerate(rip.tracks, start=1):
        print(f'Looking for offsets in {track.path}')

        # raw is a list of (offset, checksum) pairs. Convert it to a dict
        # {checksum: offset} so it's more convenient to work with. Omit all
        # zero checksums (either real silent samples or calculation errors).
        raw = get_frame450_checksums(track.path)
        offsets = {checksum: offset for (offset, checksum) in raw if checksum != 0}

        track_checksums = disc_frame450_checksums[num]

        for checksum, meta in track_checksums.items():
            # Many responses contain frame 450 checksums equal to zero.
            # This can only mean "no data", so ignore these checksums.
            if checksum == 0:
                continue

            try:
                off = offsets[checksum]
                conf = meta['confidence']
                #print(f'Possible pressing offset: {off:+5d} (confidence: {conf})')

                results.setdefault(off, {'max_conf': 0, 'tracks': 0})
                results[off]['tracks'] += 1
                results[off]['max_conf'] = max(results[off]['max_conf'], conf)

            except KeyError:
                pass

    # TODO: remove outliers
    print()
    print('Possible pressing offsets:')
    print()
    print('offset    tracks    conf')
    print('------    ------    ----')
    for offset, info in results.items():
        print(f'{offset:+6d}    {info["tracks"]:6d}    {info["max_conf"]:4d}')