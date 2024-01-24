# Data track handling in AccurateRip disc ID calculation

Data tracks present in enhanced and mixed mode CDs require special treatment
during calculation of AccurateRip disc IDs. While mixed mode CDs are not
popular anymore, enhanced CDs are still widespread.

To figure out how to deal with this problem I ripped several CDs of different
types using various AccurateRip-aware programs, and compared the results I got.
I consider `dBpoweramp` to be the reference implementation: it was created by
the same entity which operates AccurateRip database.

AccurateRip database lookup is based on a disc fingerprint of the following
format: `nnn-aaaaaaaa-bbbbbbbb-ffffffff`. The fields are:

* `nnn`: number of tracks on CD (decimal),
* `aaaaaaaa` and `bbbbbbbb`: two types of AccurateRip disc IDs (hex),
* `ffffffff`: [FreeDB disc ID] (hex).

All fields are padded with zeros if they would be shorter than 3 or 8 digits.
The three types of disc IDs are calculated based on the CD table of contents
(TOC).

## Enhanced CD (Blue Book)

Let's use "Liquid" by Recoil as an example. It has 10 audio tracks followed by
one data track.

Calculated full AccurateRip disc IDs are:

* `010-00164419-00b9f6e2-9e11600b` (calculated by `dBpoweramp` and `EAC` - correct)
* `010-00154c2f-00af4fd4-890e120a` (calculated by `Whipper` and `ARver` prior to `v0.5.0` - wrong!)

Only the number of tracks (`010`) is the same, all three disc IDs are different.
`dBpoweramp` and `EAC` verify the checksums of my ripped files correctly, but
`Whipper` and old `ARver` versions do not (I get no matching checksums).

`dBpoweramp` is developed by the same entity that operates AccurateRip database,
so its results can be considered authoritative. Actually it is interesting that
`Whipper` and old `ARver` versions get any AccurateRip results at all, instead
of a 404 error.

### Disc data

MusicBrainz provides the following information about the disc:

* MB Disc ID: `9AQWqQ0eCCwktwPPrIUIYkUw2Uo-`
* FreeDB disc ID: `890e120a`

```text
          start          length              end
      time     sect   time    sect      time     sect

 1    0:02      150   2:48   12617      2:50    12767
 2    2:50    12767   6:10   27720      9:00    40487
 3    9:00    40487   5:03   22738     14:03    63225
 4   14:03    63225   6:42   30185     20:45    93410
 5   20:45    93410   5:29   24705     26:15   118115
 6   26:15   118115   7:30   33750     33:45   151865
 7   33:45   151865   7:13   32475     40:58   184340
 8   40:58   184340   6:52   30920     47:50   215260
 9   47:50   215260   7:09   32195     54:59   247455
10   54:59   247455   5:05   22880   1:00:04   270335
```

`discid` provides equivalent data from reading a physical CD:

```json
{
 "disc": {
  "id": "9AQWqQ0eCCwktwPPrIUIYkUw2Uo-",
  "sectors": "270335",
  "offset-list": [
   150,
   12767,
   40487,
   63225,
   93410,
   118115,
   151865,
   184340,
   215260,
   247455
  ],
  "offset-count": 10
 }
}
```

There is no information about a data track in MusicBrainz and `discid` output.
That information can be extracted using `pycdio`:

```text
$ ./tracks.py
CD-ROM /dev/sr0 has 11 track(s) and 281585 session(s).
Track format is CD-DA.
Media Catalog Number: 0000000000000
  #: LSN     Format
  1: 000000  00:02:00 audio
  2: 012617  02:50:17 audio
  3: 040337  08:59:62 audio
  4: 063075  14:03:00 audio
  5: 093260  20:45:35 audio
  6: 117965  26:14:65 audio
  7: 151715  33:44:65 audio
  8: 184190  40:57:65 audio
  9: 215110  47:50:10 audio
 10: 247305  54:59:30 audio
 11: 281585  62:36:35 data
 AA: 333651  leadout
```

(`tracks.py` is a sample program distributed with `pycdio`. Note that LSN
rather than LBA is shown in the output, so add `150` sectors to convert
from LSN to LBA.)

### Analysis

