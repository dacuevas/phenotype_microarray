#!/usr/bin/python

"""
Created on Tue May 1 2012
@author Garza

This script analyses data from Phenotypic Microarrays.
It determines a logistic growth model to describe the data.
Three biologically relevant variables are derivated from the model: the lag phase, the maximum rate of growth
and the asymptote.
Curves are compared to a control through an antilogarithmic ratio,
which scores the curves and predicts if the performance of a clone is better,
the same, or worse than a control.
Further, the growth conditions of each clone are evaluated through the biomass production and the harmonic mean
(wich expresses the average rate of growth),  and each condition is classified into A, B, C, D, or E.
A being the best and E the worst.
A multiple comparison of growth conditions to each clone is undertaken and a similarity matrix is constructed.
The output contains all of the growth parameters, the average and standard deviation of replicates,
the logistic model, the comparison of real-data with the model and the similarity matrix.

"""

#1) Necessary python Modules


#try:
#    from xlrd import * #module to import and use excel data
#except:
#    ImportError
#    print 'please install the xlrd and xlwt modules  (http://www.python-excel.org)'
#try:
#    from xlwt import * #module to write xls files (both, xlrd and xlwt, are available at (xls files)http://www.python-excel.org/)
#except:
#    ImportError
#    print 'please install the xlrd and xlwt modules  (http://www.python-excel.org)'

try:
    from pylab import * #module to work with many numeric computation facilities such as arrays and matrices (http://www.scipy.org/PyLab)
except:
    ImportError
    print 'please install the pylab module (http://www.scipy.org/PyLab)'

try:
    from ASV import * #module to read and write TSV (soon the xlrd and xlwt modules will be replaced by the use  of only this ASV module)
except:
    ImportError
    print 'please install the ASV module (http://tratt.net/laurie/src/python/asv/)'



# Using command line arguments to capture what used to be user input values
import sys, getopt, os

def usage():
	print "\nusage: %s -i inputfile -o outputname -n output_directory\n\n" % os.path.basename(sys.argv[0])

input_file = None
output_file_name = None # Prefix for all output files
output_dir = None
filterFlag = False
newHMFlag = False
window_size = 3
try:
	opts, args = getopt.getopt(sys.argv[1:],"fhi:o:n:z")
except getopt.GetoptError:
	usage()
	sys.exit(2)
for opt, arg in opts:
    if opt == "-h":
        usage()
        sys.exit(2)
    elif opt == "-i":
        input_file = arg
    elif opt == "-o":
        output_file_name = arg
    elif opt == "-n":
        output_dir = arg
    elif opt == "-f":
        filterFlag = True
    elif opt == "-z":
        newHMFlag = True
    else:
        pass

# Check if arguments were not given
if not input_file or not output_file_name or not output_dir:
	usage()
	sys.exit(2)


#2) User Inputs:

#The window size is the number of points that will be used to evaluate the maximun rate of growth.
#This number is going to form overlapping windows, walking one time point, from which the maximum growth rate will be chosen.
#Only interger larger than three can be used as windows.

###try:
###    window_size = int(raw_input("Enter an integer larger than 2 for an overlapping window size:   "))
###    while window_size <= 2:
###        print '\n It has to be an interger larger than 2!\n\n'
###        window_size = int(raw_input("Enter an integer larger than 2 for an overlapping window size:   "))
###
###except ValueError:
###    print '\nInvalid character! It has to be an interger\n\n'
###    window_size = int(raw_input("Enter an integer larger than 2 for an overlapping window size:   "))
###    while window_size <= 2:
###        print '\n It has to be an interger larger than 2!\n\n'
###        window_size = int(raw_input("Enter an integer larger than 2 for an overlapping window size:   "))


#the input file has to be a correctly formated TSV file
#input_file = str(raw_input("""\n\nEnter a correctly formated TSV dataset file-name:  """))

#the ouput file, named by the user is a XLS file with multiple sheets containig the results.
#output_file_name = str(raw_input("Enter a name for your output file:   "))


#3) Functions:

#variables named 'iteration_blocks' are lists of numbers that are exentensivly used as iteration indexes
#mainly to build new sublists from lists.

def indexes_from_iteration_block(iteration_block,indexes_list):
    '''Creates a list that adds next elements in a way that every index is a sum of the last'''
    for x in range(len(iteration_block)):
            indexes_list.append(iteration_block[x]+indexes_list[x])


def sublist_by_iteration_set(some_list, list_of_iteration_steps, new_groupment):
    '''function to group elements of a list according to indexes provided.
    these indexes go from the last element, to a new sum of elements'''
    for i in range(1, len(list_of_iteration_steps)):
        new_groupment.append(some_list[list_of_iteration_steps[i-1]:list_of_iteration_steps[i]])


def frequency_of_elements(list1, list2, list3):
    '''determines the frequency of elements from list2 in list1 and stores it in list3'''
    for i in list1:
        e = list2.count(i)
        list3.append(e)
    return list3

def unique_list(some_list, uniq_list):
    '''determines and stores the uniq_list of elements from a list, in the order
    of the first time they appear'''
    for e in some_list:
        if e not in uniq_list:
            uniq_list.append(e)
    return uniq_list
def reorder_multiples(list_to_reorder, multiple, reordered_list):
    '''function to reorganize a list according to a multiple'''
    a = -1
    while a< multiple - 1:
        a+=1
        for i in range(a, len(list_to_reorder), multiple):
            reordered_list.append(list_to_reorder[i])


def pairwise_groupment(list_of_lists, pairwise):
    '''Create all possible paiwise cobinations of sublists in a list'''
    a=-1
    while a<len(list_of_lists):
        a+=1
        for i in range (a+1, len(list_of_lists)):
            pairwise.append((list_of_lists[a], list_of_lists[i]))


