import statistics
import pandas as pd
import validators
import numpy as np
from urllib.request import urlopen
import PAMI.extras.graph.plotLineGraphFromDictionary as plt


class temporalDatabaseStats:
    """
        Description:
        -------------
            temporalDatabaseStats is class to get stats of database.

        Attributes:
        ----------
        inputFile : file
            input file path
        database : dict
            store time stamp and its transaction
        lengthList : list
            store size of all transaction
        timeStampCount : dict
            number of transactions per time stamp
        periodList : list
            all period list in the database
        sep : str
            separator in file. Default is tab space.

        Methods:
        -------
        run()
            execute readDatabase function
        readDatabase()
            read database from input file
        getDatabaseSize()
            get the size of database
        getMinimumTransactionLength()
            get the minimum transaction length
        getAverageTransactionLength()
            get the average transaction length. It is sum of all transaction length divided by database length.
        getMaximumTransactionLength()
            get the maximum transaction length
        getStandardDeviationTransactionLength()
            get the standard deviation of transaction length
        getSortedListOfItemFrequencies()
            get sorted list of item frequencies
        getSortedListOfTransactionLength()
            get sorted list of transaction length
        save(data, outputFile)
            store data into outputFile
        getMinimumPeriod()
            get the minimum period
        getAveragePeriod()
            get the average period
        getMaximumPeriod()
            get the maximum period
        getStandardDeviationPeriod()
            get the standard deviation period
        getNumberOfTransactionsPerTimestamp()
            get number of transactions per time stamp. This time stamp range is 1 to max period.
    """

    def __init__(self, inputFile, sep='\t'):
        """
        :param inputFile: input file name or path
        :type inputFile: str
        :param sep:
        """
        self.inputFile = inputFile
        self.database = {}
        self.lengthList = []
        self.timeStampCount = {}
        self.periodList = []
        self.sep = sep
        self.periods = {}

    def run(self):
        self.readDatabase()

    def readDatabase(self):
        """
        read database from input file and store into database and size of each transaction.
        And store the period between transactions as list
        """
        numberOfTransaction = 0
        if isinstance(self.inputFile, pd.DataFrame):
            if self.inputFile.empty:
                print("its empty..")
            i = self.inputFile.columns.values.tolist()
            if 'TS' in i and 'Transactions' in i:
                self.database = self.inputFile.set_index('ts').T.to_dict(orient='records')[0]
            if 'TS' in i and 'Patterns' in i:
                self.database = self.inputFile.set_index('ts').T.to_dict(orient='records')[0]
            self.timeStampCount = self.inputFile.groupby('ts').count().T.to_dict(orient='records')[0]

        if isinstance(self.inputFile, str):
            if validators.url(self.inputFile):
                data = urlopen(self.inputFile)
                for line in data:
                    numberOfTransaction += 1
                    line.strip()
                    line = line.decode("utf-8")
                    temp = [i.rstrip() for i in line.split(self.sep)]
                    temp = [x for x in temp if x]
                    self.database[numberOfTransaction] = temp[1:]
                    self.timeStampCount[int(temp[0])] = self.timeStampCount.get(int(line[0]), 0)
                    self.timeStampCount[int(temp[0])] += 1
            else:
                try:
                    with open(self.inputFile, 'r', encoding='utf-8') as f:
                        for line in f:
                            numberOfTransaction += 1
                            line.strip()
                            temp = [i.rstrip() for i in line.split(self.sep)]
                            temp = [x for x in temp if x]
                            if len(temp) > 0:
                                self.database[numberOfTransaction] = temp[1:]
                                self.timeStampCount[int(temp[0])] = self.timeStampCount.get(int(line[0]), 0)
                                self.timeStampCount[int(temp[0])] += 1
                except IOError:
                    print("File Not Found")
                    quit()
        self.lengthList = [len(s) for s in self.database.values()]
        timeStampList = sorted(list(self.database.keys()))
        preTimeStamp = 0
        for ts in timeStampList:
            self.periodList.append(int(ts) - preTimeStamp)
            preTimeStamp = ts
            
        for x, y in self.database.items():
            for i in y:
                if i not in self.periods:
                    self.periods[i] = [x, x]
                else:
                    self.periods[i][0] = max(self.periods[i][0], x - self.periods[i][1])
                    self.periods[i][1] = x
        for key in self.periods:
            self.periods[key][0] = max(self.periods[key][0], abs(len(self.database) - self.periods[key][1]))
        self.periods = {k: v[0] for k, v in self.periods.items()}

    def getDatabaseSize(self):
        """
        get the size of database
        :return: data base size
        """
        return len(self.database)

    def getMinimumTransactionLength(self):
        """
        get the minimum transaction length
        :return: minimum transaction length
        """
        return min(self.lengthList)

    def getAverageTransactionLength(self):
        """
        get the average transaction length. It is sum of all transaction length divided by database length.
        :return: average transaction length
        """
        totalLength = sum(self.lengthList)
        return totalLength / len(self.database)

    def getMaximumTransactionLength(self):
        """
        get the maximum transaction length
        :return: maximum transaction length
        """
        return max(self.lengthList)

    def getStandardDeviationTransactionLength(self):
        """
        get the standard deviation transaction length
        :return: standard deviation transaction length
        """
        return statistics.pstdev(self.lengthList)

    def getVarianceTransactionLength(self):
        """
        get the variance transaction length
        :return: variance transaction length
        """
        return statistics.variance(self.lengthList)

    def convertDataIntoMatrix(self):
        singleItems = self.getSortedListOfItemFrequencies()
        itemsets = {}
        for tid in self.database:
            for item in singleItems:
                if item in itemsets:
                    if item in self.database[tid]:
                        itemsets[item].append(1)
                    else:
                        itemsets[item].append(0)
                else:
                    if item in self.database[tid]:
                        itemsets[item] = [1]
                    else:
                        itemsets[item] = [0]
        data = list(itemsets.values())
        an_array = np.array(data)
        return an_array

    def getSparsity(self):
        """
        get the sparsity of database. sparsity is percentage of 0 of database.
        :return: database sparsity
        """
        big_array = self.convertDataIntoMatrix()
        n_zeros = np.count_nonzero(big_array == 0)
        return (n_zeros / big_array.size)

    def getDensity(self):
        """
        get the sparsity of database. sparsity is percentage of 0 of database.
        :return: database sparsity
        """
        big_array = self.convertDataIntoMatrix()
        n_zeros = np.count_nonzero(big_array == 1)
        return (1.0 - n_zeros / big_array.size)

    def getTotalNumberOfItems(self):
        """
        get the number of items in database.
        :return: number of items
        """
        return len(self.getSortedListOfItemFrequencies())

    def getSortedListOfItemFrequencies(self):
        """
        get sorted list of item frequencies
        :return: item frequencies
        """
        itemFrequencies = {}
        for tid in self.database:
            for item in self.database[tid]:
                itemFrequencies[item] = itemFrequencies.get(item, 0)
                itemFrequencies[item] += 1
        return {k: v for k, v in sorted(itemFrequencies.items(), key=lambda x: x[1], reverse=True)}
    
    def getFrequenciesInRange(self):
        fre = self.getSortedListOfItemFrequencies()
        rangeFrequencies = {}
        maximum = max([i for i in fre.values()])
        values = [int(i*maximum/6) for i in range(1,6)]
        #print(maximum)
        va = len({key: val for key, val in fre.items() if val > 0 and val < values[0]})
        rangeFrequencies[va] = values[0]
        for i in range(1,len(values)):
            
            va = len({key: val for key, val in fre.items() if val < values[i] and val > values[i-1]})
            rangeFrequencies[va] = values[i]
        return rangeFrequencies
    
    def getPeriodsInRange(self):
        fre = {k: v for k, v in sorted(self.periods.items(), key=lambda x: x[1])}
        rangePeriods = {}
        maximum = max([i for i in fre.values()])
        values = [int(i*maximum/6) for i in range(1,6)]
        #print(maximum)
        va = len({key: val for key, val in fre.items() if val > 0 and val < values[0]})
        rangePeriods[va] = values[0]
        for i in range(1,len(values)):
            va = len({key: val for key, val in fre.items() if val < values[i] and val > values[i-1]})
            rangePeriods[va] = values[i]
        return rangePeriods

    def getTransanctionalLengthDistribution(self):
        """
        get transaction length
        :return: transaction length
        """
        transactionLength = {}
        for length in self.lengthList:
            transactionLength[length] = transactionLength.get(length, 0)
            transactionLength[length] += 1
        return {k: v for k, v in sorted(transactionLength.items(), key=lambda x: x[0])}

    def save(self, data, outputFile):
        """
        store data into outputFile
        :param data: input data
        :type data: dict
        :param outputFile: output file name or path to store
        :type outputFile: str
        """
        with open(outputFile, 'w') as f:
            for key, value in data.items():
                f.write(f'{key}\t{value}\n')

    def getMinimumInterArrivalPeriod(self):
        """
        get the minimum inter arrival period
        :return: minimum inter arrival period
        """
        return min(self.periodList)

    def getAverageInterArrivalPeriod(self):
        """
        get the average inter arrival period. It is sum of all period divided by number of period.
        :return: average inter arrival period
        """
        totalPeriod = sum(self.periodList)
        return totalPeriod / len(self.periodList)

    def getMaximumInterArrivalPeriod(self):
        """
        get the maximum inter arrival period
        :return: maximum inter arrival period
        """
        return max(self.periodList)
    
    def getMinimumPeriodOfItem(self):
        """
        get the minimum period of the item
        :return: minimum period
        """
        return min([i for i in self.periods.values()])
    
    def getAveragePeriodOfItem(self):
        """
        get the average period of the item
        :return: average period
        """
        return sum([i for i in self.periods.values()]) / len(self.periods)
    
    def getMaximumPeriodOfItem(self):
        """
        get the maximum period of the item
        :return: maximum period
        """
        return max([i for i in self.periods.values()])

    def getStandardDeviationPeriod(self):
        """
        get the standard deviation period
        :return: standard deviation period
        """
        return statistics.pstdev(self.periodList)

    def getNumberOfTransactionsPerTimestamp(self):
        """
        get number of transactions per time stamp
        :return: number of transactions per time stamp as dict
        """
        maxTS = max(list(self.timeStampCount.keys()))
        return {ts: self.timeStampCount.get(ts, 0) for ts in range(1, maxTS + 1)}
   
    def printStats(self):
        print(f'Database size : {self.getDatabaseSize()}')
        print(f'Number of items : {self.getTotalNumberOfItems()}')
        print(f'Minimum Transaction Size : {self.getMinimumTransactionLength()}')
        print(f'Average Transaction Size : {self.getAverageTransactionLength()}')
        print(f'Maximum Transaction Size : {self.getMaximumTransactionLength()}')
        print(f'Minimum Inter Arrival Period : {self.getMinimumInterArrivalPeriod()}')
        print(f'Average Inter Arrival Period : {self.getAverageInterArrivalPeriod()}')
        print(f'Maximum Inter Arrival Period : {self.getMaximumInterArrivalPeriod()}')
        print(f'Minimum periodicity : {self.getMinimumPeriodOfItem()}')
        print(f'Average periodicity : {self.getAveragePeriodOfItem()}')
        print(f'Maximum periodicicty : {self.getMaximumPeriodOfItem()}')
        print(f'Standard Deviation Transaction Size : {self.getStandardDeviationTransactionLength()}')
        print(f'Variance : {self.getVarianceTransactionLength()}')
        print(f'Sparsity : {self.getSparsity()}')
  
    def plotGraphs(self):
        itemFrequencies = self.getFrequenciesInRange()
        transactionLength = self.getTransanctionalLengthDistribution()
        itemPeriods = self.getPeriodsInRange()
        #numberOfTransactionPerTimeStamp = self.getNumberOfTransactionsPerTimestamp()
        plt.plotLineGraphFromDictionary(itemFrequencies, 80, 'Frequency', 'no of items', 'frequency')
        #plt.plotLineGraphFromDictionary(itemPeriods, 50, 'Periodicity', 'no of items', 'periodicity')
        plt.plotLineGraphFromDictionary(transactionLength, 100, 'transaction length', 'transaction length', 'frequency')
        #plt.plotLineGraphFromDictionary(numberOfTransactionPerTimeStamp, 100)


if __name__ == '__main__':
#     data = {'ts': [1, 1, 3, 4, 5, 6, 7],

#             'Transactions': [['a', 'd', 'e'], ['b', 'a', 'f', 'g', 'h'], ['b', 'a', 'd', 'f'], ['b', 'a', 'c'],
#                              ['a', 'd', 'g', 'k'],

#                              ['b', 'd', 'g', 'c', 'i'], ['b', 'd', 'g', 'e', 'j']]}

#     data = pd.DataFrame.from_dict(data)
#     obj = temporalDatabaseStats('tem', ',')
    import PAMI.extras.graph.plotLineGraphFromDictionary as plt

    obj = temporalDatabaseStats('Temporal_T10I4D100K.csv', '\t')
    obj.run()
    obj.printStats()
    obj.plotGraphs()
