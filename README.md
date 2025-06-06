# ARver

[![Unit tests](https://github.com/arcctgx/ARver/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/arcctgx/ARver/actions/workflows/unit-tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/ARver?logo=python&label=PyPI)](https://pypi.org/project/ARver/)
[![PePy downloads](https://img.shields.io/pepy/dt/ARver?logo=python&label=Downloads&color=%230C7DBE)](https://pepy.tech/project/ARver)

`ARver` is a command-line program for verifying audio tracks ripped from a CD
against checksums stored in AccurateRip database.

The idea behind AccurateRip verification is that it's virtually impossible to
get exact same errors when ripping different copies of the same CD on various
CD drives. If the copies are scratched or otherwise degraded, read errors will
occur in different disc sectors. CD drive defects are unlikely to manifest in
the same way on different machines. Essentially, all read errors are expected
to be unique, but in absence of errors only a single correct result exists.

AccurateRip database stores track checksums submitted by multiple users. When
many users rip the same disc without errors, correct checksums are submitted to
the database repeatably, boosting their "confidence" statistic. If a checksum
of a ripped track is not found in the database, it indicates that the result is
unique, meaning that disc read errors likely occurred while ripping.

`ARver` calculates the AccurateRip checksums of local files, fetches checksums
for a given CD from the database, and displays a report which compares them.

## Features

The package provides following command-line tools:

* `arver`: the main program. It determines the AccurateRip disc ID, fetches
AccurateRip data, calculates checksums of ripped audio files, compares them
with downloaded AccurateRip data and displays the result.

* `arver-discinfo`: displays disc IDs and the Table of Contents, fetches and
displays all AccurateRip track checksums.

* `arver-ripinfo`: calculates checksums of audio files (ARv1, ARv2 and CRC32)
and presents them as a table.

* `arver-bin-parser`: parses cached binary AccurateRip response and displays
all AccurateRip track checksums.

## Usage example

This example demonstrates the typical use case of `arver`: verification of
files just ripped from a CD.

![Animated ARver usage example](https://raw.githubusercontent.com/arcctgx/arver/v1.4.0/doc/arver_usage.gif)

The tracks have been ripped using `cdparanoia` prior to running `arver`.
AccurateRip disc ID is calculated based on the TOC of the CD which still is
in the drive. `arver` fetches the checksums from the database, and compares
checksums of local files with database entries.

In this case `arver` found that the third track was not ripped correctly, and
reports a verification failure. The disc used for this example is affected by
[CD bronzing], and `cdparanoia` reported multiple issues toward the end of the
last track.

## Installation

For typical use:

```sh
python3 -m pip install arver
```

`ARver` requires Python 3.7 or newer. A pre-built wheel package is available on
PyPI for `CPython` versions 3.7 and newer, targeting the `x86_64` architecture
for Linux. For other platforms installation is only supported from the source
distribution (see the "Dependencies" section below).

While the wheel is forward-compatible with future 3.x Python versions, the latest
Python releases may not have been tested. The latest tested Python version is
listed in the PyPI trove classifiers.

Use an editable installation for development and testing:

```sh
git clone https://github.com/arcctgx/ARver
cd ARver
python3 -m pip install --editable .
```

### Dependencies

`ARver` depends on following Python packages at runtime:

* `discid`
* `musicbrainzngs`
* `pycdio`
* `requests`

They will be installed automatically by `pip install` if needed. Alternatively,
one can install them using provided `requirements.txt` file.

The source code includes a `C` extension which depends on `libsndfile`, so
building from source requires a `C` compiler (`gcc`) and `libsndfile` headers.
This makes `libsndfile` both compile-time and runtime dependency when `ARver`
is installed from the source distribution.

#### Note about `pycdio` dependency

`pycdio` does not provide wheels, so if it's not already installed on your
system, `pip install arver` will attempt to build it from source. Building
from source may fail due to missing build-time dependencies. To work around
this, you can try installing `pycdio` using your Linux distribution's package
manager before installing `ARver`. If that doesn't work, you'll need to install
the build-time dependencies listed on the [pycdio GitHub page] and then retry
the installation with `pip`.

## Restrictions

### CD read offset corrections

Audio files must be corrected for [CD drive read offset] (e.g. by using `-O`
option in `cdparanoia`). This is crucial for AccurateRip verification: without
it the checksums of ripped tracks cannot be directly compared with database
entries. `ARver` expects the input files to have zero offset, i.e. it assumes
that required offset corrections were applied by the CD ripper. If this is not
the case, all tracks will be reported as failing verification.

### Hidden Track One Audio ("pregap track")

In some discs audio content is hidden in the pregap of track one. Many CD
rippers (e.g. `EAC` or `cdparanoia`) can detect and rip it. Unfortunately,
AccurateRip database does not store checksums of such tracks, so they can't
be verified.

`ARver` will detect the presence of track one pregap, and will display it in
CD TOC summary. If your ripper did extract the pregap track, do not pass its
file name as argument to `arver`. It will change the track sequence and cause
verification errors in other tracks. If you used a wildcard to specify audio
files, use `-x/--exclude` option to ignore the pregap track.

### Verifying Mixed Mode CDs

AccurateRip database does not store checksums of last audio tracks in Mixed
Mode CDs. These tracks cannot be verified and their verification status will
always show as `N/A` in the results summary.

### Verifying Copy Controlled CDs

Copy Controlled CDs were designed specifically to prevent ripping. The way it
is achieved makes these discs more sensitive to normal wear, and makes them
not compliant with CD audio standard. Such CDs can often be ripped, but are
much more likely to produce errors.

These CDs appear to `arver` and `arver-discinfo` as ordinary Enhanced CDs
(multisession with data track in the end). It is not possible to distinguish
them from normal Enhanced CDs based on the table of contents alone. If your
disc bears "Copy Controlled CD" logo, verification problems are expected.

### Verification without a physical disc

The regular use case of `ARver` is to verify a set of audio files right after
they have been ripped, while the CD they have been ripped from is still in the
drive.

Commands `arver` and `arver-discinfo` support an alternative mode of operation,
where disc information is downloaded from MusicBrainz by disc ID lookup. While
this can be useful, it is reliable only for Audio CDs. Information about data
tracks is not encoded in MusicBrainz disc ID, but it is necessary to calculate
AccurateRip disc ID. Attempts to verify discs with data tracks (Enhanced or
Mixed Mode CDs) using disc ID lookup may not work at all, result in false
negatives or low confidence values.

`arver` can try to guess the disc TOC based on the lengths of provided audio
files with `-t/--track-lengths` option. This is considered expert usage: there
is no way to know that files were ripped from a CD containing a pregap track
or a data track, but it affects disc ID calculation. Options `-D/--data-length`
and `-P/--pregap-length` can be used to provide this information if it is known
from another source. Note that the lengths must be specified exactly: even an
off-by-one mistake will result in a different (and probably wrong) disc ID.

If the data track length is provided, `arver` will calculate the disc ID as if
it was an Enhanced CD. Verifying Mixed Mode CDs this way is not supported.

## Acknowledgements

AccurateRip database is (c) Illustrate. Used with permission.

Thanks to the following people and projects for source code and inspiration:

* [leo-bogert/accuraterip-checksum]
* [whipper-team/whipper]
* [cyanreg/cyanrip]

[CD bronzing]: https://en.wikipedia.org/wiki/Compact_disc_bronzing
[pycdio GitHub page]: https://github.com/rocky/pycdio#requirements
[CD drive read offset]: http://www.accuraterip.com/driveoffsets.htm
[leo-bogert/accuraterip-checksum]: https://github.com/leo-bogert/accuraterip-checksum
[whipper-team/whipper]: https://github.com/whipper-team/whipper
[cyanreg/cyanrip]: https://github.com/cyanreg/cyanrip
