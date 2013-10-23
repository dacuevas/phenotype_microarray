#!/usr/bin/perl -w
use strict;
use List::Util qw(sum min max);
use Statistics::Basic qw(median);
use POSIX qw(floor);


my $filename = $ARGV[0];
my $suffix = $ARGV[1] ? $ARGV[1] : "out";

my $clones = {};
my $substrates = {};
my $hms = {};
my $data = {};
my $annData = {};

open(FILE,"<$filename") or die "Couldn't open '$filename' for reading\n";

my $header = <FILE>;

while (<FILE>) {
	chomp;
	my($clone,$mainSource,$substrate,$well,$harmonicMean) = split "\t";
###	++$clones->{$clone}->{$bin};
###	++$substrates->{$substrate}->{$bin};
###	if ($bin =~ m/(growth|linear)/) {
        next if $harmonicMean =~ /nan/i;
		if (! defined $hms->{clones}->{$clone}) {
			$hms->{clones}->{$clone} = ();
		}
		push @{$hms->{clones}->{$clone}},$harmonicMean;

		if (! defined $hms->{substrates}->{$substrate}) {
			$hms->{substrates}->{$substrate} = ();
		}
		push @{$hms->{substrates}->{$substrate}},$harmonicMean;
		$data->{$clone}->{$substrate} = $harmonicMean;
###        $annData->{$clone}->{$substrate} = $ann;
###	}
}
close FILE;


###open(FILE,">counts_clones_$suffix.txt") or die "Couldn't open file 'counts_clones_$suffix.txt' for writing\n";
###print FILE join "\t",("clone","bin","count\n");
###foreach my $clone(keys $clones) {
###	foreach my $bin(keys $clones->{$clone}) {
###		print FILE join "\t",($clone,$bin,$clones->{$clone}->{$bin}."\n");
###	}
###}
###close FILE;


###open(FILE,">counts_substrates_$suffix.txt") or die "Couldn't open file 'counts_substrates_$suffix.txt' for writing\n";
###print FILE "substrate\tbin\tcount\n";
###foreach my $substrate(keys $substrates) {
###	foreach my $bin(keys $substrates->{$substrate}) {
###		print FILE join "\t",($substrate,$bin,$substrates->{$substrate}->{$bin},"\n");
###	}
###}
###close FILE;


my $stats = {};

###open(FILE,">stats_clones_$suffix.txt") or die "Couldn't open file 'stats_clones_$suffix.txt' for writing\n";
###print FILE join "\t",("clone","numGrowth","numLinear","numNoGrowth","numMisfits","meanHM","stdevHM","minHM","maxHM\n");
###foreach my $clone(keys $hms->{clones}) {
###	my @currHms = @{$hms->{clones}->{$clone}};
###	my ($numGrowth,$numLinear,$numNoGrowth,$numMisfits);
	
###	$numGrowth = $clones->{$clone}->{growth} || 0;
###	$numLinear = $clones->{$clone}->{linear} || 0;
###	$numNoGrowth = $clones->{$clone}->{nogrowth} || 0;
###	$numMisfits = $clones->{$clone}->{misfits} || 0;

###	$stats->{$clone} = getStats($hms->{clones}->{$clone});
###	my $mean = $stats->{$clone}->{mean};
###	my $stdev = $stats->{$clone}->{stdev};
###	my $min = $stats->{$clone}->{min};
###	my $max = $stats->{$clone}->{max};
###	print FILE join "\t",($clone,$numGrowth,$numLinear,$numNoGrowth,$numMisfits,$mean,$stdev,$min,$max."\n");
###}
###close FILE;


###open(FILE,">stats_substrates_$suffix.txt") or die "Couldn't open file 'stats_substrates_$suffix.txt' for writing\n";
###print FILE join "\t",("substrate","numGrowth","numLinear","numNoGrowth","numMisfits","meanHM","medianHM","stdevHM","minHM","maxHM\n");
foreach my $substrate(keys %{$hms->{substrates}}) {
	my @currHms = @{$hms->{substrates}->{$substrate}};
	my ($numGrowth,$numLinear,$numNoGrowth,$numMisfits);

	$numGrowth = $substrates->{$substrate}->{growth} || 0;
	$numLinear = $substrates->{$substrate}->{linear} || 0;
	$numNoGrowth = $substrates->{$substrate}->{nogrowth} || 0;
	$numMisfits = $substrates->{$substrate}->{misfits} || 0;

	$stats->{$substrate} = getStats($hms->{substrates}->{$substrate});
	my $mean = $stats->{$substrate}->{mean};
	my $median = $stats->{$substrate}->{median};
	my $stdev = $stats->{$substrate}->{stdev};
	my $min = $stats->{$substrate}->{min};
	my $max = $stats->{$substrate}->{max};
###	print FILE join "\t",($substrate,$numGrowth,$numLinear,$numNoGrowth,$numMisfits,$mean,$median,$stdev,$min,$max."\n");
}
###close FILE;



open(FILE,">function_distribution_$suffix.txt") or die "Couldn't open 'function_distribution_$suffix.txt' for writing\n";
print FILE join "\t",("clone","substrate","category","harmonic_mean","substrate_mean","substrate_std\n");
foreach my $clone(keys %$data) {
	foreach my $substrate(keys %{$data->{$clone}}) {
		my $hm = $data->{$clone}->{$substrate};
		my $mean = $stats->{$substrate}->{mean};
		my $stdev = $stats->{$substrate}->{stdev};
        my $lowBound = $mean-$stdev*3;
        my $highBound = $mean+$stdev*3;
		my $category = $hm >= $lowBound && $hm <= $highBound && $hm < 0.5      ? "No Growth"
						 : $hm >= $lowBound && $hm <= $highBound && $hm >= 0.5 ? "Expected Growth"
						 : $hm > $mean+($stdev*2)							   ? "Gain of Function"
						 :                                                       "Loss of Function";

# Last used version
#		my $category = $hm < 0.5					  ?  "No Growth"
#						 : $hm > $mean+($stdev*2)	 ?  "Gain of Function"
#						 : $hm < $mean-($stdev*2)	 ?  "Loss of Function"
#						 :										"Expected Growth";
#
		print FILE join "\t",($clone,$substrate,$category,$hm,$mean,$stdev."\n");
	}
}

close FILE;

sub getStats {
	my @data = @{$_[0]};

	# Basic statistics
	my $min = min @data;
	my $max = max @data;
	my $n = @data;
	my $sum = sum @data;
	my $mean = $sum / $n;
	my $medvector = median()->set_size($n);
	foreach (@data) {
		$medvector->insert($_);
	}
	my $median = $medvector->query;
	my ($squaredSum,$numGrowth,$numNoGrowth) = (0) x 3;
	foreach (@data) {
		$squaredSum += (($_ - $mean) ** 2 );
		if ($_ >= 0.5) {
			++$numGrowth;
		}
		else {
			++$numNoGrowth;
		}
	}
	$squaredSum /= $n;
	my $stdev = sqrt $squaredSum;
	my $growth = $numGrowth >= $n*0.5 ? 1 : 0;


	return {
				mean => $mean,
				median => $median,
				stdev => $stdev,
				min => $min,
				max => $max,
				growth => $growth
	};
}