def list_to_col(given_list, sheet, col_start, row_start, interval):
    '''writes a list in columns, the row and column of the start is determined, as well as
       the interval between'''
    for i in range(0,len(given_list)*interval, interval):
        sheet.write(row_start + i, col_start, given_list[i/interval])

def list_to_row(given_list, sheet, col_start, row_start, interval):
    '''writes a list in rows'''
    for i in range(0,len(given_list)*interval, interval):
        sheet.write(row_start, col_start + i, given_list[i/interval])



#4) Classes:

#a) Experiment:
# see the instructions for the correct formating of the input file.
# Lists such as META, different_clones, different_growth_conditions, and others, are stored every time the program is executed.
# this allows the construction of many graphs and calculations straight from the command-line in a python shell.

class Experiment:
    '''instance returns data from the input file'''
    def __init__(self, META):
        self.META = META #A META table is a list that contains all of the data from an input file. The rows are stored in nested lists.
                         #Whenever this class is informed, other input files can be uploaded and evaluated by its methods.
                         # They can also be stored in other names to call the program's other classes and methods.

    def different_clones(self, different_clones, clone_row):
        '''returns one list with the different clones of the experiment and a list of all the clones in the clone_row'''

        clone_row.extend(META[0][1:])
        unique_list(clone_row, different_clones)

    def different_main_nutrient_source(self, different_main_nutrient_source, main_nutrient_source_row):
        '''returns one list with the different main nutrient sources and one with all of the main nutrient source row'''

        main_nutrient_source_row.extend(META[1][1:])
        unique_list(main_nutrient_source_row, different_main_nutrient_source)

    def different_growth_conditions(self, different_growth_conditions, growth_conditions_row):
        '''returns one list with the different growth conditions of the experiment and a list of the entire growth condition row'''
        growth_conditions_row.extend(META[2][1:])
        __growth_conditions = zip(main_nutrient_source_row,growth_conditions_row)
        unique_list(__growth_conditions, different_growth_conditions)

    def different_wells(self, different_wells, wells_row):
        '''returns one list with the different wells of the experiment and one with all the experiment's well'''
        wells_row.extend(META[3][1:])
        unique_list(wells_row, different_wells)

    def time_vector(self, experiment_time, time_vector = None):
        '''returns a list with the time points of the experiment, or a vector with the total time of the
            experiment divided into intervals of length 25(can be easly editable if more or less memory is available).
            This vector can be used to achieve more precision while determining the lag phase.'''
        __experiment_time = []
        for i in META:
            __experiment_time.append(i[0])
        for i in __experiment_time[4:]:
            experiment_time.append(float(i))
###        for x in range(0, experiment_time[-1], 25):
###            time_vector.append(x)
        # 0.4 is approximately 25 minutes
        for x in arange(0, experiment_time[-1], 0.4):
            time_vector.append(x)


#b) Experiment Unit

