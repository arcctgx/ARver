# TODO list

## Must have in `v1.0.0`

- [x] read TOC from physical CD
- [x] read TOC from DiscID
- [x] calculate FreeDB CD indentifier
- [x] calculate AccurateRip CD identifiers
- [x] calculate AccurateRip checksums of ripped files (WAV and FLAC)
- [x] fetch AccurateRip results from database
- [x] parse AccurateRip binary data format
- [x] compare database checksums with file checksums
- [x] Audio CD support
- [x] Enhanced CD support
- [x] README.md (with acknowledgements)
- [ ] proper Python package (pip-installable, with wheels)

## Nice to have (in no particular order)

- [ ] Mixed Mode CD support
- [x] parser for cached AccurateRip response binary files
- [x] show copy CRC of ripped files in results
- [ ] calculate copy CRC with or without zero samples
- [ ] full FLAC support (audio file properties + CRC calculation)
- [ ] warn if lengths of ripped tracks don't match CD TOC
- [ ] create log file with results
- [ ] offset detection
- [ ] write-up of all I learned about CDs and AccurateRip
