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

## Pressing offset

TODO

---

[1] A CDDA sector can also be called a "frame", but I'll avoid using that name
here because of ambiguity.
