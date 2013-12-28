#!/usr/bin/python
# pmanalysis.py
# Author: Daniel A Cuevas
# Created on 22 Nov. 2013

import sys
import os
import getptopt


def usage():
    '''Usage message for failed script execution'''
	print "\nusage: %s -i inputfile -o outputname -n output_directory\n\n" \
            % os.path.basename(sys.argv[0])


###############################################################################
# Argument Parsing
###############################################################################

inputFile = None
outPrefix = None # Prefix for all output files
outputDir = None
filterFlag = False
newHMFlag = False
window_size = 3
try:
	opts, args = getopt.getopt(sys.argv[1:],'fhi:o:n:z')
except getopt.GetoptError:
	usage()
	sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        usage()
        sys.exit(2)
    elif opt == '-i':
        inputFile = arg
    elif opt == '-o':
        outPrefix = arg
    elif opt == '-n':
        outputDir = arg
    elif opt == '-f':
        filterFlag = True
    elif opt == '-z':
        newHMFlag = True
    else:
        pass

# Check if arguments were not given
if not inputFile or not outputPrefix or not outputDir:
	usage()
	sys.exit(2)

###############################################################################
# Data Processing
###############################################################################

# Parse data file
