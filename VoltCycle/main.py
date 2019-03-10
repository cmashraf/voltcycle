# main functions we have used so far

import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import warnings
import matplotlib.cbook
import peakutils
import copy
from matplotlib import rcParams



def read_cycle(data):
    """This function reads a segment of datafile (corresponding a cycle)
    and generates a dataframe with columns 'Potential' and 'Current'

    Parameters
    __________
    data: segment of data file

    Returns
    _______
    A dataframe with potential and current columns  
    """     

    current = []
    potential = []
    for i in data[3:]:
        current.append(float(i.split("\t")[4]))
        potential.append(float(i.split("\t")[3]))
    zippedList = list(zip(potential, current))
    df = pd.DataFrame(zippedList, columns = ['Potential' , 'Current'])
    return df


def read_file(file):
    """This function reads the raw data file, gets the scanrate and stepsize
    and then reads the lines according to cycle number. Once it reads the data
    for one cycle, it calls read_cycle function to generate a dataframe. It 
    does the same thing for all the cycles and finally returns a dictionary,
    the keys of which are the cycle numbers and the values are the 
    corresponding dataframes.

    Parameters
    __________
    file: raw data file

    Returns:
    ________
    dict_of_df: dictionary of dataframes with keys = cycle numbers and
    values = dataframes for each cycle
    n_cycle: number of cycles in the raw file  
    """   
    dict_of_df = {} 
    h = 0
    l = 0
    n_cycle = 0
    #a = []
    with open(file, 'rt') as f:
        print(file + ' Opened')
        for line in f:
            record = 0
            if not (h and l):
                if line.startswith('SCANRATE'):
                    scan_rate = float(line.split()[2])
                    h = 1
                if line.startswith('STEPSIZE'):
                    step_size = float(line.split()[2])
                    l = 1
            if line.startswith('CURVE'):
                n_cycle += 1
                if n_cycle > 1:
                    number = n_cycle - 1
                    df = read_cycle(a)
                    key_name = 'cycle_' + str(number)
                    #key_name = number
                    dict_of_df[key_name] = copy.deepcopy(df)
                a = []
            if n_cycle:
                a.append(line)
    return dict_of_df, number


#df = pd.DataFrame(list(dict1['df_1'].items()))
#list1, list2 = list(dict1['df_1'].items())
#list1, list2 = list(dict1.get('df_'+str(1)))

def data_frame(dict_cycle, n):
    """Reads the dictionary of dataframes and returns dataframes for each cycle

    Parameters
    __________
    dict_cycle: Dictionary of dataframes
    n: cycle number

    Returns:
    _______
    Dataframe correcponding to the cycle number 
    """
    list1, list2 = (list(dict_cycle.get('cycle_'+str(n)).items()))
    zippedList = list(zip(list1[1], list2[1]))
    data  = pd.DataFrame(zippedList, columns = ['Potential' , 'Current'])
    return data
def plot(dict, n):
    """For basic plotting of the cycle data
  
    Parameters
    __________
    dict: dictionary of dataframes for all the cycles
    n: number of cycles

    Saves the plot in a file called cycle.png 
    """

    for i in range(n):
        print(i+1)
        df = data_frame(dict_cycle, i+1)
        plt.plot(df.Potential, df.Current, label = "Cycle{}".format(i+1))
        
    
    plt.xlabel('Voltage')
    plt.ylabel('Current')
    plt.legend()
    plt.savefig('cycle.png')
    print('executed')


dict_cycle, n_cycle  = read_file('test.txt')
rcParams.update({'figure.autolayout': True})
plot(dict_cycle, n_cycle)


#split forward and backward sweping data, to make it easier for processing.
def split(vector):
    """
    This function takes an array and splits it into two half.
    """
    split = int(len(vector)/2)
    end = int(len(vector))
    vector1 = np.array(vector)[0:split]
    vector2 = np.array(vector)[split:end]
    return vector1, vector2

def critical_idx(x, y): ## Finds index where data set is no longer linear 
    """
    This function takes x and y values callculate the derrivative of x and y, and calculate moving average of 5 and 15 points.
    Finds intercepts of different moving average curves and return the indexs of the first intercepts.
    """
    k = np.diff(y)/(np.diff(x)) #calculated slops of x and y

    ## Calculate moving average for 5 and 15 points.
    ## This two arbitrary number can be tuned to get better fitting.
    ave5 = []
    ave15 = []
    for i in range(len(x)-5):  # The reason to minus 5 is to prevent j from running out of index.
        a = 0 
        for j in range(0,5):
            a = a + k[i+j]
        ave5.append(round(a/5, 9)) # keeping 9 desimal points for more accuracy
    ave5 = np.asarray(ave5)
    for i in range(len(x)-15): 
        b = 0 
        for j in range(0,15):
            b = b + k[i+j]
        ave15.append(round(b/15, 9))
    ave15 = np.asarray(ave15)
    ## Find intercepts of different moving average curves
    idx = np.argwhere(np.diff(np.sign(ave15 - ave5[:len(ave15)])!= 0)).reshape(-1) #reshape into one row.
    return int(idx[0])

