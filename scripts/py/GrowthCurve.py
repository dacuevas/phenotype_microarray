# GrowthCurve.py
# Author: Daniel A Cuevas
# Created on 21 Nov. 2013

# Microbial growth curve class to extract parameters
# Use with Phenotype MicroArray analysis pipeline

import pylab as py
import Models


class GrowthCurve:
    def __init__(self, data, time):
        self.dataReps = data  # OD data values (replicates implied)
        self.dataMed = py.median(self.data, axis=0)
        self.time = time  # time values
        self.asymptote = self.calcAsymptote()
        self.maxGrowthRate, self.mgrTime = self.calcMGR()
        self.dataLogistic, self.lag = self.calcLag()
        self.growthLevel = self.calcGrowth()

    def calcAsymptote(self):
        '''Obtain the value of the highest OD reading'''
        stop = self.nReads - 3
        maxA = -1
        for idx in py.xrange(1, stop):
            av = py.mean(self.data[idx:idx + 3])
            if av > maxA:
                maxA = av
        return maxA

    def calcMGR(self):
        '''Obtain the value of the max growth'''
        stop = self.nReads - 4
        grs = []
        for idx in py.xrange(1, stop):
            gr = ((py.log(self.data[idx + 3]) - py.log(self.data[idx])) /
                  (self.time[idx + 3] - self.time[idx]))
            grs.append(gr)
        sortIdx = py.argsort(grs)[-2]  # Obtain index of desired growth rate
        maxGR = grs[sortIdx]
        t = self.time[sortIdx + 2]  # Add 2 for mid window of MGR
        return maxGR, t

    def calcLag(self):
        '''Obtain the value of the lag phase using best fit model'''
        logisticData, lag, sseF = Models(self.dataMed, self.dataMed[1],
                                         self.maxGrowthRate, self.mgrTime,
                                         self.asymptote, self.time).Logistic()
        return logisticData, lag

    def calcGrowth(self):
        '''Calculate growth level using an adjusted harmonic mean'''
        return len(self.dataLogistic) / py.sum([(1 / (x + self.asymptote))
                                                for x in self.dataLogistic])