class ExperimentUnit:
    '''instance to parse data from the sets, identifying technical replicates and returning
    parameters for an unit of the experiment that each analyzes curve contains, such as the average of each OD600 measure,
    its standard deviation, a maximum growth-rate and an asymptote.'''

    def __init__(self, META = None):
        self.META = META

    def filter(self, filterList, rawTypes):
        '''creates a list of replicates that do not pass the filter'''
        numDataVals = len(self.META) - 5  # Minus 5 to exclude first data rows
        numReps = len(self.META[1]) - 1  # Minus 1 to exclude row header
        data = []  # Holds all OD values
        # Create list of lists of data -- data[rep][val]
        for rep in range(1, numReps + 1):  # range() function is non-inclusive
            repIdx = rep - 1  # Idx for data array
            data.append([])
            for val in range(5, numDataVals + 5):
                data[repIdx].append(float(self.META[val][rep]))

        # Iterate through each and determine if they pass any filters
        for repIdx in range(numReps):
            clone = self.META[0][repIdx + 1]
            mainSource = self.META[1][repIdx + 1]
            substrate = self.META[2][repIdx + 1]
            repList = data[repIdx]

            # Linearity flag -- set to False if does not pass linearity tests
            linearFlag = True

            # Find asymptote using sliding window of three data points
            asym = 0
            asymPos = 0
            # Minus 2 because of non-inclusiveness and starting at pos 1
            for idx in range(1, numDataVals - 2):
                currAsym = mean(repList[idx:idx + 3])
                if asym < currAsym:
                    asym = currAsym
                    asymPos = idx + 1
            # Check that asymptote position is greater than 2 hours
            if asymPos > 3:
                try:
                    targetRate = (repList[asymPos + 1] - repList[asymPos - 1]) / 60
                except IndexError, e:
                    print >> sys.stderr, "asymPos = %d" % asymPos
                    print >> sys.stderr, "length = %d" % len(repList)
                    print >> sys.stderr, "numDataVals = %d" % numDataVals
                    print >> sys.stderr, e
                    sys.exit(1)
                targetPerc = targetRate * 0.30
                # Check that linearity between 2nd hour and point of asymptote
                for idx in range(3, asymPos - 1):
                    rate = repList[idx + 2] - repList[idx] / 60
                    if (rate < targetRate - targetPerc or
                        rate > targetRate + targetPerc):
                            linearFlag = False
                            break
            else:
                linearFlag = False


            # Misfits test -- starting OD within first 2 hours >= 0.18
            if [ i for (i,j) in enumerate(repList[:4]) if j >= 0.18 ]:
                rawTypes["Misfits"].append("%s_%s_%s" % (clone, mainSource, substrate))
                filterList.append(repIdx)

            # No Growth test -- 1 hour OD >= 24 hour OD + 0.03
            elif repList[1] >= repList[47] + 0.03:
                rawTypes["NoGrowth"].append("%s_%s_%s" % (clone, mainSource, substrate))
                filterList.append(repIdx)

            # Linear test -- linear flag pass earlier test
            elif linearFlag:
                rawTypes["Linear"].append("%s_%s_%s" % (clone, mainSource, substrate))

            # All tests passed -- Growth
            else:
                rawTypes["Growth"].append("%s_%s_%s" % (clone, mainSource, substrate))

    def rep_average(self, average_a, (x, y)):
        '''determines the average of replicates and stores in a list''' #(x, y) is a tupple with the index that corresponds to a replicates location
                                                                        #in the META file.

        __average_META = []
        for i in range(4, len(self.META)):
            __average_META.append(average(map(float, self.META[i][x:y])))#Convert META objects to float
        __iteration_block_1 = [len(META) - 4]
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        sublist_by_iteration_set(__average_META, __iteration_block_2, average_a) #average_a contains nested sublists of the
                                                                                 #average OD measures from replicates.
    def rep_median(self, filterList, average_a, (x, y)):
        '''determines the average of replicates and stores in a list''' #(x, y) is a tupple with the index that corresponds to a replicates location
                                                                        #in the META file.

        __average_META = []
        for i in range(4, len(self.META)):
            replicates = []
            for j in range(x, y):
                if j not in filterList:
                    replicates.append(self.META[i][j])
            if len(replicates) != 0:
                __average_META.append(median(map(float, replicates)))#Convert META objects to float
            else:
                __average_META.append(nan)
        __iteration_block_1 = [len(META) - 4]
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        sublist_by_iteration_set(__average_META, __iteration_block_2, average_a) #average_a contains nested sublists of the
                                                                                 #average OD measures from replicates.
    def rep_stdev(self, filterList, stdev_a, (x, y)):
        __stdev_META = []
        for i in range(4, len(self.META)):
            replicates = []
            for j in range(x, y):
                if j not in filterList:
                    replicates.append(self.META[i][j])
            if len(replicates) != 0:
                __stdev_META.append(array(map(float, replicates)).std())
            else:
                __stdev_META.append(nan)
        __iteration_block_1 = [len(META) - 4]
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        sublist_by_iteration_set(__stdev_META, __iteration_block_2, stdev_a) #average_a contains nested sublists of the
                                                                             #standard deviation from replicates.

    def asymptote(self, asymptote, average_a):
        '''the highest of 3 consecutive measures is selected as the asymptote'''
        __iteration_block_1 = [3] * len(average_a)
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        __consecutive_averages = []
        sublist_by_iteration_set(average_a, __iteration_block_2, __consecutive_averages)
        __consecutive_averages_av = []
        for i in __consecutive_averages:
            __consecutive_averages_av.append(sum(i)/3.0)
        __sorted_av = sorted(__consecutive_averages_av, reverse = True)
        asymptote.append(__sorted_av[0])

    def p2(self, p2, average_a):
        '''the second measure from average_a is selected as P2'''#the reason p2 is used as the first point in the curve is
                                                                 #because the mesure in time 0 is inconsistent with the rest
                                                                 #of the data, probably because temperature is not stabilized.
        p2.append(average_a[1])
    def max_growth_rate(self, window_size, max_growth_rate, average_a, experiment_time):
        '''the maximum growth rate is selected iterating over the overlapping windows'''
        __overlapped_time = []
        a = - 1
        b = window_size - 1
        while b <= len(experiment_time)-2:
                    a += 1
                    b += 1
                    __overlapped_time.append((experiment_time[a], experiment_time[b]))#a list of tupples containing time1 and time2

        __overlapped_od = []
        a = -1
        b = window_size - 1
        while b <= len(average_a)-2:
            a += 1
            b += 1
            __overlapped_od.append((array(average_a[a]), array(average_a[b])))#tupples average1 and average2

        __growth_rate = []
        for i in range(len(__overlapped_od)):#rate of growth is determined as the doubling time per minute U = 2.303*(log(OD2)-log(OD1))/(t2 - t1).
            __growth_rate.append(((2.303*(log10(__overlapped_od[i][1])-log10(__overlapped_od[i][0])))/(__overlapped_time[i][1] - __overlapped_time[i][0])))
        __sorted_growth_rate = []
        __sorted_growth_rate.append(sorted(__growth_rate, reverse = True))
        max_growth_rate.append(__sorted_growth_rate[0][1]) #the second highest is selected as the umax.
                                                           #To select a different one, change the second index.


#c) Logistic Model

class LogisticModel:
    '''determines a logistic model and its standard deviation'''
    def __init__(self, average_a, lag_time, asymptote, p2, max_growth_rate, experiment_time):
        self.average_a = average_a
        self.lag_time = lag_time
        self.asymptote = asymptote
        self.p2 = p2
        self.max_growth_rate = max_growth_rate
        self.experiment_time = experiment_time

    def model(self, model_y, model_stdev):
        __model_y = [] #list stores the predicted points of the model, which form an ordered pair with each time of the experiment
        __model_stdev = [] #the standard deviation is determined as the dispersion of the model points in comparison to the actual data
                            #y = p2 + (A-p2)/(1+exp((Um/A)*(L - t)+2)) (model)
                            #d = sum(((ydata - (ydata+ymodel)/2)**2)**0.5)/N (std dev.)

        for i in range(len(experiment_time)):
            __model_y.append(self.p2 + ((self.asymptote-self.p2)/(1 + exp(((self.max_growth_rate/self.asymptote)*(self.lag_time - experiment_time[i]))+2))))
        __list_of_squares = []
        for i in range(len(self.average_a)):
            __list_of_squares.append(pow((pow((self.average_a[i] - ((self.average_a[i]+__model_y[i])/2)),2)), 0.5))
        __model_stdev.append((sum(__list_of_squares))/len(self.average_a))
        model_y.append(__model_y)
        model_stdev.append(__model_stdev)


