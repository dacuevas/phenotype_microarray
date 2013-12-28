#!/usr/bin/python
# pmanalysis.py
# Main driver for the PM analysis
#
# Author: Daniel A Cuevas
# Created on 22 Nov. 2013
# Updated on 28 Dec. 2013

import argparse
import PMData
import sys
import time
import datetime


###############################################################################
# Utility methods
###############################################################################

def timeStamp():
    '''Return ime stamp'''
    t = time.time()
    fmt = '[%Y-%m-%d %H:%M:%S]'
    return datetime.datetime.fromtimestamp(t).strftime(fmt)


def printStatus(msg):
    '''Print status message'''
    print >> sys.stderr, timeStamp(), ' ', msg

###############################################################################
# Argument Parsing
###############################################################################

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='Input PM file')
parser.add_argument('outdir',
                    help='Directory to store output files')
parser.add_argument('-o', '--outprefix',
                    help='Prefix prepended to output files')
parser.add_argument('-f', '--filter', action='store_true',
                    help='Apply filtering to growth curves')
parser.add_argument('-g', '--newgrowth', action='store_true',
                    help='Apply new growth level calculation')

args = parser.parse_args()
inputFile = args.infile
outPrefix = args.outprefix if args.outprefix else 'out'
outDir = args.outdir
filterFlag = args.filter
newGrowthFlag = args.newgrowth
verbFlag = args.verbose
window_size = 3

###############################################################################
# Data Processing
###############################################################################

# Parse data file
printStatus('Parsing input file.')
sys.stderr.flush()
pmdata = PMData.PMData(inputFile)
printStatus('Parsing complete.')
