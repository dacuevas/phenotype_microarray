#!/usr/bin/perl
use Tie::File;
use Fcntl 'O_RDONLY';
use FindBin;

$length = scalar@ARGV;
#my @file;
$time = localtime;
open (OUTFILE, ">out");

# prints clone names by taking them from command line arguments

print OUTFILE "Clone\t";
for $j(0 .. 96){
	foreach $i(0..$length-1){
		
		if($i == $length-1){
			$temp = substr($ARGV[$i],0,-4);
			print OUTFILE "$temp\t";
		}
		
		else{
			$temp = substr($ARGV[$i],0,-4);
			print OUTFILE "$temp\t";
		}
	}
}

print OUTFILE "\n";

# prints main sources taking them from file 'pm_plate_1.txt' 
# from current directory

$plates = "$FindBin::Bin/pm_plate_1.txt";
tie @file, 'Tie::File', $plates, mode => O_RDONLY or die "Can't open file";
printf OUTFILE "Main Source\t";

foreach $i(0..95){	
	
	chomp @temp;
	@temp = split(/\t/,$file[$i]);
		
		for(0..$length-1){
			print OUTFILE $temp[1];
			print OUTFILE "\t";
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
			print OUTFILE "\t";
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
			print OUTFILE "\t";
	}
	
}

print OUTFILE "\n";

# determines number of data points taken per well
$data = "$FindBin::Bin/${ARGV[0]}";
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
	open(DATA, "<$ARGV[$i]");
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
				print OUTFILE "$temp[1]\t";
			}
		$line++;	
		}
	print OUTFILE "\n";
	$count += .5;			
	$line += 107;				
}

close OUTFILE;