# d) Lag_phase

class Lag_phase_evaluation:
    '''instance to evaluate the best lag phase for the logistic model. It tests all the time points of a vector
       with the same total length as the experiment time'''
    def __init__(self, average_a, asymptote, p2, max_growth_rate, experiment_time, time_vector):
        self.average_a = average_a
        self.asymptote = asymptote
        self.p2 = p2
        self.max_growth_rate = max_growth_rate
        self.experiment_time = experiment_time
        self.time_vector = time_vector
    def lag_phase_selection(self, lag_phase):
        '''all of the points in the time vector are probed in search of the smallest standard deviation
        of the logistic model. the point with the smallest deviation is selected as the lag phase'''
        __model_y = []
        __stdev = []

        for i in self.time_vector:
            LogisticModel(self.average_a, i, self.asymptote, self.p2, self.max_growth_rate, self.experiment_time).model(__model_y, __stdev)
        __index = []
        __index.append(__stdev.index(min(__stdev)))
        for i in __index:
            lag_phase.append(time_vector[i])


# e) Experimental Groups

#experiment groups are sets of different clones that share the same growth condition and main nutrient source.

class ExperimentGroup:
    '''instance to compare experiment groups. an experiment group is a set of different clones grown under the same
        growth condition.'''
    def __init__(self, logistic_model_of_experiment_group = None):#logistic_model_of_experiment_group should be a list with
                                                                  #sublists of ordered y points of the logistic model from
                                                                  #the individuals of an experimental group.
        self.logistic_model_of_experiment_group = logistic_model_of_experiment_group
    def ratio(self, ratio): #the formula used to calculate the ratio is R=10**sum(log(yia/yib)/N.
        '''the ratio is a pairwise average of the ratio of clones compared under an antilogarithmic scale'''
        __list_of_logs = []
        for i in range(len(self.logistic_model_of_experiment_group)):
            for x in range(len(self.logistic_model_of_experiment_group[i])):
                __list_of_logs.append(log10(self.logistic_model_of_experiment_group[0][x]/self.logistic_model_of_experiment_group[i][x]))
        __iteration_block_1 = [len(self.logistic_model_of_experiment_group[0])]*len(self.logistic_model_of_experiment_group)
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        __list_of_logs_separated = []
        sublist_by_iteration_set(__list_of_logs, __iteration_block_2, __list_of_logs_separated)
        for i in __list_of_logs_separated:
            ratio.append(pow(10, sum(i)/len(self.logistic_model_of_experiment_group[0]))) #ratio =  10**sum(log(ycontrol/yexperiment)/
    def scores(self, ratio, scores): #the scores are a symmetrical distribution of the ratio within + or - 100%.
        for i in ratio:
            if i > 2:
                scores.append(-4)
            elif i > 1.75:
                scores.append(-3)
            elif i > 1.50:
                scores.append(-2)
            elif i > 1.25:
                scores.append(-1)
            elif i > 0.875:
                scores.append(0)
            elif i > 0.75:
                scores.append(1)
            elif i > 0.625:
                scores.append(2)
            elif i > 0.5:
                scores.append(3)
            else:
                scores.append(4)
    def predicted_performance(self, scores, predicted_performance):
        for i in scores:
            if i == -4 or i == -3 or i == -2:
                predicted_performance.append('worst')
            elif i == -1 or i == 0 or i == 1:
                predicted_performance.append('equal')
            elif i == 2 or i == 3 or i == 4:
                predicted_performance.append('better')


# g) Clone

class Clone:
    '''instance to analyze a clone with regard to its many growth conditions'''
    def __init__(self, logistic_model_by_clones = None, asymptote_by_clones = None, maxgrowthrate_by_clones = None):
        self.logistic_model_by_clones = logistic_model_by_clones
        self.asymptote_by_clones = asymptote_by_clones
        self.maxgrowthrate_by_clones = maxgrowthrate_by_clones
    def harmonic_mean(self, harmonic_mean): #The harmonic mean represents the average of rates of growth. In this method,
                                            #the asymptote is weighted atributing a higher mean to the clones that accumulate
                                            #more biomass H = N/(1**-1sum(yi+assymptote)
        __ratio = []
        for i in range(len(self.logistic_model_by_clones)):
            for x in range(len(self.logistic_model_by_clones[i])):
                if newHMFlag:
                    __ratio.append(1/(self.logistic_model_by_clones[i][x]+ self.asymptote_by_clones[i]*self.maxgrowthrate_by_clones[i]))
                else:
                    __ratio.append(1/(self.logistic_model_by_clones[i][x]+ self.asymptote_by_clones[i]))
        __iteration_block_1 = [len(self.logistic_model_by_clones[0])]*len(self.logistic_model_by_clones)
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        __ratio_by_clone = []
        sublist_by_iteration_set(__ratio, __iteration_block_2, __ratio_by_clone)
        for i in __ratio_by_clone:
            harmonic_mean.append(len(i)/sum(i))
    def harmonic_mean_other_method(self, harmonic_mean_other_method): #Through this metod, there is no weght given to the asymptote        __ratio = []
        __ratio = []
        for i in range(len(self.logistic_model_by_clones)):
            for x in range(len(self.logistic_model_by_clones[i])):
                __ratio.append(1/(self.logistic_model_by_clones[i][x]))
        __iteration_block_1 = [len(self.logistic_model_by_clones[0])]*len(self.logistic_model_by_clones)
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        __ratio_by_clone = []
        sublist_by_iteration_set(__ratio, __iteration_block_2, __ratio_by_clone)
        for i in __ratio_by_clone:
            harmonic_mean_other_method.append(len(i)/sum(i))

    def classification(self, harmonic_mean, classsification):#Grow conditions are classified according to to the value of the harmonic mean
                                                             #Class A are the best and D the worst.
        for i in harmonic_mean:
            if i >= 0.75:
                classification.append('Class A')
            elif i > 0.5:
                classification.append('Class B')
            elif i > 0.32:
                classification.append('Class C')
            else:
                classification.append('Class D')

    def classification_other_method(self, harmonic_mean_other_method, classification_other_method):
        for i in harmonic_mean_other_method:
            if i >= 0.333:
                classification_other_method.append('Class A')
            elif i > 0.256:
                classification_other_method.append('Class B')
            elif i > 0.180:
                classification_other_method.append('Class C')
            elif i > 0.105:
                classification_other_method.append('Class D')
            else:
                classification_other_method.append('Class E')





