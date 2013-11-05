#!/bin/bash

usage() {
	echo "
usage: $scriptname -i PM_data -n output_directory -o output_name -p plate_filename -r \"regex\" [Options]

Required
   -i [PM_data]            : PM OD filepath or directory path to files (if directory, must use '-d' argument)
   -n [output_directory]   : Output directory (will create if non-existent)
   -o [output_name]        : Prefix prepended to all output files
   -p [plate_filename]     : Tab-delimited plate filepath
   -r \"[regex]\"            : Regular expression to indicate clone names found in OD filenames (quotes around regex are recommended)

Optional
   -c                      : Clear all intermediate files (except for input file into PManalysis)
   -d                      : Flag if input is a directory of OD files
   -f                      : Flag if filter should be applied to growth curves during PManalysis
   -h, -?, --help          : This help message
   --hm                    : Use new harmonic mean calculation
   --reps                  : Flag if there are replicates involved
   -s [scripts_directory]  : Directory where scripts are stored [Default is current directory]
   -v                      : Verbose output

" >&2
}

error() {
	echo "*****FATAL ERROR OCCURRED*****" >&1
	echo $1 >&2
	exit 1
}

checkInputFile() {
	if [[ $2 -eq 0 ]]; then
		if [[ ! -d $1 ]]; then
			getTime && error "${currtime}	Directory '$1' does not exist."
		fi
		# Store directory in new variable and remove trailing slash
		inputfiledir=$(echo $inputfile | perl -ne 'chomp; s/\/$//; print;') 
		inputfile=$(ls $1)

	elif [[ ! -f $1 ]]; then
		getTime && error "${currtime}	File '$1' does not exist."
	fi
}

checkOutputDir() {
	# Remove trailing slash
	outputdir=$(echo $1 | perl -ne 'chomp; s/\/$//; print;')
	# Check to see if directory needs to be created
	[[ ! -d $1 ]] && getTime && echo "${currtime}	Output directory '$1' does not exist. Creating now." >&1 && mkdir $1
}


checkScriptDir() {
	if [[ -z $1 ]]; then
		scriptdir="./" # Script directory is current directory
	else
		[[ ! -d $1 ]] && getTime && error "${currtime}	Script directory '$1' does not exist."
		scriptdir=$1
	fi
	# Remove trailing slash
	scriptdir=$(echo $scriptdir | perl -ne 'chomp; s/\/$//; print;')
}

getTime() {
	currtime=$(date "+[%F %H:%M:%S]")
}

####################################################
#ARGUMENT PARSING
####################################################

scriptname=$(echo $0 | perl -ne '@tmp=split /\//; print $tmp[-1];')
inputdirflag=1
filterflag=""
hmFlag=""
reps=1

while [[ $# != 0 ]]; do
	case $1 in
	-h|-\?|--help)
		usage
		exit 2
		;;
	-c)
		clearfiles=0
		;;
	-d)
		inputdirflag=0
		;;
	-f)
        filterflag="-f"
		;;
    --hm)
        hmFlag="-z"
        ;;
	-i)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -o value" >&2 && usage && exit 2
		inputfile=$1
		;;
	-n)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -n value" >&2 && usage && exit 2
		outputdir=$1
		;;
	-o)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -o value" >&2 && usage && exit 2
		outputname=$1
		;;
	-p)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -p value" >&2 && usage && exit 2
		plate=$1
		;;
	-r)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -r value" >&2 && usage && exit 2
		regex=$1
		;;
	--reps)
		reps=2
		;;
	-s)
		shift
		[[ ! $1 || $(printf "%s" "$1" | perl -ne 'm/(^-.$)/; print $1;') ]] && echo "Missing -s value" >&2 && usage && exit 2
		scriptdir=$1
		;;
	-v)
		verbose=0;
		;;
	*)
		echo "Unknown option $1" >&2
		usage
		exit 2
	esac
	shift
done


# Check if required options are given
if [[ ! $inputfile ||
	! $outputname ||
	! $plate ||
	! $outputdir ||
	! $regex ]]; then
	usage
	exit 2
fi

# Check if input file or directory exists
checkInputFile $inputfile $inputdirflag

# Remove leading slashes from output directory
checkOutputDir $outputdir

# Check if script direectory exists
checkScriptDir $scriptdir

# Convert input files line endings from DOS to UNIX
getTime && echo "${currtime}	*****Checking line endings*****" >&1
for f in ${inputfile[@]}; do
	f=$(echo $f | perl -ne 's/([\(\)])/\\$1/g; print;') # Escape any parentheses in input file name
	cmd="${scriptdir}/line2unix $inputfiledir/$f"
	[[ $verbose ]] && getTime && echo "${currtime}	Executing $cmd" >&1
	eval $cmd
	[[ $? -ne 0 ]] && getTime && error "${currtime}	Fail on command: $cmd"
done

################################################
#BIOLOG PARSING PART 1
################################################

parsedfiles=() # Will contain array of file names for next step

# Iterate through files and produce first parsed version of each file
getTime && echo "${currtime}	*****Parsing phase 1*****" >&1
for f in ${inputfile[@]}; do
	rname=$(echo "$f,$regex" | perl -ne 'chomp; ($f,$r)=split /,/; $f=~m/($r)/; print $1;')
	f=$(echo $f | perl -ne 's/([\(\)])/\\$1/g; print;') # Escape any parentheses in input file name
	out="${rname}_${outputname}.txt"
	parsedfiles=("${parsedfiles[@]}" "$outputdir/$out") # Append to array
	cmd="${scriptdir}/biologout_parse2 $inputfiledir/$f > $outputdir/${out}"
	[[ $verbose ]] && getTime && echo "${currtime}	Executing $cmd" >&1
	eval $cmd
	[[ $? -ne 0 ]] && getTime && error "${currtime}	Fail on command: $cmd"
done


################################################
#BIOLOG PARSING PART 2
################################################

out="${outputname}_data.txt"
cmd="${scriptdir}/pm_data_organizer4 -p $plate -f ${parsedfiles[@]} -r $reps > $outputdir/${out}"
getTime && echo "${currtime}	*****Parsing phase 2*****" >&1
[[ $verbose ]] && getTime && echo "${currtime}	Executing $cmd" >&1
eval $cmd
[[ $? -ne 0 ]] && getTime && error "${currtime}	Fail on command: $cmd"


################################################
#ANALYSIS
################################################

in="$outputdir/${out}"
cmd="${scriptdir}/PManalysis.py -i $in -o $outputname -n $outputdir $filterflag $hmFlag"
getTime && echo "${currtime}	*****Starting modeling script*****" >&1
[[ $verbose ]] && getTime && echo "${currtime}	Executing $cmd" >&1
eval $cmd
[[ $? -ne 0 ]] && getTime && error "${currtime}	Fail on command: $cmd"

getTime && echo "${currtime}	*****Completed!*****" >&1

[[ $clearfiles ]] && rm ${parsedfiles[@]}
