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

## Motivation

At one time I had to re-rip my entire CD collection, and I needed to check the
correctness of my rips (i.e. are `+` or `-` symbols reported by `cdparanoia`
*really* as harmless as the docs say?)

There already exist Linux CD rippers which utilize AccurateRip database to
verify the results, such as `Whipper` and `cyanrip`, but they didn't fit my
workflow too well. I needed a tool which only performs verification, so I
decided to write my own program for that purpose (and maybe went a little too
deep down the rabbit hole in the process).

## Features

TODO

## Installation

TODO

## Usage example

The following example demonstrates the typical use case of ARver: verification
of files just ripped from a CD.

[![asciicast](https://asciinema.org/a/Y2rl6KN8plN5V1rTMuzS3tuf6.svg)](https://asciinema.org/a/Y2rl6KN8plN5V1rTMuzS3tuf6)

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