#g) Clustering

class Clustering:
    '''clusterin of clones by similarity indexes'''

    def __init__ (self, different_clones, different_growth_conditions, classification_by_clones):
        self.different_clones = different_clones
        self.different_growth_conditions = different_growth_conditions
        self.classification_by_clones = classification_by_clones

    def similarity_matrix(self, row_col, matrix):
        row_col.append([self.different_clones[:-1], self.different_clones[1:]])
        __pairwise = []                                         #all the classifications are grouped in all possible unique pairs
        __a=-1
        while __a < len(self.classification_by_clones) - 1:
            __a+=1
            for i in range(__a+1, len(self.classification_by_clones)):
                __pairwise.append((self.classification_by_clones[__a], self.classification_by_clones[i]))
        __dice = []
        for x in range(len(__pairwise)):                    #A modified Dice index is used to attribute similarity values.
                                                            #Exact macth score 2, distance of one letter score 1, and two letters
                                                            #score a 0.5. Distance of 3, scores 0.

            for i in range(len(__pairwise[0][0])):
				if __pairwise[x][0][i] == 'Class A':
					if __pairwise[x][1][i] == 'Class A':
						__dice.append(2)
					elif __pairwise[x][1][i] == 'Class B':
						__dice.append(1)
					elif __pairwise[x][1][i] == 'Class C':
						__dice.append(0.5)
					elif __pairwise[x][1][i] == 'Class D':
						__dice.append(0.0)

				elif __pairwise[x][0][i] == 'Class B':
					if __pairwise[x][1][i] == 'Class B':
						__dice.append(2)
					elif __pairwise[x][1][i] == 'Class A':
						__dice.append(1)
					elif __pairwise[x][1][i] == 'Class C':
						__dice.append(1)
					elif __pairwise[x][1][i] == 'Class D':
						__dice.append(0.5)

				elif __pairwise[x][0][i] == 'Class C':
					if __pairwise[x][1][i] == 'Class C':
						__dice.append(2)
					elif __pairwise[x][1][i] == 'Class A':
						__dice.append(0.5)
					elif __pairwise[x][1][i] == 'Class B':
						__dice.append(1)
					elif __pairwise[x][1][i] == 'Class D':
						__dice.append(1)

				elif __pairwise[x][0][i] == 'Class D':
					if __pairwise[x][1][i] == 'Class D':
						__dice.append(2)
					elif __pairwise[x][1][i] == 'Class A':
						__dice.append(0.0)
					elif __pairwise[x][1][i] == 'Class B':
						__dice.append(0.5)
					elif __pairwise[x][1][i] == 'Class C':
						__dice.append(1)
					elif __pairwise[x][1][i] == 'Class E':
						__dice.append(1)


        __b = len(__dice)/len(self.different_growth_conditions)
        __iteration_block_1 = [len(self.different_growth_conditions)] * __b
        __iteration_block_2 = [0]
        indexes_from_iteration_block(__iteration_block_1, __iteration_block_2)
        __dice_by_pairwise = []
        sublist_by_iteration_set(__dice, __iteration_block_2, __dice_by_pairwise)
        __similarity_index = []
        __c = len(self.different_growth_conditions)*2.0
        for i in __dice_by_pairwise:
            __similarity_index.append(sum(i)/__c)
        __iteration_block_3 = []
        for i in range(len(self.different_clones)-1, 0, -1):
            __iteration_block_3.append(i)
        __iteration_block_4 = [0]
        indexes_from_iteration_block(__iteration_block_3, __iteration_block_4)
        sublist_by_iteration_set(__similarity_index, __iteration_block_4, matrix)

class Pearson:
    '''Correlate pairwise groupments using Pearson correlation'''
    def __init__ (self, two_sublists):
	     self.two_sublists = two_sublists

    def pearson_correlation(self, correlation):
        __A = []
        __B = []
        __C = []

        for i in range(len(self.two_sublists[0])):
            __A.append((self.two_sublists[0][i]-average(self.two_sublists[0]))*(self.two_sublists[1][i] - average(self.two_sublists[1])))
            __B.append(pow(self.two_sublists[0][i]-average(self.two_sublists[0]), 2))
            __C.append(pow(self.two_sublists[1][i]-average(self.two_sublists[1]), 2))
        __P = sum(__A)
        __Q = pow(sum(__B)*sum(__C),0.5)

        correlation.append(1-__P/__Q)

