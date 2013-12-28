# PMData.py
# Author: Daniel A Cuevas
# Created on 12 Dec. 2013


import pylab as py


class PMData:
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
        self.beginParse()

    def beginParse(self):
        f = open(self.filepath, 'r')
        # Begin iteration through file
        for lnum, l in enumerate(f):
            l = l.rstrip('\n')
            ll = l.split('\t')

            # Line 1: clone names
            if lnum == 0:
                self.parseClones(ll)

            # Line 2: source names
            elif lnum == 1:
                self.parseSources(ll)

            # Line 3: condition substrates
            elif lnum == 2:
                self.parseConditions(ll)

            # Line 4: well indicies [A-H][1-12]
            elif lnum == 3:
                self.parseWells(ll)

            # Line 5+: OD values
            else:
                self.parseOD(ll)
        f.close()

    def parseClones(self, ll):
        self.clonesNU = ll[1:]
        self.clones = set(ll[1:])
        self.numClones = len(self.clones)

    def parseSources(self, ll):
        self.sourcesNU = ll[1:]
        # Initialize conditions hash
        self.conditions = {s: [] for s in set(self.sourcesNU)}

    def parseConditions(self, ll):
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
            # Check if clone already exists in hash - this is replicate 1
            numRep = numRep + 1 if clone == prevClone else 1
            self.numReplicates[clone] = numRep
            prevClone = clone
            if clone not in self.dataHash:
                self.dataHash[clone] = {}

            if numRep not in self.dataHash[clone]:
                self.dataHash[clone][numRep] = {}

            for source, sourceList in self.conditions.items():
                self.dataHash[clone][numRep][source] = {cond: py.array([])
                                                        for cond in sourceList}

    def parseWells(self, ll):
        self.wells = {well: (source, cond) for well, source, cond in
                      zip(ll[1:], self.sourcesNU, self.conditionsNU)}

    def parseOD(self, ll):
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
            self.dataHash[clone][numRep][source][condition] =\
                py.append(self.dataHash[clone][numRep][source][condition], od)

    def getCloneData(self, clone, source, condition):
        retArray = py.array([self.dataHash[clone][1][source][condition]])
        for i in xrange(2, self.numReplicates[clone] + 1):
            retArray = py.concatenate(
                (retArray,
                 py.array([self.dataHash[clone][i][source][condition]])))
        return retArray
