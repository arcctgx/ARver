#!/usr/bin/perl

###############################################################################
#																			#
#								  ARFlac.pl								  #
#																			#
#			  KitchenStaff (Kitchen.Staff.Supervisor@gmail.com)			#
#																			#
# Many thanks to Mr. Spoon for his kind permission to use the AccurateRip	#
# technology and database.  Access to AccurateRip is regulated, see		  #
# [url=http://www.accuraterip.com/3rdparty-access.htm]http://www.accuraterip.com/3rdparty-access.htm[/url] for details.				#
#																			#
# Original ARCue script by Christopher Key <cjk32@cam.ac.uk>				  #
#																			#
# This script allows the usage of AccurateRip's extensive track checksum	  #
# database to verify the accuracy of directories of flac files. To use,	  #
# simply run:																#
#																			#
# ARFlac.pl Flacdir1 Flacdir2 etc...										  #
# Note that this is not a perfect system.  If the disc originally had a data  #
# track, this routine may not find a match.  This is also dependent on the	#
# Accurate Rip database having seen the CD a sufficient number of times.	  #
# This tool should be used to verify that a set of files is good, but not to  #
# necessarily indicate that the entire set is bad (different pressings, etc.) #
#																			#
###############################################################################

use strict;

use LWP;
use Carp;
use POSIX;

my $lwpUserAgent = LWP::UserAgent->new;

foreach my $flacDir (@ARGV) {

	# Get the list of flac files from the directory
	print $flacDir . ":";
	
	opendir CURDIR, $flacDir;
	my @flaclist = readdir CURDIR;
	closedir CURDIR;
	
	my @filelist = grep {/flac$/i} @flaclist;
	@filelist = sort @filelist;
	
	# We need track offsets in 'frames'
	# can get these from metaflac
	my (@trackOffsets,@trackLengths,@trackSamples);
	my $tn=0;
	my $tmpl=0;
	foreach my $fl (@filelist) {
	
		  $tmpl = `metaflac --show-total-samples "$flacDir/$fl"`;
		  $trackSamples[$tn] = floor($tmpl/1);
		  $trackLengths[$tn] = ceil($tmpl/588);
		  printf $trackSamples[$tn] . ":";
		  $tn++;
	}
	
	my $trackCount = $tn;
	my $curoff = 0;
	$trackOffsets[0] = 0;
	for ($tmpl = 1; $tmpl <= $trackCount; $tmpl++) {
		  $curoff += $trackLengths[$tmpl-1];
		  $trackOffsets[$tmpl] = $curoff;
	}

	# Calculate the three disc ids used by AR
	my ($discId1, $discId2, $cddbDiscId) = (0, 0, 0);

	{
		use integer;

		for (my $trackNo = 0; $trackNo <= $trackCount; $trackNo++) {
			my $trackOffset = $trackOffsets[$trackNo];

			$discId1 += $trackOffset;
			$discId2 += ($trackOffset ? $trackOffset : 1) * ($trackNo + 1);
			if ($trackNo < $trackCount) {
				$cddbDiscId = $cddbDiscId + sumDigits(int($trackOffset/75)+2);
			}
		}

		$cddbDiscId = (($cddbDiscId % 255) << 24) + ((int($trackOffsets[$trackCount]/75) - int($trackOffsets[0]/75)) << 8) + $trackCount;

		$discId1 &= 0xFFFFFFFF;
		$discId2 &= 0xFFFFFFFF;
		$cddbDiscId &= 0xFFFFFFFF;
	}

  print "\nChecking AccurateRip database\n\n";

	# See if we can find the disc in the database
	my $arUrl = sprintf("http://www.accuraterip.com/accuraterip/%.1x/%.1x/%.1x/dBAR-%.3d-%.8x-%.8x-%.8x.bin",
		$discId1 & 0xF, $discId1>>4 & 0xF, $discId1>>8 & 0xF, $trackCount, $discId1, $discId2, $cddbDiscId);

	my $arDiscNotInDb = 0;
	my $arNetworkFailed = 0;

	my $response = $lwpUserAgent->get($arUrl);
	
	if (!$response->is_success) {
		if ($response->status_line =~ m/^404/) {
			$arDiscNotInDb = 1;
		}else{
			$arNetworkFailed = $response->status_line;
		}
	}

	# Extract CRCs from response data
	my $arCrcCount = 0;
	my @arTrackConfidences = ();
	my @arTrackCRCs = ();

	if (!($arDiscNotInDb || $arNetworkFailed)) {
		my $arCrcData = $response->content;
		my $ptr = 0;

		while ($ptr < length($arCrcData)) {
			my ($chunkTrackCount, $chunkDiscId1, $chunkDiscId2, $chunkCddbDiscId);

			# Force perl to interpret these values as signed integers
			{
				use integer;

				$chunkTrackCount = unpack("c",substr($arCrcData,$ptr,1));
				$chunkDiscId1 = unpack("V",substr($arCrcData,$ptr+1,4)) + 0;
				$chunkDiscId2 = unpack("V",substr($arCrcData,$ptr+5,4)) + 0;
				$chunkCddbDiscId = unpack("V",substr($arCrcData,$ptr+9,4)) + 0;
			}

			$ptr +=13;

			if ( $chunkTrackCount != $trackCount
				|| $chunkDiscId1 != $discId1
				|| $chunkDiscId2 != $discId2
				|| $chunkCddbDiscId != $cddbDiscId ) {

				croak("Track count or Disc IDs don't match.");
			}

			# How if it flagged that a track is not in the database?
			for (my $track = 0; $track < $trackCount; $track++) {
				my ($trackConfidence, $trackCrc);

				# Force perl to interpret these values as signed integers
				{
					use integer;

					$trackConfidence = unpack("c",substr($arCrcData,$ptr,1));
					$trackCrc = unpack("V",substr($arCrcData,$ptr+1,4)) + 0;
					$ptr += 9;
				}

				if ($arCrcCount == 0){
					$arTrackConfidences[$track] = [];
					$arTrackCRCs[$track] = [];
				}

				$arTrackConfidences[$track]->[$arCrcCount] = $trackConfidence;
				$arTrackCRCs[$track]->[$arCrcCount] = $trackCrc;
			}
			$arCrcCount++;
		}
	}
	

	printf "Track\tRipping Status\t\t[Disc ID: %08x-%08x]\n", $discId1, $cddbDiscId;

	# Calculate a CRC for each track
	my $errLevel = 0;

	# Calculate a CRC for each track
	my @trackCRCs = ();
	my $FH;
	my ($accuratelyRipped, $notAccuratelyRipped, $notInDatabase) = (0, 0, 0);
	for (my $trackNo = 0; $trackNo < $trackCount; $trackNo++) {
	
		# Open a pipe to flac decode
		open($FH, "flac -d -c -f --force-raw-format --totally-silent --endian=little --sign=signed \"$flacDir/$filelist[$trackNo]\" |");
		binmode $FH;
		
		my ($frame, $CRC);
		$CRC = 0;
		  $CRC = processFile($FH, $trackLengths[$trackNo], $trackNo==0, $trackNo==$trackCount-1);
		
		close($FH);

		{
			use integer;
			$trackCRCs[$trackNo] = $CRC & 0xFFFFFFFF;
		}


		if ($arDiscNotInDb) {
			printf " %d\tTrack not present in database.	[%08x]\n",
				$trackNo + 1, $trackCRCs[$trackNo];

			$notInDatabase++;
		}	elsif ($arNetworkFailed) {
			printf " %d\t	[%08x]\n",
				$trackNo + 1, $trackCRCs[$trackNo];

		} else {

			my $foundCrc = 0;
			my $foundCrcMatch = 0;

			for (my $arCrcNo=0; $arCrcNo < $arCrcCount; $arCrcNo++) {
				if ($arTrackConfidences[$trackNo]->[$arCrcNo] != 0){
					$foundCrc = 1;

					if ($arTrackCRCs[$trackNo]->[$arCrcNo] == $trackCRCs[$trackNo]) {
						printf " %d\tAccurately Ripped	(confidence %d)	[%08x]\n",
							$trackNo + 1, $arTrackConfidences[$trackNo]->[$arCrcNo], $arTrackCRCs[$trackNo]->[$arCrcNo];

						$accuratelyRipped++;

						$foundCrcMatch = 1;
						last;
					}
				}
			}
			if (!$foundCrc) {
					printf " %d\tTrack not present in database.	[%08x]\n",
					$trackNo + 1, $trackCRCs[$trackNo];

				$notInDatabase++;
			}elsif (!$foundCrcMatch) {
				printf " %d\t** Rip not accurate **  (confidence %d)	[%08x] [%08x]\n",
					$trackNo + 1, $arTrackConfidences[$trackNo]->[0], $arTrackCRCs[$trackNo]->[0], $trackCRCs[$trackNo];

				$notAccuratelyRipped++;
			}
		}
	}

	if ($arDiscNotInDb) {
			print "Disc not present in AccurateRip database.\n";
			$errLevel = 2;
	} elsif ($arNetworkFailed) {
			print "Failed to get $arUrl : " . $arNetworkFailed . "\n";
			$errLevel = 3;
	} elsif ($accuratelyRipped == $trackCount) {
		print "All Tracks Accurately Ripped.\n";
	} else {
		if ($notAccuratelyRipped >= 3) {
			print "Your CD disc is possibly a different pressing to the one(s) stored in AccurateRip.\n"
		}

		printf "Track(s) Accurately Ripped: %d\n", $accuratelyRipped;
		printf "**** Track(s) Not Ripped Accurately: %d ****\n", $notAccuratelyRipped;
		printf "Track(s) Not in Database: %d\n", $notInDatabase;

		$errLevel = 1;
	}

	print "\n\n\n";
}

