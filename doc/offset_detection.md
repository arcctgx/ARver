# Offset detection

## CD drive read offset

Most CD drives have non-zero _read offset_. When requested to read a CDDA
sector, they don't start reading exactly at the sector boundary. They either
start by reading a number of final bytes of the preceding sector, or start a
number of bytes into the requested sector.

CD drive read offsets are specified in _audio frames_. One stereo audio frame
consists of two 16-bit samples (left and right channel). 588 frames (2352
bytes) make one CDDA sector (exactly 1/75 second of audio). [1]

The offset can be positive or negative (rarely zero). A positive offset means
that the drive starts reading from the final frames of the preceding sector
(i.e. the ripper must read _ahead_ to correct for the read offset). At the
time of writing, the largest positive offset in the AccurateRip drive database
is +1776 frames, and the largest negative offset is -1164 frames. Positive
offsets are more common than negative ones. The offset of +6 frames is the
most common by far.

When applying a correction would mean reading samples before the first track
or after the last track (i.e. overreading into CD lead in or lead out), the
missing audio frames are assumed to contain digital silence (i.e. samples with
zero value).

The time differences caused by ignoring read offset corrections are tiny:
+1776 frames is about 10 msec, and +6 frames is 34 µsec. While not perceptible
by a human listener, shifting the audio data one way or another changes its
calculated checksum.

## Disc pressing offset

Another type of audio offset can be introduced in the CD production process.
This _pressing offset_ is often seen in later releases of the same album, when a
new batch of discs is manufactured. Like the CD drive read offset, the pressing
offset is measured in audio frames and can be positive or negative. All discs
pressed from a given master share the same pressing offset, but from the end
user perspective the offset values are unpredictable and must be detected
separately for each disc. For practical purposes, the search area is limited
to ±5 CD sectors (±2940 audio frames, so 5881 possible offsets in total).

It is important to note that a non-zero pressing offset does not change the CD
TOC. In the AccurateRip database responses corresponding to various pressing
offsets will be grouped together under a single AccurateRip disc ID, with no
indication of the offset value itself.

The process of finding the pressing offset is essentially a brute force search.
Checksums corresponding to all possible frame offsets within the search radius
are calculated for each ripped audio file. The pressing offset is only known
once a checksum corresponding to a specific offset matches a database entry.

This would be very expensive if the checksum calculation was based on an entire
CD track. To optimize the process, AccurateRip database stores two types of
checksums for each track: the full file checksum for verification, and an
offset finding checksum calculated only from audio frames in the CD sector 450.
Limiting the calculation to a single CD sector is much faster. There are some
edge cases related to handling very short CD tracks, but in practice these
cases can be avoided by not calculating the checksum if a given offset is
"impossible" for a given track. Such short tracks are rare anyway, and the
offset finding checksums can be calculated based on other tracks from the
same disc.

The key point is: when a CD track is ripped with no offset corrections applied,
the effective offset of a resulting audio file is a sum of the CD drive read
offset and of the disc pressing offset:

```text
effective offset = drive read offset + disc pressing offset
```

The effective offset can be positive or negative, depending on the actual values
of these two parameters. A special case is when the CD drive read offset and the
disc pressing offset cancel each other out, resulting in an effective offset of
zero. In such case no corrections are needed to verify the CD rip.

## Verification with zero effective offset

The disc used in this example is "Soul of a New Machine" by Fear Factory (2002
release on Metal Mind Productions, 17 tracks). My CD drive has read offset of
+6 frames, so I'm passing `-O 6` option to `cdparanoia`. Initially `arver` is
unable to verify the rip:

```text
$ arver *.wav
AccurateRip disc ID: 017-0023fef1-01bc9ce9-e50cf111
MusicBrainz disc ID: zx8jyQae9Qdn9tacl1661NmsrVo-
Disc type: Audio CD

(...)

Got 8 AccurateRip responses (max confidence: 52)

(...)

Verification of all tracks failed. Looks like your disc pressing does not exist in AccurateRip database.
```

A matching CD TOC was found in the AccurateRip database, but no checksums were
matched. When `arver` is given the `-f` switch on the command line, it will try
to detect the disc pressing offset:

```text
$ arver -f *.wav

(...)

Possible pressing offsets:

offset    tracks    conf
------    ------    ----
  -691        17      52
  +528        17      24
  +167        17      18
 -1361        17      15
    +0         1      15
  +173         1      14
```

Six possible offsets were detected. Four of them were found in all 17 tracks.
The offsets of 0 and +173 have only been found in a single track, so these
outliers may be incorrect.

The correction required to shift the ripped files to an effective zero offset
is the sum of the drive read offset and of the CD pressing offset. In this
case, the drive read offset is +6 audio frames, and to verify against the
offset corresponding to the maximum confidence, the effective correction is
`6 - 691 = -685` frames. This value must be passed to the `-O` option of
`cdparanoia`.

After ripping the disc with the offset correction of -685 frames, `arver`
reports another error when trying to verify the files:

```text
CD track 1 is 2 frames longer than "track01.cdda.wav"

Track length mismatch. Retry in permissive mode to verify anyway.
```

The first file is two CD sectors too short and will not verify correctly even
in permissive mode. The problem is that specifying a negative offset forces
`cdparanoia` to overread into the CD lead in. Because one CD sector is exactly
588 audio frames, and CD ripping requires reading full CD sectors, the offset
correction of -685 frames means the ripper must overread 2 CD sectors into the
lead in. Many CD drives are unable to do this, and the ripper will omit these
sectors from the resulting audio file.

Rippers such as EAC detect this situation and pad the resulting audio file with
digital silence, so that the length of the ripped track matches the CD TOC.
`cdparanoia` does not do this automatically, but it's relatively easy to fix
manually:

```sh
mv track01.cdda.wav track01.cdda.wav.bak
sox track01.cdda.wav.bak track01.cdda.wav pad 1176s
```

The number 1176 is two CD sectors converted to audio frames: `2*588`. The
number of CD sectors that must be padded is `abs(offset) // 588 + 1`, where
`//` operator is the integer (truncating) division.

Interestingly, positive offset corrections don't result in similar problems:
overreading into the CD lead out doesn't appear to be an issue and the length
of the last ripped track matches the CD TOC. This likely depends on the CD
drive, so your mileage may vary.

After correcting the first track `arver` successfully verifies all tracks, with
the majority having the confidence of 52 (the maximum available for this disc).
Yay!

Finally, another attempt to detect offsets shows that the audio files were
shifted to an effective offset of zero. Note that the remaining offset values
have changed accordingly:

```text
$ arver -f *.wav

(...)

Possible pressing offsets:

offset    tracks    conf
------    ------    ----
    +0        17      52
 +1219        17      24
  +858        17      18
  -670        17      15
  +691         1      15
  +864         1      14
```

---

[1] A CDDA sector can also be called a "frame", but I'll avoid using that name
here because of ambiguity.
