#!/usr/bin/perl
# data_formatter.pl
# Combine multiple phenotype microarray files into one data file
#
# Authors: Ted Kassen (Primary) & Daniel A Cuevas


use Tie::File;
use Fcntl 'O_RDONLY';
use FindBin;
use File::Basename;
use Getopt::Long;


sub usage {
    my $msg = shift;
    my $filepath = basename($0);
    print "ERROR: $msg\n\n" if $msg;
    print << "END"
USAGE
    perl $filepath [Options] -f file_list -p plate_file

REQUIRED
    -f, --files LIST,OF,FILES      : Comma-separated list of data files
    -p, --plate PLATE.TXT          : Plate filepath

OPTIONS
    -o, --out                      : Output file name
    -r, --reps                     : Replicate flag
    -?, -h, --help                 : This usage message

NOTES
    FILE NAME FORMATS:
        When using replicates be sure to have the file name in the format,

        <Clone Name>_<Replicate Letter>_<other text>.txt
        Regex used:    <Clone Name> -- [A-Za-z0-9-.]+
                       <Replicate Letter> -- [A-Za-z0-9]+

        When replicates are not indicated,

        <Clone Name>_<other text>.txt
        Regex used:    <Clone Name> -- [A-Za-z0-9-._]+
END
;
    exit(1);
}

# Argument parsing
my $opts = {
                files      =>  "",
                plate      =>  "",
                out        =>  "",
                reps       =>  "",
                help       =>  ""
};

GetOptions(
                "f=s"      =>  \$opts->{files},
                "files=s"  =>  \$opts->{files},
                "p=s"      =>  \$opts->{plate},
                "plate=s"  =>  \$opts->{plate},
                "o=s"      =>  \$opts->{out},
                "out=s"    =>  \$opts->{out},
                "r"        =>  \$opts->{reps},
                "reps"     =>  \$opts->{reps},
                "h"        =>  \$opts->{help},
                "help"     =>  \$opts->{help}
);

&usage("") if $opts->{help} ||
              !$opts->{files} ||
              !$opts->{plate};

$outName = $opts->{out} ? $opts->{out} : "out";
@fileList = split(/,/, $opts->{files});


$length = scalar@fileList;
#my @file;
$time = localtime;
open (OUTFILE, ">$outName");

# prints clone names by taking them from command line arguments

print OUTFILE "Clone\t";
#for $j(0 .. 96){
for $j(0 .. 95){
	foreach $i(0..$length-1){

        # Remove extension
        $temp = fileparse($fileList[$i], qr/\.[^.]*/);
        if( $opts->{reps} ) {
            ($name, $rep) = $temp =~ /^([A-Za-z0-9-.]+)_([A-Za-z0-9]+)/;
        }
        else {
            ($name) = $temp =~ /^([A-Za-z0-9-._]+)/;
        }

		if($i == $length-1 && $j == 95){
            #$temp = substr($ARGV[$i],0,-4);
			print OUTFILE "$name";
		}
		
		else{
            #$temp = substr($ARGV[$i],0,-4);
			print OUTFILE "$name\t";
		}
	}
}

print OUTFILE "\n";

# prints main sources taking them from file 'pm_plate_1.txt' 
# from current directory

#$plates = "$FindBin::Bin/pm_plate_1.txt";
$plates = $opts->{plate};

tie @file, 'Tie::File', $plates, mode => O_RDONLY or die "Can't open file";
printf OUTFILE "Main Source\t";

foreach $i(0..95){	
	
	chomp @temp;
	@temp = split(/\t/,$file[$i]);
		
		for(0..$length-1){
			print OUTFILE $temp[1];
            print OUTFILE "\t" if $_ != $length-1 || $i != 95;
	}
	
}

print OUTFILE "\n";

# prints growth media taking them from file 'pm_plate_1.txt' 
# from current directory

printf OUTFILE "Growth Media\t";
foreach $i(0..95){	
	
	chomp @temp;
	@temp = split(/\t/,$file[$i]);
		
		for(0..$length-1){
			print OUTFILE $temp[2];
			print OUTFILE "\t" if $_ != $length-1 || $i != 95;
	}
	
}

print OUTFILE "\n";

# prints well numbers taking them from file 'pm_plate_1.txt' 
# from current directory

printf OUTFILE "Wells\t";
foreach $i(0..95){	
	
	@temp = split(/\t/,$file[$i]);
	chomp @temp;
		
		for(0..$length-1){
			print OUTFILE $temp[0];
			print OUTFILE "\t" if $_ != $length-1 || $i != 95;
	}
	
}

print OUTFILE "\n";

# determines number of data points taken per well
#$data = "$FindBin::Bin/${ARGV[0]}";
$data = $fileList[0];
tie @file, 'Tie::File', $data, mode => O_RDONLY or die "Can't open file";
$runs = ((scalar@file))/203;
$size = (scalar@file);
untie @file;

$i = 1;
$line = 6;
$count = 0.0;

my @temp;
@file = ();

#push all data into @file
foreach $i(0 .. $length-1){
    #open(DATA, "<$ARGV[$i]");
	open(DATA, "<$fileList[$i]") or die "Couldn't open $fileList[$i]\n";
	@temp = <DATA>;
	push(@file,@temp);
	close($file_handle);
}

@temp = ();

chomp @file;

# prints datapoints
foreach(0...$runs-1){
	printf OUTFILE <%.1f>,$count;
	printf OUTFILE "\t";
    foreach $i (0 ..  95){
        foreach $k(0 .. $length-1){
            @temp = split(/\t/,$file[($size*$k)+$line]);
            print OUTFILE "$temp[1]";
            print OUTFILE "\t" if $k != $length-1 || $i != 95;
        }
        $line++;	
    }
	print OUTFILE "\n";
	$count += .5;			
	$line += 107;				
}

close OUTFILE;