#h) Plots???

#5) Program


#Input is used to create META
print "Parsing '%s'\t\t\t\t(step 1/9)" % os.path.basename(input_file)
sys.stdout.flush()
META = ASV()
META.input_from_file(input_file, TSV())

#List with the different clones, different main nutrient source, different growth conditions, wells, and time
#are created. These lists can be further used to determine the experimental groups and write the output file.
#They can also ne used in the construction of plots from the comand-line.

experiment = Experiment(META)
different_clones = []
clone_row = []
experiment.different_clones(different_clones, clone_row = clone_row)


different_main_nutrient_source =[]
main_nutrient_source_row = []
experiment.different_main_nutrient_source(different_main_nutrient_source, main_nutrient_source_row)


different_growth_conditions = []
growth_conditions_row = []
experiment.different_growth_conditions(different_growth_conditions, growth_conditions_row = growth_conditions_row)


different_wells = []
wells_row = []
experiment.different_wells(different_wells, wells_row)


experiment_time = []
time_vector = []
experiment.time_vector(experiment_time, time_vector = time_vector)


print "Creating experiment data structures\t\t\t(step 2/9)"
sys.stdout.flush()
#The different experiment groups are identified.
all_experiment_groups = zip(clone_row, main_nutrient_source_row, growth_conditions_row, wells_row)
# pair-wise grouping of the clone_row, the growth condition row, and the main nutrient source row
different_experiment_groups = []
unique_list(all_experiment_groups, different_experiment_groups)
# the grouping of clone + main nutrient source + growth condition is the unique key that separates
#the data into unique experimental groups.
frequency_of_experiment_groups = []
frequency_of_elements(different_experiment_groups, all_experiment_groups, frequency_of_experiment_groups)
iteration_block_for_replicates = [0]
indexes_from_iteration_block(frequency_of_experiment_groups, iteration_block_for_replicates)

iteration_block_for_replicates_average =[]#list of tuples that correspond to the position of technical replicates in META
a=0
b =-1
while a< len(iteration_block_for_replicates)-1:
    a+=1
    b+=1
    iteration_block_for_replicates_average.append((iteration_block_for_replicates[b]+1, iteration_block_for_replicates[a]+1))


#technical replicates are averaged and the standard deviation value is stored in a list
average_of_replicates = []
stdev_of_replicates = []

print "Calculating asymptotes and growth rates\t\t\t(step 3/9)"
sys.stdout.flush()
#Biological parameters are determined and stored in lists
asymptote = []
p2 = []
max_growth_rate = []
filterList = []
if filterFlag:
    rawTypes = {"Misfits" : [], "NoGrowth" : [], "Linear" : [], "Growth" : []}
    ExperimentUnit(META = META).filter(filterList,rawTypes)
for i in iteration_block_for_replicates_average:
	ExperimentUnit(META = META).rep_median(filterList, average_of_replicates, i)
	ExperimentUnit(META = META).rep_stdev(filterList, stdev_of_replicates, i)
for i in average_of_replicates:
    ExperimentUnit().asymptote(asymptote, i)
    ExperimentUnit().p2(p2, i)
    ExperimentUnit().max_growth_rate(window_size, max_growth_rate, i, experiment_time)

print "Calculating lag phases\t\t\t\t\t(step 4/9)"
sys.stdout.flush()
#the Lag_phase_evaluation class is used to probe the points of the time vector with in the logistic model
#searching for the one wit the least standard deviation.
lag_phase = []
for i in range(len(average_of_replicates)):
	Lag_phase_evaluation(average_of_replicates[i], asymptote[i], p2[i], max_growth_rate[i], experiment_time, time_vector).lag_phase_selection(lag_phase)


print "Creating logistic models\t\t\t\t(step 5/9)"
sys.stdout.flush()
#With the biological parameters determined. The data is fitted into a logistic model that will be used to compare samples.
best_logistic_model = []
best_logistic_model_std = []
for i in range(len(average_of_replicates)):
    LogisticModel(average_of_replicates[i], lag_phase[i], asymptote[i], p2[i], max_growth_rate[i], experiment_time).model(best_logistic_model, best_logistic_model_std)

#The model of each sample is compared to a control. Assumed to be first experimental group.
iteration_block_for_experiment_groups_1 = [len(different_clones)]*len(different_growth_conditions)
iteration_block_for_experiment_groups_2 = [0]
indexes_from_iteration_block(iteration_block_for_experiment_groups_1, iteration_block_for_experiment_groups_2)
best_logistic_model_by_experiment_groups = []
sublist_by_iteration_set(best_logistic_model, iteration_block_for_experiment_groups_2, best_logistic_model_by_experiment_groups)

ratio = []
scores = []
predicted_performance = []

for i in best_logistic_model_by_experiment_groups:
    ExperimentGroup(logistic_model_of_experiment_group = i).ratio(ratio)

ExperimentGroup().scores(ratio,scores)

ExperimentGroup().predicted_performance(scores, predicted_performance)


#How well a clone does with the analyzed growth conditions is determined and compared among clones.
logistic_model_ordered_by_clones = []
logistic_model_by_clones = []
asymptote_ordered_by_clones = []
asymptote_by_clones = []
maxgrowthrate_ordered_by_clones = []
maxgrowthrate_by_clones = []
a=-1
while a < len(different_clones)-1:
	a +=1
	for i in range(a, len(best_logistic_model), len(different_clones)):
		logistic_model_ordered_by_clones.append(best_logistic_model[i])


a=-1
while a < len(different_clones)-1:
	a +=1
	for i in range(a, len(asymptote), len(different_clones)):
		asymptote_ordered_by_clones.append(asymptote[i])
		maxgrowthrate_ordered_by_clones.append(max_growth_rate[i])
