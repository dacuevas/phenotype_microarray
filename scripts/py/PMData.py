# PMData.py
# Phenotype microarray module for parsing optical density data
#
# Author: Daniel A Cuevas
# Created on 12 Dec. 2013
# Updated on 28 Dec. 2013

import pylab as py


class PMData:
    '''Class for parsing phenotype microarray data'''
    def __init__(self, filepath):
        self.filepath = filepath
        self.numClones = 0
        self.numConditions = 0
        self.numReplicates = {}  # Hash of clone->{rep. count}
        self.clones = []  # Set of unique clone names
        self.conditions = {}  # Hash of source->[conditions]
        self.wells = {}  # Hash of well->(source,condition)
        self.time = []  # Array of time values

        self.clonesNU = []  # Array of clones (non-unique)
        self.sourcesNU = []  # Array of sources (non-unique)
        self.conditionsNU = []  # Array of conditions (non-unique)

        # Primary data structure to access data
        self.dataHash = {}  # clone->{source}->{condition}->[ODs]
        self.__beginParse()

    def __beginParse(self):
        '''Initiate parsing on '''
        f = open(self.filepath, 'r')
        # Begin iteration through file
        for lnum, l in enumerate(f):
            l = l.rstrip('\n')
            ll = l.split('\t')

            # Line 1: clone names
            if lnum == 0:
                self.__parseClones(ll)

            # Line 2: source names
            elif lnum == 1:
                self.__parseSources(ll)

            # Line 3: condition substrates
            elif lnum == 2:
                self.__parseConditions(ll)

            # Line 4: well indicies [A-H][1-12]
            elif lnum == 3:
                self.__parseWells(ll)

            # Line 5+: OD values
            else:
                self.__parseOD(ll)
        f.close()

    def __parseClones(self, ll):
        '''Clone line parsing method'''
        self.clonesNU = ll[1:]
        self.clones = set(ll[1:])
        self.numClones = len(self.clones)

    def __parseSources(self, ll):
        '''Main sources line parsing method'''
        self.sourcesNU = ll[1:]
        # Initialize conditions hash
        self.conditions = {s: [] for s in set(self.sourcesNU)}

    def __parseConditions(self, ll):
        '''Growth conditions line parsing method'''
        self.conditionsNU = ll[1:]
        # Add to conditions hash
        [self.conditions[self.sourcesNU[idx]].append(c)
         for idx, c in enumerate(self.conditionsNU)]

        # Duplicate conditions created for each source
        # in above method - must remove
        for source in self.conditions:
            self.conditions[source] = set(self.conditions[source])
            self.numConditions += len(self.conditions[source])

        # Initialize main data hash
        prevClone = ""
        numRep = 1
        for clone in self.clonesNU:
            # Keep track of replicate numbers
            # Reset rep number if we reach a new clone name
            numRep = numRep + 1 if clone == prevClone else 1

            # Update replicate count for clone
            self.numReplicates[clone] = numRep
            prevClone = clone

            if clone not in self.dataHash:
                self.dataHash[clone] = {}

            if numRep not in self.dataHash[clone]:
                self.dataHash[clone][numRep] = {}

            # Add condition to main data hash
            for source, sourceList in self.conditions.items():
                self.dataHash[clone][numRep][source] = {cond: py.array([])
                                                        for cond in sourceList}

    def __parseWells(self, ll):
        '''Well line parsing method'''
        # Store as well->(source,condition)
        self.wells = {well: (source, cond) for well, source, cond in
                      zip(ll[1:], self.sourcesNU, self.conditionsNU)}

    def __parseOD(self, ll):
        '''OD data lines parsing method'''
        ll = [float(x) for x in ll]
        self.time.append(ll[0])
        numRep = 1
        prevClone = ""
        for idx, od in enumerate(ll[1:]):
            clone = self.clonesNU[idx]
            source = self.sourcesNU[idx]
            condition = self.conditionsNU[idx]

            # Check which clone + replicate we are observing
            numRep = numRep + 1 if clone == prevClone else 1
            prevClone = clone

            # Append OD reading to array
            self.dataHash[clone][numRep][source][condition] =\
                py.append(self.dataHash[clone][numRep][source][condition], od)

    def getCloneData(self, clone, source, condition):
        '''Retrieve all growth curves for a clone+source+condition'''
        # Initialize the numpy array to return
        retArray = py.array([self.dataHash[clone][1][source][condition]])
        # Check if any other replicates should be returned
        # retArray is a 2xN multidimensional numpy array
        for i in xrange(2, self.numReplicates[clone] + 1):
            retArray = py.concatenate(
                (retArray,
                 py.array([self.dataHash[clone][i][source][condition]])))
        return retArray
