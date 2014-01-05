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
        self.numFiltered = 0
        self.numReplicates = {}  # Hash of clone->{rep. count}
        self.clones = []  # Set of unique clone names
        self.conditions = {}  # Hash of source->[conditions]
        self.wells = {}  # Hash of source->{condition]->well
        self.time = []  # Array of time values

        self.clonesNU = []  # Array of clones (non-unique)
        self.sourcesNU = []  # Array of sources (non-unique)
        self.conditionsNU = []  # Array of conditions (non-unique)

        # Primary data structure to access data
        self.dataHash = {}  # clone->{rep #}->{source}->{condition}->[ODs]
                            #               ->{filter}
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
            # Pre-set filter to False
            for source, sourceList in self.conditions.items():
                self.dataHash[clone][numRep][source] =\
                    {cond: {'filter': False, 'od': py.array([])}
                     for cond in sourceList}

    def __parseWells(self, ll):
        '''Well line parsing method'''
        # Store as source->{condition}->well
        for idx, well in enumerate(ll[1:]):
            source = self.sourcesNU[idx]
            cond = self.conditionsNU[idx]
            try:
                self.wells[source]
            except KeyError:
                self.wells[source] = {}
            self.wells[source][cond] = well

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
            self.dataHash[clone][numRep][source][condition]['od'] =\
                py.append(self.dataHash[clone][numRep][source]
                          [condition]['od'], od)

    def getCloneReplicates(self, clone, source, condition, applyFilter=False):
        '''Retrieve all growth curves for a clone+source+condition'''
        # Check if any other replicates should be returned
        # retArray is a 2xN multidimensional numpy array
        retArray = py.array([])
        first = True
        for i in xrange(2, self.numReplicates[clone] + 1):
            # Check if filter is enabled and curve should be filtered
            if applyFilter and \
                    self.dataHash[clone][i][source][condition]['filter']:
                continue
            elif first:
                retArray = py.array([self.dataHash[clone][i][source]
                                    [condition]['od']])
                first = False
            else:
                retArray = py.concatenate(
                    (retArray,
                     py.array([self.dataHash[clone][i][source]
                              [condition]['od']])))
        return retArray

    def getFiltered(self):
        '''Retrieve array of all growth curves labeled as filtered'''
        ret = []
        for clone, repDict in self.dataHash.items():
            for rep, sourceDict in repDict.items():
                for source, condDict in sourceDict.items():
                    for cond, odDict in condDict.items():
                        if odDict['filter']:
#                            try:
#                                ret[clone]
#                            except KeyError:
#                                ret[clone] = {}
#                            try:
#                                ret[clone][source]
#                            except KeyError:
#                                ret[clone][source] = {}
#                            try:
#                                ret[clone][source][cond]
#                            except KeyError:
#                                ret[clone][source][cond] = {}
                            ret.append((clone, source, cond, rep,
                                        odDict['od']))
                            #ret[clone][source][cond][rep] = odDict['od']
        return ret

    def setFilter(self, clone, rep, source, condition, filter):
        '''Set filter for specific curve'''
        oldFilter = self.dataHash[clone][rep][source][condition]['filter']
        self.dataHash[clone][rep][source][condition]['filter'] = filter
        if not oldFilter and filter:
            self.numFiltered += 1
        elif oldFilter and not filter:
            self.numFiltered -= 1
