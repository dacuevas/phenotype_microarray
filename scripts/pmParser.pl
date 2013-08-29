#!/usr/bin/perl

use warnings;
use strict;
use Date::Parse;
use File::Basename;
use Getopt::Long;


################################################
## Subroutines
################################################

###
# Printout when command line arguments are incorrect
###
sub usage {
    my $msg = shift;
    my $filepath = basename($0);
    print "ERROR: $msg\n\n" if $msg;
    print << "END"
USAGE
    perl $filepath [Options] <PM_file.txt OR PM_directory>

REQUIRED
    -f, --files "Data file list"    : Comma-separated list of data files
               OR
    -d, --dir "Data directory"      : Directory containing data files
                                      (Given preference over -f)

OPTIONS
    -p, --plate "platePath.txt"     : Plate filepath
    -r, --reps                      : Replicate flag
    -?, -h, --help                  : This usage message

NOTES
    FILE NAME FORMATS:
        When using replicates be sure to have the file name in the format,

        <Clone Name>_<Replicate Letter>_<other text>.txt
        Regex used:    <Clone Name> -- [A-Za-z0-9-.]+
                       <Replicate Letter> -- [A-Za-z]+

        When replicates are not indicated,
        <Clone Name>_<other text>.txt
        Regex used:    <Clone Name> -- [A-Za-z0-9-.]+

END
;
    exit(1);
}


###
# Error message output and exit
###
sub error {
    my $msg = shift;
    print STDERR "ERROR: $msg\n";
    exit(2);
}


###
# Input is array of file paths. Files are checked for existence
###
sub checkFiles {
    my $files = shift;
    foreach( @$files ) {
        return 0 if ! -e $_;
    }
    return 1;
}


###
# Input is the file path to the plate file. Plate information is stored
# (and returned) as a hash-reference object
###
sub readPlate {
    my $file = shift;
    open(FILE,"<$file") or die "Couldn't open $file for reading.\n";
    my $plate = {};
    while( <FILE> ) {
        chomp;
        my ($well, $source, $media, $conc) = split /\t/;
        $plate->{$well} = [$source, $media, $conc];
    }
    return $plate;
}


###
#
###
sub readData {
    my ($file, $data, $reps) = @_;
    my ($name, $rep);
    my $fname = basename($file);

    # Grab name (and replicate if applicable)
    if( $reps ) {
        ($name, $rep) = $fname =~ /^([A-Za-z0-9-.]+)_([A-Za-z]+)/;
    }
    else {
        ($name) = $fname =~ /^([A-Za-z0-9-.]+)/;
        $rep = 1;
    }

    # Check that the name and replicate variables are defined
    ! defined $name && ! defined $rep : &error("Could not extract name (and replicate) from $fle") ?
                        ! defined $name : &error("Could not extract name from $file") ?
                        ! defined $rep : &error("Could not extract replicate from $file") ? 1;

    # Begin data extraction
    open(FILE,"<$file") or die "Couldn't open $file for reading\n";

    my ($prevTime, $diffTime);
    while( <FILE> ) {
        chomp;
        # Find time point
        if( /(\d.*?\s.{11})\s+/ ) {
            if( ! defined $prevTime ) {
                $prevTime = str2time($1);
                $diffTime = 0.0;
            }
            else {
                $diffTime = ($prevTime - str2time($1)) / 3600;
            }
        }
        elsif( /(\w\d+)\s+([0-9.]+)/ ) {
            # Well = $1
            # Data = $2
            $data->{$name}->{$currTime}->{$1} = $2;
        }
    }
}

###################################################
## ARGUMENT PARSING
###################################################

my $opts = {
                    "files"    =>   "",
                    "dir"      =>   "",
                    "plate"    =>   "",
                    "reps"     =>   "",
                    "help"     =>   ""
};

GetOptions(
                    "f=s"      =>   \$opts->{"files"},
                    "files=s"  =>   \$opts->{"files"},
                    "d=s"      =>   \$opts->{"dir"},
                    "dir=s"    =>   \$opts->{"dir"},
                    "p=s"      =>   \$opts->{"plate"},
                    "plate=s"  =>   \$opts->{"plate"},
                    "r"        =>   \$opts->{"reps"},
                    "reps"     =>   \$opts->{"reps"},
                    "h"        =>   \$opts->{"help"},
                    "help"     =>   \$opts->{"help"}
);

&usage("") if $opts->{"help"} ||
            ( !$opts->{"files"} && !$opts->{"dir"} );


#####################################################
## Check if data files exist
#####################################################
my @filepaths = [];
if( $opts->{"files"} ) {
    @filepaths = split(",", $opts->{"files"});
}
# Check if directory exists and is not empty
else {
    &usage("Data directory does not exist") unless ! $opts->{"dir"} || -e  $opts->{"dir"};
    opendir(DIR, $opts->{"dir"}) or &usage("Couldn't open $opts->{'dir'} to read files");
    while( my $f = readdir(DIR) ) {
        next if $f =~ m/^\./;
        push(@filepaths, "$opts->{'dir'}/$f");
    }
    # Check if directory was empty
    &usage("Directory empty given") if $#filepaths == 0;
}
&checkFiles(\@filepaths) || &usage("File(s) does not exist");

# Check if plate file exists
my $plate;
if( $opts->{"plate"} ) {
    if( -e $opts->{"plate"} ) {
        $plate = &readPlate($opts->{"plate"});
    }
    else {
        &usage("Plate file does not exist");
    }
}


######################################################
## Data extraction process
######################################################
my $data = {};
