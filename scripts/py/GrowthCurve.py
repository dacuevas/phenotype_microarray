# GrowthCurve.py
# Bacteria growth curve class to extract parameters
# Use with Phenotype MicroArray analysis pipeline
#
# Author: Daniel A Cuevas
# Created on 21 Nov. 2013
# Updated on 28 Dec. 2013


import pylab as py
import Models


class GrowthCurve:
    '''Bacteria growth curve class'''
    def __init__(self, data, time):
        self.dataReps = data  # OD data values (replicates implied)
        self.dataMed = py.median(self.dataReps, axis=0)
        self.time = time  # time values
        self.asymptote = self.__calcAsymptote()
        self.maxGrowthRate, self.mgrTime = self.__calcMGR()
        self.dataLogistic, self.lag = self.__calcLag()
        self.growthLevel = self.__calcGrowth()

    def __calcAsymptote(self):
        '''Obtain the value of the highest OD reading'''
        stop = len(self.time) - 3
        maxA = -1
        for idx in xrange(1, stop):
            av = py.mean(self.dataMed[idx:idx + 3])
            if av > maxA:
                maxA = av
        return maxA

    def __calcMGR(self):
        '''Obtain the value of the max growth'''
        stop = len(self.time) - 4
        #grs = []
        maxGR = 0
        for idx in xrange(1, stop):

            # Growth rate calculation
            # (log(i+3) - log(i)) / (time(i+3) - time(i))
            gr = ((py.log(self.dataMed[idx + 3]) - py.log(self.dataMed[idx])) /
                  (self.time[idx + 3] - self.time[idx]))
            #grs.append(gr)
            if idx == 1 or gr > maxGR:
                maxGR = gr
                t = self.time[idx + 2]
        #sortIdx = py.argsort(grs)[-2]  # Obtain index of desired growth rate
        #maxGR = grs[sortIdx]
        #t = self.time[sortIdx + 2]  # Add 2 for mid window of MGR
        return maxGR, t

    def __calcLag(self):
        '''Obtain the value of the lag phase using best fit model'''
        logisticData, lag, sseF = Models.Models(self.dataMed, self.dataMed[1],
                                                self.maxGrowthRate,
                                                self.mgrTime, self.asymptote,
                                                self.time).Logistic()
        return logisticData, lag

    def __calcGrowth(self):
        '''Calculate growth level using an adjusted harmonic mean'''
        return len(self.dataLogistic) / py.sum([(1 / (x + self.asymptote))
                                                for x in self.dataLogistic])
