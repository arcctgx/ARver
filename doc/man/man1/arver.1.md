% ARVER(1)

# NAME

arver - Verify audio tracks ripped from a CD against AccurateRip database

# SYNOPSIS

`arver [-h] [-d device_path | -i disc_id | -t] [-1] [-p] [-x pattern] [-P frames] [-D frames] [-v] file [file ...]`

# DESCRIPTION

`arver` is a command-line program for verifying audio tracks ripped
from a CD against checksums stored in the AccurateRip database.

The idea behind AccurateRip verification is that it's virtually
impossible to get exact same errors when ripping different copies of the
same CD on various CD drives. If the copies are scratched or otherwise
degraded, read errors will occur in different disc sectors. CD drive
defects are unlikely to manifest in the same way on different machines.
Essentially, all read errors are expected to be unique, but in the
absence of errors only a single correct result exists. AccurateRip
database stores track checksums submitted by multiple users. When many
users rip the same disc without errors, correct checksums are submitted
to the database repeatably, boosting their "confidence" statistic. If
a checksum of a ripped track is not found in the database, it indicates
that the result is unique, meaning that disc read errors likely occurred
while ripping.

`arver` calculates AccurateRip checksums for local files, fetches
checksums for a given CD from the database, and compares them.

The Disc Table of Contents (TOC) necessary for AccurateRip lookup can be
obtained in three ways:

* Reading a physical CD in the drive (default and recommended if the
  disc contains data tracks).

* Querying the MusicBrainz database using a disc ID.

* Estimating from the lengths of the provided audio tracks.

WAV and FLAC audio formats are supported.

By default, files named `track00.cdda.wav`, `track00.wav`,
`track00.cdda.flac`, or `track00.flac` are assumed to be pregap tracks and
are filtered out.

# OPTIONS

* `-y`, `--yes`
: Assume "yes" to all queries.

* `-d path`, `--drive=path`
: Read disc TOC from a CD in the specified drive (e.g. /dev/sr0).

**-i discid, \--disc-id=discid**

:   Get disc TOC from MusicBrainz by disc ID query.

**-t, \--track-lengths**

:   Derive disc TOC from the lengths of audio tracks.

The options -d, -i, and -t are mutually exclusive.

**-p, \--permissive**

:   Ignore mismatched track lengths.

**-x pattern, \--exclude=pattern**

:   Exclude files matching the specified pattern. Can be used multiple
    times.

**-1, \--use-arv1**

:   Use only AccurateRip version 1 (ARv1) checksums for verification.

**-P sectors, \--pregap-length=sectors**

:   Specify the length of track one pregap in CDDA sectors (default: 0).
    This is only used with `-t/--track-lengths` option.

**-D sectors, \--data-length=sectors**

:   Specify the length of Enhanced CD data track in CDDA sectors (default: 0).
    This is only used with `-t/--track-lengths` option.

**-v, \--version**

:   Show program version and exit.

# USAGE NOTES

Audio files must be corrected for CD drive read offset (e.g., using the
`-O` option in `cdparanoia`). AccurateRip verification requires
correctly offset-corrected files; otherwise, the checksums will not
match database entries, and all tracks will fail verification.

Some discs contain audio content hidden in the pregap of track one. Many
CD rippers (e.g., `EAC` or `cdparanoia`) can detect and extract it,
but AccurateRip does not store checksums for these tracks. `arver`
will detect track one pregap and display it in the CD TOC summary. If
the ripper extracted the pregap track, do not include it in the file
list; otherwise, it will disrupt track sequencing and cause verification
errors. Use the `-x` or `--exclude` option to ignore pregap tracks.

AccurateRip database does not store checksums of last audio tracks in
Mixed Mode CDs. These tracks cannot be verified and their verification
status will always show as `N/A` in the results summary.

## VERIFICATION WITHOUT A PHYSICAL DISC

The regular use case of `arver` is to verify a set of audio files
right after they have been ripped, while the CD they have been ripped
from is still in the drive.

Commands `arver` and `arver-discinfo` support an alternative mode of
operation, where disc information is downloaded from MusicBrainz by disc
ID lookup. While this can be useful, it is reliable only for Audio CDs.
Information about data tracks is not encoded in MusicBrainz disc ID, but
it is necessary to calculate AccurateRip disc ID. Attempts to verify
discs with data tracks (Enhanced or Mixed Mode CDs) using disc ID lookup
may not work at all, result in false negatives, or low confidence
values.

`arver` can try to guess the disc TOC based on the lengths of provided
audio files with `-t/--track-lengths` option. This is considered expert
usage: there is no way to know that files were ripped from a CD
containing a pregap track or a data track, but it affects disc ID
calculation. Options `-D/--data-length` and `-P/--pregap-length` can be
used to provide this information if it is known from another source.
Note that the lengths must be specified exactly: even an off-by-one
mistake will result in a different (and probably wrong) disc ID. If the
data track length is provided, `arver` will calculate the disc ID as
if it was an Enhanced CD. Verifying Mixed Mode CDs this way is not
supported.

# EXAMPLES

Verify audio files against AccurateRip:

```text
arver *.wav
```

Specify a non-default CD drive:

```text
arver -d /dev/cdrom1 *.wav
```

Use MusicBrainz disc ID lookup:

```text
arver -i dUmct3Sk4dAt1a98qUKYKC0ZjYU- *.wav
```

# AUTHOR

Me.

# SEE ALSO

cdparanoia(1)

# BUGS

Probably.