def mean(vector):
    """
    This function returns the mean values.
    """
    a = 0
    for i in vector:
        a = a + i
    return a/len(vector)
      
def linear_coeff(x, y):
    """
    This function returns the inclination coeffecient and y axis interception coeffecient m and b. 
    """
    m = (y-mean(y)) / (x - mean(x))    
    b = mean(y) - m * mean(x)
    return m, b

def y_fitted_line(m, b, x):
    y_base = []
    for i in x:
        y = m * i + b
        y_base.append(y)
    return y_base    

def linear_background(x, y):
    idx = critical_idx(x, y) + 3 #this is also arbitrary number we can play with.
    m, b = linear_coeff(x[(idx - int(0.5 * idx)) : (idx + int(0.5 * idx))], y[(idx - int(0.5 * idx)) : (idx + int(0.5 * idx))])
    y_base = y_fitted_line(m, b, x)
    return y_base

def peak_detection(data_y):
    """ peak_detection(dataframe['y column'])
    This function returns a list of the indecies of the y values of the peaks detected in the dataset.
    The function takes an input of the column containing the y variables in the dataframe.
    This column is then split into two arrays, one of the positive and one of the negative values.
    This is because cyclic voltammetry delivers negative peaks however the peakutils function work better with positive peaks.
    The absolute values of each of these vectors are then imported into the peakutils.indexes
    function to determine the significant peak(s) for each array. The value(s) are then saved as a list."""
 
    index_list = []

    y1, y2 = split(data_y)

    peak_top = peakutils.indexes(abs(y1), thres=0.5, min_dist=0.001)
    peak_bottom = peakutils.indexes(abs(y2), thres=0.5, min_dist=0.001)
    index_list.append([peak_top[0], peak_bottom[0]])

    return index_list
def peak_potentials(data, index, potential_column_name):
    """Outputs potentials of given peaks in cyclic voltammetry data.

       Parameters
       ----------
       data : Must be in the form of a pandas DataFrame

       index : integer(s) in the form of a list or numpy array

       potential_column_name : the name of the column of the DataFrame
         which contains potentials from cyclic voltammogram. If a string,
         must be input with single or double quotation marks

       Returns
       -------
       Result : numpy array of potentials at peaks."""
    series = data.iloc[index][potential_column_name]
    potentials_array = (series).values
    return potentials_array


def del_potential(data, index, potential_column_name):
    """Outputs the difference in potentials between anodic and cathodic peaks
       in cyclic voltammetry data.

       Parameters
       ----------
       data : Must be in the form of a pandas DataFrame

       index : integer(s) in the form of a list or numpy array

       potential_column_name : the name of the column of the DataFrame
         which contains potentials from cyclic voltammogram. If a string,
         must be input with single or double quotation marks.

       Returns
       -------
       Results : difference in the form of a floating point number. """
    del_potential = (
        peak_potentials(data, index, potential_column_name)[1] -
        peak_potentials(data, index, potential_column_name)[0]
    )
    return del_potential


def half_wave_potential(data, index, potential_column_name):
    """Outputs the half wave potential(redox potential) from cyclic
       voltammetry data.

       Parameters
       ----------
       data : Must be in the form of a pandas DataFrame

       index : integer(s) in the form of a list or numpy array

       potential_column_name : the name of the column of the DataFrame
         which contains potentials from cyclic voltammogram. If a string,
         must be input with single or double quotation marks

       Returns
       -------
       Results : the half wave potential in the form of a
         floating point number."""
    half_wave_potential = (del_potential(data, index, potential_column_name))/2
    return half_wave_potential


def peak_currents(data, index, current_column_name):
    """Outputs currents of given peaks in cyclic voltammetry data.

       Parameters
       ----------
       data : Must be in the form of a pandas DataFrame

       index : integer(s) in the form of a list or numpy array

       current_column_name : the name of the column of the DataFrame
         which contains potentials from cyclic voltammogram. If a string,
         must be input with single or double quotation marks

       Returns
       -------
       Result : numpy array of currents at peaks"""
    series = data.iloc[index][current_column_name]
    currents_array = (series).values
    return currents_array