iteration_block_for_clones_1 = [len(different_growth_conditions)]*len(different_clones)
iteration_block_for_clones_2 = [0]
indexes_from_iteration_block(iteration_block_for_clones_1, iteration_block_for_clones_2)
sublist_by_iteration_set(logistic_model_ordered_by_clones, iteration_block_for_clones_2, logistic_model_by_clones)
sublist_by_iteration_set(asymptote_ordered_by_clones, iteration_block_for_clones_2, asymptote_by_clones)
sublist_by_iteration_set(maxgrowthrate_ordered_by_clones, iteration_block_for_clones_2, maxgrowthrate_by_clones)


print "Calculating harmonic means and classifications\t\t(step 6/9)"
sys.stdout.flush()
harmonic_mean = []
harmonic_mean_b = []
classification = []
classification_b = []
for i in range(len(logistic_model_by_clones)):
    Clone(logistic_model_by_clones = logistic_model_by_clones[i],
          asymptote_by_clones = asymptote_by_clones[i],
          maxgrowthrate_by_clones = maxgrowthrate_by_clones[i]).harmonic_mean(harmonic_mean)

Clone().classification(harmonic_mean, classification)

for i in range(len(logistic_model_by_clones)):
    Clone(logistic_model_by_clones = logistic_model_by_clones[i], asymptote_by_clones = asymptote_by_clones[i]).harmonic_mean_other_method(harmonic_mean_b)

Clone().classification_other_method(harmonic_mean_b, classification_b)
classification_by_clones = []
sublist_by_iteration_set(classification, iteration_block_for_clones_2, classification_by_clones)


print "Calculating Dice similarity matrices\t\t\t(step 7/9)"
sys.stdout.flush()
sim_matrix_row_col = []
sim_matrix = []
f = Clustering(different_clones, different_growth_conditions, classification_by_clones)
f.similarity_matrix(sim_matrix_row_col, sim_matrix)


harmonic_mean_by_clones = []
sublist_by_iteration_set(harmonic_mean, iteration_block_for_clones_2, harmonic_mean_by_clones)
paired_list = []
pairwise_groupment(harmonic_mean_by_clones, paired_list)


print "Calculating Pearson correlations\t\t\t(step 8/9)"
sys.stdout.flush()
correlation = []
for i in paired_list:
    Pearson(i).pearson_correlation(correlation)
iteration_block_for_pearson = []
for i in range(1, len(different_clones)):
    iteration_block_for_pearson.append(i)
iteration_block_for_pearson = iteration_block_for_pearson[::-1]
iteration_block_for_pearson_2 = [0]
indexes_from_iteration_block(iteration_block_for_pearson, iteration_block_for_pearson_2)
pearson_matrix = []
sublist_by_iteration_set(correlation, iteration_block_for_pearson_2, pearson_matrix)


print "Writing output files\t\t\t\t\t(step 9/9)"
sys.stdout.flush()
# 6)write the output file


# a)output_sheet_1: comparison to control

outfile = open("%s/comparisons.txt" % output_dir,"w")
outfile.write("\t".join(["clone","mainsource","growthcondition","well","lagphase","maximumgrowthrate",
	"asymptote","modelstdev","ratio","score","predictedperformance"]))
outfile.write("\n")

for index in range(len(different_experiment_groups)):
	expgroup = different_experiment_groups[index]
	outfile.write("\t".join(str(x) for x in [expgroup[0],expgroup[1],expgroup[2],expgroup[3],lag_phase[index],
			round(max_growth_rate[index],4),asymptote[index],round(best_logistic_model_std[index][0],4),
			round(ratio[index],4),scores[index],predicted_performance[index]]))
	outfile.write("\n")
outfile.close()

#Output file 2: Growth Conditions Classification:

experiment_groups_by_clones = []
a=-1
while a < len(different_clones)-1:
	a +=1
	for i in range(a, len(different_experiment_groups), len(different_clones)):
		experiment_groups_by_clones.append(different_experiment_groups[i])

outfile = open("%s/classifications.txt" % output_dir,"w")
outfile.write("\t".join(["clone","mainsource","growthcondition","well","harmonicmean","growthclass",
	"mean_no_asymptote","growthclass_no_asymptote"]))
outfile.write("\n")

for index in range(len(experiment_groups_by_clones)):
	expgroup = experiment_groups_by_clones[index]
	outfile.write("\t".join(str(x) for x in [expgroup[0],expgroup[1],expgroup[2],expgroup[3],harmonic_mean[index],
			classification[index],harmonic_mean_b[index],classification_b[index]]))
	outfile.write("\n")
outfile.close()

#Output file 3: Similarity Matrix using the Dice coefficient on qualitative data

outfile = open("%s/dice_similiarity.txt" % output_dir,"w")
outfile.write("\t")
outfile.write("\t".join(str(x) for x in sim_matrix_row_col[0][0]))
outfile.write("\n")
for index in range(len(sim_matrix_row_col[0][1])):
	outfile.write(str(sim_matrix_row_col[0][1][index]))

	# Each sim_matrix element represents a column in the half-matrix
	# thus, each element is a different length list
	# e.g. sm[0][0]
	#      sm[0][1]   sm[1][0]
	#      sm[0][2]   sm[1][1]   sm[2][0]
	#      sm[0][3]   sm[1][2]   sm[2][1]   sm[3][0]
	first_idx = 0
	second_idx = index
	while second_idx >= 0:
		outfile.write("\t%f" % sim_matrix[first_idx][second_idx])
		first_idx += 1
		second_idx -= 1
	outfile.write("\n")
