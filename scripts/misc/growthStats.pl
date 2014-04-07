#!/usr/bin/perl -w
use strict;
use List::Util qw(sum min max);
use Statistics::Basic qw(median);
use POSIX qw(floor);


my $filename = $ARGV[0];
my $threshold = $ARGV[1] ? $ARGV[1] : 0.5;
my $suffix = $ARGV[2] ? $ARGV[2] : "out";

my $clones = {};
my $substrates = {};
my $hms = {};
my $data = {};
my $annData = {};

open(FILE,"<$filename") or die "Couldn't open '$filename' for reading\n";

my $header = <FILE>;
my $nanList = {};
while (<FILE>) {
    chomp;
    my($clone,$mainSource,$substrate,$well,$harmonicMean) = split "\t";
        if ($harmonicMean =~ /nan/i) {
            if (! defined $nanList->{$clone}) {
                $nanList->{$clone} = ();
            }
            push @{$nanList->{$clone}},$substrate;
            next;
        }
        if (! defined $hms->{clones}->{$clone}) {
            $hms->{clones}->{$clone} = ();
        }
        push @{$hms->{clones}->{$clone}},$harmonicMean;

        if (! defined $hms->{substrates}->{$substrate}) {
            $hms->{substrates}->{$substrate} = ();
        }
        push @{$hms->{substrates}->{$substrate}},$harmonicMean;
        $data->{$clone}->{$substrate} = $harmonicMean;
}
close FILE;

my $stats = {};

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
}



########## Functin distribution ##########
# Expected Growth:     HM >= threshold && [avg - (2*stddev) < HM < avg + (2*stddev)]
# No Growth:           HM < threshold && [avg - (2*stddev) < HM < avg + (2*stddev)]
# Gain of Function:    HM >= threshold && HM > avg + (2*stddev)
# Loss of Function:    HM <= avg - (2*stddev)
##########################################
#open(FILE,">function_distribution_$suffix.txt") or die "Couldn't open 'function_distribution_$suffix.txt' for writing\n";
#print FILE join "\t",("clone","substrate","category","harmonic_mean","substrate_mean","substrate_std\n");
print join "\t",("clone","substrate","category","harmonic_mean","substrate_mean","substrate_std\n");
foreach my $clone(keys %$data) {
    foreach my $substrate(keys %{$data->{$clone}}) {
        my $hm = $data->{$clone}->{$substrate};
        my $mean = $stats->{$substrate}->{mean};
        my $stdev = $stats->{$substrate}->{stdev};
        my $lowBound = $mean-$stdev*2;
        my $highBound = $mean+$stdev*2;
        my $category = $hm >= $lowBound && $hm <= $highBound && $hm >= $threshold ? "Expected Growth"
                         : $hm > $mean+($stdev*2) && $hm >= $threshold            ? "Gain of Function"
                         : $hm < $mean-($stdev*2) && $mean >= $threshold          ? "Loss of Function"
                         :                                                          "No Growth";

# Last used version
#        my $category = $hm >= $lowBound && $hm <= $highBound && $hm < 0.5      ? "No Growth"
#                         : $hm >= $lowBound && $hm <= $highBound && $hm >= 0.5 ? "Expected Growth"
#                         : $hm > $mean+($stdev*2)                               ? "Gain of Function"
#                         :                                                       "Loss of Function";
#        my $category = $hm < 0.5                      ?  "No Growth"
#                         : $hm > $mean+($stdev*2)     ?  "Gain of Function"
#                         : $hm < $mean-($stdev*2)     ?  "Loss of Function"
#                         :                                        "Expected Growth";
#
#        print FILE join "\t",($clone,$substrate,$category,$hm,$mean,$stdev."\n");
        print join "\t",($clone,$substrate,$category,$hm,$mean,$stdev."\n");
    }
}

# Print out nans
foreach my $clone(keys %$nanList) {
    foreach my $substrate(@{$nanList->{$clone}}) {
        print "$clone\t$substrate\tnan\tnan\tnan\tnan\n";
    }
}


sub getStats {
    my @data = @{$_[0]};

    # Basic statistics
    my $min = min @data;
    my $max = max @data;
    my $n = @data;
    my $sum = sum @data;
    my $mean = $sum / $n;
    #my $medvector = median()->set_size($n);
    #foreach (@data) {
    #    $medvector->insert($_);
    #}
    #my $median = $medvector->query;
    my ($squaredSum,$numGrowth,$numNoGrowth) = (0) x 3;
    foreach (@data) {
        $squaredSum += (($_ - $mean) ** 2 );
        #if ($_ >= 0.5) {
        #    ++$numGrowth;
        #}
        #else {
        #    ++$numNoGrowth;
        #}
    }
    $squaredSum /= $n;
    my $stdev = sqrt $squaredSum;
    #my $growth = $numGrowth >= $n*0.5 ? 1 : 0;


    return {
                mean => $mean,
                #median => $median,
                stdev => $stdev,
                min => $min,
                max => $max
                #growth => $growth
    };
}

