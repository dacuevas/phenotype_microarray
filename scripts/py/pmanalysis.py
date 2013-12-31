#!/usr/bin/python
# pmanalysis.py
# Main driver for the phenotype microarray analysis
#
# Author: Daniel A Cuevas
# Created on 22 Nov. 2013
# Updated on 28 Dec. 2013

import argparse
import sys
import time
import datetime
import PMData
import GrowthCurve


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
    sys.stderr.flush()


def curveFilter(clone, rep, source, cond, curve, pmData):
    '''Determine if growth curve passes filters'''
    ODmax = 0.18  # Maximum optical density in first two hours
    # Only check from 30 minute to 2 hour mark
    if [x for x in curve[1:5] if x >= ODmax]:
        pmData.setFilter(clone, rep, source, cond, True)
#        # Add to filteredCurves
#        try:
#            filteredCurves[clone]
#        except:
#            filteredCurves[clone] = {}
#        try:
#            filteredCurves[clone][rep]
#        except:
#            filteredCurves[clone][rep] = {}
#        try:
#            filteredCurves[clone][rep][source]
#        except:
#            filteredCurves[clone][rep][source] = {}

###############################################################################
# Argument Parsing
###############################################################################

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='Input PM file')
parser.add_argument('outdir',
                    help='Directory to store output files')
parser.add_argument('-o', '--outsuffix',
                    help='Suffix appended to output files. Default is "out"')
parser.add_argument('-f', '--filter', action='store_true',
                    help='Apply filtering to growth curves')
parser.add_argument('-g', '--newgrowth', action='store_true',
                    help='Apply new growth level calculation')

args = parser.parse_args()
inputFile = args.infile
outSuffix = args.outsuffx if args.outsuffix else 'out'
outDir = args.outdir
filterFlag = args.filter
newGrowthFlag = args.newgrowth
window_size = 3

###############################################################################
# Data Processing
###############################################################################

# Parse data file
printStatus('Parsing input file...')
pmData = PMData.PMData(inputFile)
printStatus('Parsing complete.')
printStatus('Found {} samples and {} growth conditions.'.format(
    pmData.numClones, pmData.numConditions))


# Perform filter
if filterFlag:
    printStatus('Performing filtering...')
    for c, repDict in pmData.dataHash.items():
        for rep, sDict in repDict.items():
            for s, condDict in sDict.items():
                for cond, curve in condDict.items():
                    # Perform filter check
                    curveFilter(c, rep, s, cond, curve, pmData)
    printStatus('Filtering complete.')

printStatus('Processing growth curves and creating logistic models...')
logData = {}
for c in pmData.clones:
    logData[c] = {}
    for s, condList in pmData.conditions.items():
        logData[c][s] = {}
        for cond in condList:
            curves = pmData.getCloneReplicates(c, s, cond)
            if curves:
                gc = GrowthCurve.GrowthCurve(curves, pmData.time)
                logData[c][s][cond] = gc
printStatus('Processing complete.')


printStatus('Printing output files...')
fhInfo = open('curveinfo_{}.txt'.format(outSuffix), 'w')
fhInfo.write('sample\tmainsource\tgrowthcondition\twell\tlag\t')
fhInfo.write('maxiumimgrowthrate\tasymptote\tgrowthlevel\n')

fhLogCurve = open('logistic_curve_{}.txt'.format(outSuffix), 'w')
fhLogCurve.write('sample\tmainsource\tgrowthcondition\twell\t')
fhLogCurve.write('\t'.join(['{:.1f}'.format(x) for x in pmData.time]))
fhLogCurve.write('\n')

for c in pmData.clones:
    for w, condTuple in pmData.wells.items():
        s, cond = condTuple
        fhInfo.write('{}\t{}\t{}\t{}\t'.format(c, s, cond, w))
        fhLogCurve.write('{}\t{}\t{}\t{}\t'.format(c, s, cond, w))

        # Print curve information
        try:
            curve = logData[c][s][cond]
        except KeyError:
            continue
        lag = curve.lag
        mgr = curve.maxGrowthRate
        asymptote = curve.asymptote
        gLevel = curve.growthLevel
        fhInfo.write('\t'.join(['{:.3f}'.format(x)
                                for x in (lag, mgr, asymptote, gLevel)]))
        fhInfo.write('\n')

        # Print logistic curves
        fhLogCurve.write('\t'.join(['{:.3f}'.format(x)
                                    for x in curve.dataLogistic]))
        fhLogCurve.write('\n')
fhInfo.close()
fhLogCurve.close()
printStatus('Printing complete.')
printStatus('Analysis complete.')
