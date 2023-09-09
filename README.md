# ARver

`ARver` is a command-line program for verifying audio tracks ripped from a CD
against checksums stored in AccurateRip database.

The idea behind AccurateRip verification is that it's virtually impossible to
get exact same errors when ripping different copies of the same CD on various
CD drives. If the copies are scratched or otherwise degraded, read errors will
occur in different disc sectors. CD drive defects are unlikely to manifest in
the same way on different machines. Essentially, all read errors are expected
to be unique, but in absence of errors only a single correct result exists.

AccurateRip database stores track checksums submitted by multiple users. When
many users rip the same disc without errors, same checksums are submitted to
the database repeatably, boosting their "confidence" statistic. If a checksum
of a ripped track is not found in the database, it indicates that the track has
not been ripped correctly. Since the result is unique, disc read errors likely
occurred while ripping.

`ARver` calculates the AccurateRip checksums of local files, fetches checksums
for a given CD from the database, and displays a report which compares them.

## Features

TODO

## Restrictions

### Using MusicBrainz disc IDs instead of physical discs

The regular use case of ARver is to verify a set of audio files just after they
have been ripped, while the CD they have been ripped from is still in the drive.

Commands `arver` and `arver-discinfo` support an alternative mode of operation,
where disc information is downloaded from MusicBrainz by disc ID lookup. While
this can be useful, it is reliable only for Audio CDs. Information about data
tracks is not encoded in MusicBrainz disc ID, but it is necessary to calculate
AccurateRip disc ID. Attempts to verify discs with data tracks (e.g. Enhanced
CDs) using disc ID lookup may not work at all, result in false negatives or low
confidence values.

### Verifying Copy Controlled CDs

Copy Controlled CDs were designed specifically to prevent ripping. The way it
is achieved makes these discs more sensitive to normal wear, and makes them
not compliant with Red Book standard. Such CDs can often be ripped, but are
more likely to produce errors.

ARver is unable to distinguish these discs from regular Enhanced CDs. If your
disc bears "Copy Controlled CD" logo, verification problems are expected.

## Installation

TODO

## Usage example

The following example demonstrates the typical use case of ARver: verification
of files just ripped from a CD.

![ARver usage example](doc/arver_usage.gif)

The tracks have been ripped using `cdparanoia` prior to running `arver`.
AccurateRip disc ID is calculated based on the TOC of the CD which still is
in the drive. `arver` fetches the checksums from the database, and compares
checksums of local files with database entries.

In this case `arver` found that the last track was not ripped correctly, and
reports an error. The CD is affected by [disc rot], and `cdparanoia` reported
multiple issues toward the end of the third track.

## Acknowledgements

AccurateRip database is (c) Illustrate. Used with permission.

[disc rot]: https://en.wikipedia.org/wiki/Disc_rot