sub processFile {
	use integer;
	my ($FH, $tracklength, $firstTrack, $lastTrack) = @_;
	my ($frame,$CRC,$frameOffset,$frameNo,$sample,$endFrame,$frmloop);
	
	$CRC=0;
	
	if ($firstTrack) {
		  # Skip first 4 frames
		  if ($tracklength<=4) {
			  return 0;
		  }
		 
		  if (read($FH, $frame, 4*2352) != 4*2352) { croak ("read failed.") };
		 
		  if (read($FH, $frame, 2352) != 2352) { croak ("read failed.") };
		  $sample = unpack("V",substr($frame,2348,4));
		  $CRC += $sample;
		  $frameNo = 5;
	} else {
		  $frameNo = 0;
	}
	
	if ($lastTrack) {
		  $endFrame = $tracklength-5;
	} else {
		  $endFrame = $tracklength;
	}
	
	
	for ($frmloop=$frameNo; $frmloop<$endFrame;$frmloop++) {
	
		  if (read($FH, $frame, 2352) != 2352) { croak ("read failed.") };
		$frameOffset = $frmloop * 588;

		foreach (unpack("V588", $frame)) {
			$CRC += $_ * (++$frameOffset);
		}
	}
	
	return $CRC;
}
	
	

sub sumDigits {
	my $n = shift;
	my $r = 0;
	while ($n > 0) {
		$r = $r + ($n % 10);
		$n = int($n / 10);
	}
	return $r;
}