outfile.close()

#Output file 4: Similarity Matrix using the Dice coefficient on qualitative data

outfile = open("%s/pearson_similarity.txt" % output_dir,"w")
outfile.write("\t")
outfile.write("\t".join(str(x) for x in sim_matrix_row_col[0][0]))
outfile.write("\n")
for index in range(len(sim_matrix_row_col[0][1])):
	outfile.write(str(sim_matrix_row_col[0][1][index]))

	# Each pearson_matrix element represents a column in the half-matrix
	# thus, each element is a different length list
	# e.g. pm[0][0]
	#      pm[0][1]   pm[1][0]
	#      pm[0][2]   pm[1][1]   pm[2][0]
	#      pm[0][3]   pm[1][2]   pm[2][1]   pm[3][0]
	first_idx = 0
	second_idx = index
	while second_idx >= 0:
		outfile.write("\t%f" % pearson_matrix[first_idx][second_idx])
		first_idx += 1
		second_idx -= 1
	outfile.write("\n")
outfile.close()

#Output file 5: Replicate Averages

outfile = open("%s/replicate_median.txt" % output_dir,"w")
outfile.write("time\t\t")
outfile.write("\t".join(str(x) for x in experiment_time))
outfile.write("\n")

expgroupidx = 0
for index in range(len(different_experiment_groups)*2):
	expgroup = different_experiment_groups[expgroupidx]
	if index % 2 == 0:
		outfile.write("%s\tmedian\t" % expgroup[0])
		outfile.write("\t".join(str(x) for x in average_of_replicates[expgroupidx]))
	else:
		outfile.write("%s\tstd_dev\t" % expgroup[2])
		outfile.write("\t".join(str(x) for x in stdev_of_replicates[expgroupidx]))
		expgroupidx += 1
	outfile.write("\n")
outfile.close()


# Outputfile 6:the Logistic Model

outfile = open("%s/logistic_model.txt" % output_dir,"w")
outfile.write("time\t")
outfile.write("\t".join(str(x) for x in experiment_time))
outfile.write("\n")
for index in range(len(different_experiment_groups)):
	expgroup = different_experiment_groups[index]
	outfile.write("\t".join(str(x) for x in [expgroup[0],expgroup[3]]))
	outfile.write("\t")
	outfile.write("\t".join(str(x) for x in best_logistic_model[index]))
	outfile.write("\n")
outfile.close()


# Ouput file 7: Real Data X Logistic Model

outfile = open("%s/model_x_realdata.txt" % output_dir,"w")
outfile.write("time\t\t")
outfile.write("\t".join(str(x) for x in experiment_time))
outfile.write("\n")

expgroupidx = 0
for index in range(len(different_experiment_groups)*2):
	expgroup = different_experiment_groups[expgroupidx]
	if index % 2 == 0:
		outfile.write("%s\trealdata\t" % expgroup[0])
		outfile.write("\t".join(str(x) for x in average_of_replicates[expgroupidx]))
	else:
		outfile.write("%s\tlogisticmodel\t" % expgroup[2])
		outfile.write("\t".join(str(x) for x in best_logistic_model[expgroupidx]))
		expgroupidx += 1
	outfile.write("\n")
outfile.close()


# Output file 8: Filters
if filterFlag:
    outfile = open("%s/filter_info.txt" % output_dir,"w")
    outfile.write("clone\tmainsource\tsubstrate\tfiltergroup\n")
    for name in rawTypes["Misfits"]:
        clone, mainsource, substrate = name.split("_")
        outfile.write("%s\t%s\t%s\tmisfits\n" % (clone, mainsource, substrate))

    for name in rawTypes["NoGrowth"]:
        clone, mainsource, substrate = name.split("_")
        outfile.write("%s\t%s\t%s\tnogrowth\n" % (clone, mainsource, substrate))

    for name in rawTypes["Linear"]:
        clone, mainsource, substrate = name.split("_")
        outfile.write("%s\t%s\t%s\tlinear\n" % (clone, mainsource, substrate))

    for name in rawTypes["Growth"]:
        clone, mainsource, substrate = name.split("_")
        outfile.write("%s\t%s\t%s\tgrowth\n" % (clone, mainsource, substrate))
    outfile.close()


# Create heatmap
harmonic_mean_matrix = []
sublist_by_iteration_set(harmonic_mean, iteration_block_for_clones_2, harmonic_mean_matrix)
harmonic_mean_matrix = array(harmonic_mean_matrix)

# Plot the imagine with the values for the harmonic means in rows, and colored by similarity.
imshow(harmonic_mean_matrix, interpolation = 'nearest', extent = [0, len(different_growth_conditions)*3, 0, len(different_clones)*4])

#Create a separate list of names for compounds, separated from their nutrient sources.
compounds = []
for i in range(len(different_growth_conditions)):
	compounds.append(different_growth_conditions[i][1]) # May change the [1] for a [0] if you want to plot the source instead of the compound.

xticks(arange(1.5, len(different_growth_conditions)*3, 3), compounds, fontsize = 4, rotation = 90)
yticks(range(2,len(different_clones)*4, 4), different_clones[::-1], fontsize = 4)
tick_params(length = 0)
cbar = colorbar(orientation = 'vertical', extend = 'both', spacing = 'uniform', drawedges = False, shrink = 0.4, ticks = [1.2, 0.6])
cbar.set_ticklabels(['Growth', 'No Growth'])
for i in cbar.ax.get_yticklabels():
	i.set_fontsize(8)

savefig("%s/%s_heatmap.png" % (output_dir,output_file_name), dpi=300, figsize = (15,15))

