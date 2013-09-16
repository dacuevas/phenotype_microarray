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
    --columnorder                   : Print out in column order (PM analysis) (In development)
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
        my ($well, $mainSource, $substrate, $conc) = split /\t/;
        $plate->{$well} = { main_source => $mainSource,
                            substrate  => $substrate,
                            conc   => $conc
        };
    }
    return $plate;
}


###
# Input is the file path to the PM analyst file. Data is stored in the
# data hash-reference object
###
sub readData {
    ###my $file = shift; my $data = shift; my $reps = shift;
    ###my $time = shift;
    my ($file, $data, $reps, $time) = @_;
    my ($name, $rep);
    my $fname = basename($file);

    # Grab name (and replicate if applicable)
    if( $reps ) {
        ($name, $rep) = $fname =~ /^([A-Za-z0-9-.]+)_([A-Za-z]+)/;
    }
    # Set replicate to 1 if not applicable
    else {
        ($name) = $fname =~ /^([A-Za-z0-9-.]+)/;
        $rep = 1;
    }

    # Check that the name and replicate variables are defined
    ! defined $name && ! defined $rep ? &error("Could not extract name (and replicate) from $file") :
                        ! defined $name ? &error("Could not extract name from $file") :
                        ! defined $rep ? &error("Could not extract replicate from $file") : 1;

    # Begin data extraction
    open(FILE,"<$file") or die "Couldn't open $file for reading\n";

    # Time difference is calculated to record relative time
    # instead of current time
    my ($prevTime, $currTime);
    my @timePoints;
    while( <FILE> ) {
        chomp;
        # Find time point
        if( /(\d.*?\s.{11})\s+/ ) {
            my $timeRead = str2time($1);
            if( ! defined $prevTime ) {
                push(@timePoints, "0.0");
                $currTime = "0.0";
            }
            else {
                my $diffTime = ($timeRead - $prevTime) / 3600;
                $currTime = sprintf("%.1f", $timePoints[-1] + $diffTime);
                push(@timePoints, $currTime);
            }
            # Set new previous time
            $prevTime = $timeRead;
        }
        elsif( /(\w\d+)\s+([0-9.]+)/ ) {
            # Well = $1
            # Data = $2
            #print STDERR "Well $1, Data $2\n";
            #<>;
            $data->{$name}->{$rep}->{$1}->{$currTime} = $2;
        }
    }
    @$time = @timePoints if @timePoints > @$time;
    close(FILE);
}


###
# Input is the data hash-reference object. Information is printed in the order:
# (All output is tab-delimited)
# Row 1 (header) -- clone (main_source substrate || well#) [time]
# Row 2-n -- clone (main_source substrate || well#) [data]
# Note: When replicates are kept separate, the clone is separated into two
# columns for "clone" and "rep"
###
sub printData {
    my ($data, $plate, $reps, $time) = @_;
    foreach my $c ( keys %$data ) {
        foreach my $r ( keys %{$data->{$c}} ) {
            foreach my $w ( keys %{$data->{$c}->{$r}} ) {
                my @ods = ();
                foreach my $t( @$time ) {
                    my $val = ($data->{$c}->{$r}->{$w}->{$t}) ?
                                $data->{$c}->{$r}->{$w}->{$t} :
                                0;
                    push(@ods, $val);
                }

                my $ms = $plate ? $plate->{$w}->{main_source} : 0;
                my $s = $plate ? $plate->{$w}->{substrate} : 0;
                if( $reps ) {
                    $plate ?
                        print join("\t", ($c, $r, $ms, $s, @ods)) :
                        print join("\t", ($c, $r, $w, @ods))
                    ;
                }
                else {
                    $plate ?
                        print join("\t", ($c, $ms, $s, @ods)) :
                        print join("\t", ($c, $w, @ods))
                    ;
                }
                print "\n";
            }
        }
    }

}

###################################################
## ARGUMENT PARSING
###################################################

my $opts = {
                    files    =>   "",
                    dir      =>   "",
                    plate    =>   "",
                    reps     =>   "",
                    help     =>   ""
};

GetOptions(
                    "f=s"      =>   \$opts->{files},
                    "files=s"  =>   \$opts->{files},
                    "d=s"      =>   \$opts->{dir},
                    "dir=s"    =>   \$opts->{dir},
                    "p=s"      =>   \$opts->{plate},
                    "plate=s"  =>   \$opts->{plate},
                    "r"        =>   \$opts->{reps},
                    "reps"     =>   \$opts->{reps},
                    "h"        =>   \$opts->{help},
                    "help"     =>   \$opts->{help}
);

&usage("") if $opts->{help} ||
            ( !$opts->{files} && !$opts->{dir} );


#####################################################
## Check if data files exist
#####################################################
my @filepaths;
if( $opts->{files} ) {
    @filepaths = split(",", $opts->{files});
}
# Check if directory exists and is not empty
else {
    &usage("Data directory does not exist") unless ! $opts->{dir} || -e  $opts->{dir};
    opendir(DIR, $opts->{dir}) or &usage("Couldn't open $opts->{dir} to read files");
    while( my $f = readdir(DIR) ) {
        next if $f =~ m/^\./;
        push(@filepaths, "$opts->{dir}/$f");
    }
    # Check if directory was empty
    &usage("Directory empty given") if $#filepaths == 0;
}
&checkFiles(\@filepaths) || &usage("File(s) does not exist");

# Check if plate file exists
my $plate;
if( $opts->{plate} ) {
    if( -e $opts->{plate} ) {
        $plate = &readPlate($opts->{plate});
    }
    else {
        &usage("Plate file does not exist");
    }
}


######################################################
## Data extraction process
######################################################
my $data = {};
my @time;

# Read in data for each file
foreach my $f ( @filepaths ) {
    &readData($f, $data, $opts->{reps}, \@time);
}

######################################################
## Data printout process
######################################################

# Print out headers first
# Depends on if a plate file was supplied or not
# and if replcates are kept separate
if( $opts->{reps} ) {
    $plate ?
        print "clone\trep\tmain_source\tsubstrate" :
        print "clone\trep\twell";
}
else {
    $plate ?
        print "clone\tmain_source\tsubstrate" :
        print "clone\twell";
}

# Print out hours
foreach my $timeIter( @time ) {
    print "\t".sprintf("%.1f", $timeIter);
    $timeIter += 0.5;
}
print "\n"; # End of header line

# Print out data
&printData($data, $plate, $opts->{reps}, \@time);