Let's examine FreeDB disc IDs first, as they are easiest to understand. The
format of FreeDB disc ID is `XXSSSSTT` where `XX` is a checksum, `SSSS` is the
total number of seconds on the disc, and `TT` is the number of tracks on CD,
all in hexadecimal. Let's break these two FreeDB disc IDs down:

```text
     XX SSSS TT
MB:  89 0e12 0a (0a = 10 tracks)
EAC: 9e 1160 0b (0b = 11 tracks!)
```

The total CD length is 1h 00m 04s = 3604 s (3602 s excluding lead in).

* MB length (sec): `0e12` hex = `3602` dec
* EAC length (sec): `1160` hex = `4448` dec

delta = 4448 s - 3602 s = 846 s

Where does this 846 seconds difference come from? The data track is offset
from the end of last audio track by the usual `11400` sectors (152 seconds,
or `2:32.00`). The data track is 333651 - 281585 = 52066 sectors long (694
seconds and 16 sectors, or `11:34.16`).

152 s + 694 s = 846 s

So it appears one must know the length of data track to calculate AccurateRip
disc ID of an enhanced CD. `discid` doesn't provide this, and MusicBrainz disc
ID does not encode this information. This means it is not possible to calculate
AccurateRip disc ID just from MusicBrainz disc ID. Reading a physical CD with
`pycdio` is necessary. :(

### Examples

The following examples demonstrate that it is possible to calculate correct disc
IDs by using correct input data. No changes are necessary in functions which
perform the calculations. `freedb_id()` and `accuraterip_ids()` are internal
`ARver` functions.

`lba_offsets` are LBA offsets of *audio* tracks. `sectors` is the LBA of the
first sector following the last audio track. In a regular CDDA disc this is
equivalent to the lead out offset. But this is *not* the lead out offset when
another session follows audio tracks!

`lba_offsets` and `sectors` are acquired by reading a physical CD using `discid`,
or from MusicBrainz based on disc ID.

`true_leadout` is the LBA offset of track `0xAA` (170). This offset, along with
the information about existence of data tracks, can be acquired by reading a
physical CD using `pycdio`.

The numbers in examples follow the data from "Disc data" section above, with
LSN offsets reported by `pycdio` converted to LBA (LBA = LSN + 150).

#### FreeDB disc ID

This is what the calculation looks like if we are not aware of the data track:

```python
>>> from arver.disc.fingerprint import freedb_id
>>> lba_offsets = [150, 12767, 40487, 63225, 93410, 118115, 151865, 184340, 215260, 247455]
>>> sectors = 270335
>>> freedb_id(lba_offsets, sectors)
'890e120a'  # same as MusicBrainz or Whipper - NOK
```

We can obtain the correct result only if we know that there is a data track
and we know its offset (taking into account the usual `11400` sectors gap
after the last audio track). We must also know the true lead out offset:

```python
>>> from arver.disc.fingerprint import freedb_id
>>> lba_offsets = [150, 12767, 40487, 63225, 93410, 118115, 151865, 184340, 215260, 247455, 281735]
>>> true_leadout = 333801
>>> freedb_id(lba_offsets, true_leadout)
'9e11600b'  # same as EAC - OK
```

#### AccurateRip disc IDs

AccurateRip ID calculation requires knowing the true lead out offset too:

```python
>>> from arver.disc.fingerprint import accuraterip_ids
>>> lba_offsets = [150, 12767, 40487, 63225, 93410, 118115, 151865, 184340, 215260, 247455]
>>> sectors = 270335
>>> accuraterip_ids(lba_offsets, sectors)
('00154c2f', '00af4fd4')    # same as Whipper - NOK
```

Specifying the true lead out offset corrects the calculated AccurateRip disc
IDs of an enhanced CD. No manipulation of offset list is necessary:

```python
>>> from arver.disc.fingerprint import accuraterip_ids
>>> lba_offsets = [150, 12767, 40487, 63225, 93410, 118115, 151865, 184340, 215260, 247455]
>>> true_leadout = 333801
>>> accuraterip_ids(lba_offsets, true_leadout)
('00164419', '00b9f6e2')    # same as EAC - OK
```

## Mixed mode CD (Yellow Book)

Let's use "Mortal Kombat Trilogy" game CD as an example. It contains 29 tracks:
the first one is the game data, the rest are audio tracks.

The AccurateRip disc ID calculated by EAC is `028-00517a54-05a845d2-af0da31d`.
One can immediately see that the initial number in the disc ID is the number
of *audio* tracks, not the total number of tracks.

Calculation of FreeDB disc ID requires offsets of all tracks, regardless of
their type. `discid` is able to provide them for mixed mode CDs, because the
data track and audio tracks share the same CD session. Lead out offset is
correct too, because there is just one session and the last audio track is
not followed by a data track. This means that the FreeDB disc ID can be
calculated based on the data provided by `discid` alone.

```python
>>> offsets = [150, 66728, 76502, 85963, 93760, 104048, 116066, 124743, 134206, 142916, 151852, 160720,
...     169425, 178731, 188459, 196711, 206354, 214845, 223686, 225746, 226384, 232668, 239447, 239931,
...     244989, 254264, 260066, 261222, 261674]
>>> leadout = 261976
>>> freedb_id(offsets, leadout)
'af0da31d'     # same as EAC - OK
```

The tricky part is the calculation of AccurateRip disc IDs. Using the same data
as above results in one of the two fingerprints being incorrect:

```python
>>> accuraterip_ids(offsets, leadout)
('00517a54', '05f9c027')      # 00517a54 is OK, 05f9c027 is not
```

But, taking into account that the number in the beginning of the full AR disc
ID is the number of audio tracks, what if we omit the data track's offset in
the calculation?

```python
>>> accuraterip_ids(offsets[1:], leadout)
('00517a54', '05a845d2')      # both are correct now
```

So it seems that the offset list must not include the data tracks. Therefore,
correct handling of mixed mode CDs requires information that `discid` cannot
provide. `pycdio` must be used to determine which tracks are data tracks. Once
this is known, it becomes possible to filter out offsets of data tracks.

### Sample AccurateRip response for a Yellow Book CD

As indicated above, MK Trilogy CD contains 28 audio tracks. AccurateRip response
for that CD is following:

```text
disc ID: 028-00517a54-05a845d2-af0da31d
track  1:   00000000   (confidence: 0)
track  2:   f7372315   (confidence: 1)
track  3:   953b5f00   (confidence: 1)
track  4:   7cc9a20d   (confidence: 1)
track  5:   83f58407   (confidence: 1)
track  6:   33754ce7   (confidence: 1)
track  7:   efe4fc28   (confidence: 1)
track  8:   bd1fe2a7   (confidence: 1)
track  9:   a1ff10c6   (confidence: 1)
track 10:   a84d3b16   (confidence: 1)
track 11:   00a31f62   (confidence: 1)
track 12:   4c856e88   (confidence: 1)
track 13:   ec88131e   (confidence: 1)
track 14:   7e72262f   (confidence: 1)
track 15:   5c5b588f   (confidence: 1)
track 16:   62a24ed2   (confidence: 1)
track 17:   bc6ef90f   (confidence: 1)
track 18:   026de5e6   (confidence: 1)
track 19:   982fddd8   (confidence: 1)
track 20:   2a2734ed   (confidence: 1)
track 21:   4dabe6e0   (confidence: 1)
track 22:   0083e0c8   (confidence: 1)
track 23:   00000000   (confidence: 0)
track 24:   060d3d73   (confidence: 1)
track 25:   75c6048b   (confidence: 1)
track 26:   dd6ee61a   (confidence: 1)
track 27:   e5ecb215   (confidence: 1)
track 28:   00000000   (confidence: 0)
```

Note that the first track has checksum `00000000` with zero confidence. This
corresponds to CD track 1, i.e. the *data track*! Since AccurateRip response
only contains 28 tracks, it means that the checksum of one audio track is
not included. Indeed, there is no checksum of the final audio track. This
seems to be a limitation of AccurateRip database and there is nothing `ARver`
can do to work around it.

Also note that some *audio* tracks have zero checksums with zero confidences
as well. This is because they are too short: apparently AccurateRip provides a
checksum only if the track length exceeds some threshold.

[FreeDB disc ID]: <https://en.wikipedia.org/wiki/CDDB#Example_calculation_of_a_CDDB1_(FreeDB)_disc_ID>
