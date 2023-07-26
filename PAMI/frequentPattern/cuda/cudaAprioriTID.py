# Apriori is one of the fundamental algorithm to discover frequent patterns in a transactional database. This program employs apriori property (or downward closure property) to  reduce the search space effectively. This algorithm employs breadth-first search technique to find the complete set of frequent patterns in a transactional database.
#
#
# **Importing this algorithm into a python program**
# ----------------------------------------------------
#
#     import PAMI.frequentPattern.cuda.cuAprioriBit as alg
#
#     obj = alg.cuAprioriBit(iFile, minSup)
#
#     obj.startMine()
#
#     frequentPatterns = obj.getPatterns()
#
#     print("Total number of Frequent Patterns:", len(frequentPatterns))
#
#     obj.save(oFile)
#
#     Df = obj.getPatternInDataFrame()
#
#     memUSS = obj.getMemoryUSS()
#
#     print("Total Memory in USS:", memUSS)
#
#     memRSS = obj.getMemoryRSS()
#
#     print("Total Memory in RSS", memRSS)
#
#     run = obj.getRuntime()
#
#     print("Total ExecutionTime in seconds:", run)


__copyright__ = """
 Copyright (C)  2021 Rage Uday Kiran

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""





import os
import csv
import time
import numpy as np
import pycuda.gpuarray as gpuarray
import pycuda.autoinit
import psutil
import pycuda.driver as cuda
from pycuda.compiler import SourceModule
import pycuda

deviceIntersection = SourceModule("""
    __global__ void intersection(int *compareThis, int *compareThat, int *resultStart,
                                 int *values, int *result, int resultX, int resultY){
        const int tidX = blockIdx.x * blockDim.x + threadIdx.x;
        const int tidY = blockIdx.y * blockDim.y + threadIdx.y;
        int resultIndex = resultStart[tidX] + tidY;

        // ignore if tidX or tidY is out of bounds or if the value comparing with is 0
        if (tidX > resultX-1 || tidY > resultY-1 || values[compareThis[tidX] + tidY] == 0) return;

        for (int i = 0; i < resultY; i++){
            if ( values[compareThat[tidX] + i] == 0) return;
            if ( values[compareThis[tidX] + tidY] == values[compareThat[tidX] + i]){
                result[resultIndex] = values[compareThis[tidX] + tidY];
                return;
            }
        }

        //result[resultIndex] = values[compareThis[tidX] + tidY];

    }

"""
                                  )


class cudaAprioriTID:
    """
    :Description: Apriori is one of the fundamental algorithm to discover frequent patterns in a transactional database. This program employs apriori property (or downward closure property) to  reduce the search space effectively. This algorithm employs breadth-first search technique to find the complete set of frequent patterns in a transactional database.

    :Reference:  Agrawal, R., Imieli ́nski, T., Swami, A.: Mining association rules between sets of items in large databases.
            In: SIGMOD. pp. 207–216 (1993), https://doi.org/10.1145/170035.170072

    :param  iFile: str :
                   Name of the Input file to mine complete set of frequent patterns
    :param  oFile: str :
                   Name of the output file to store complete set of frequent patterns
    :param  minSup: int :
                   The user can specify minSup either in count or proportion of database size. If the program detects the data type of minSup is integer, then it treats minSup is expressed in count. Otherwise, it will be treated as float.
    :param  sep: str :
                   This variable is used to distinguish items from one another in a transaction. The default seperator is tab space. However, the users can override their default separator.



    :Attributes:

        startTime : float
          To record the start time of the mining process

        endTime : float
          To record the completion time of the mining process

        finalPatterns : dict
          Storing the complete set of patterns in a dictionary variable

        memoryUSS : float
          To store the total amount of USS memory consumed by the program

        memoryRSS : float
          To store the total amount of RSS memory consumed by the program

        Database : list
          To store the transactions of a database in list



    **Methods to execute code on terminal**
    ----------------------------------------------------

            Format:
                      >>> python3 cudaAprioriTID.py <inputFile> <outputFile> <minSup>

            Example:
                      >>>  python3 cudaAprioriTID.py sampleDB.txt patterns.txt 10.0

            .. note:: minSup will be considered in percentage of database transactions


    **Importing this algorithm into a python program**
    ----------------------------------------------------

    .. code-block:: python

             import PAMI.frequentPattern.cuda.cuAprioriBit as alg

             obj = alg.cuAprioriBit(iFile, minSup)

             obj.startMine()

             frequentPatterns = obj.getPatterns()

             print("Total number of Frequent Patterns:", len(frequentPatterns))

             obj.savePatterns(oFile)

             Df = obj.getPatternInDataFrame()

             memUSS = obj.getMemoryUSS()

             print("Total Memory in USS:", memUSS)

             memRSS = obj.getMemoryRSS()

             print("Total Memory in RSS", memRSS)

             run = obj.getRuntime()

             print("Total ExecutionTime in seconds:", run)


    **Credits:**
    -------------

             The complete program was written by Tarun Sreepada under the supervision of Professor Rage Uday Kiran.

    """

    __time = 0
    __memRSS = 0
    __memUSS = 0
    __GPU_MEM = 0
    filePath = ""
    sep = ""
    minSup = 0
    Patterns = {}

    def __init__(self, filePath, sep, minSup):
        self.filePath = filePath
        self.sep = sep
        self.minSup = minSup
        self.__time = 0
        self.__memRSS = 0
        self.__memUSS = 0

    def _readFile(self, fileName, separator):
        """
        Reads a file and stores the data in a dictionary

        Args:
            fileName: string
            separator: string

        Returns:
            dictionary: dictionary
        """
        file = open(fileName, 'r')
        dictionary = {}
        lineNumber = 1
        for line in file:
            line = line.strip()
            line = line.split(separator)
            for i in range(len(line)):
                if line[i] in dictionary:
                    dictionary[line[i]].append(lineNumber)
                else:
                    dictionary[line[i]] = [lineNumber]
            lineNumber += 1

        # sort dictionary by size of values
        dictionary = dict(
            sorted(dictionary.items(), key=lambda x: len(x[1]), reverse=True))
        return dictionary, lineNumber

    def get_time(self):
        """Calculating the total amount of time taken by the mining process

                :return: returning total amount of runtime taken by the mining process

                :rtype: float
                """

        return self.__time

    def get_memRSS(self):
        """Total amount of RSS memory consumed by the mining process will be retrieved from this function

                :return: returning RSS memory consumed by the mining process

                :rtype: float
                """
        return self.__memRSS

    def get_memUSS(self):
        """Total amount of USS memory consumed by the mining process will be retrieved from this function

                :return: returning USS memory consumed by the mining process

                :rtype: float
                """
        return self.__memUSS

    def get_GPU_MEM(self):
        return self.__GPU_MEM

    def get_Patterns(self):
        """ Function to send the set of frequent patterns after completion of the mining process

                :return: returning frequent patterns

                :rtype: dict
                """
        return self.Patterns

    def get_numberOfPatterns(self):
        return len(self.Patterns)

    def startMine(self):
        """
                   Frequent pattern mining process will start from here
               """
        dev_Intersection = deviceIntersection.get_function("intersection")
        startTime = time.time()
        final = {}

        data, lineNo = self._readFile(self.filePath, self.sep)
        if self.minSup < 1:
            self.minSup = int(lineNo * self.minSup)

        data = dict(filter(lambda x: len(x[1]) >= self.minSup, data.items()))
        for key, value in data.items():
            final[key] = len(value)

        while len(data) > 1:
            # sort data by size of values
            data = dict(
                sorted(data.items(), key=lambda x: len(x[1]), reverse=True))

            values = list(data.values())
            maxLength = values[0]
            for i in range(1, len(values)):
                while len(values[i]) != len(maxLength):
                    values[i].append(0)

            values = np.array(values)
            resultSize = 0

            compareThis = []
            compareThat = []
            resultStart = []
            counter = 0

            for i in range(len(values)):
                for j in range(i+1, len(values)):
                    resultSize += 1
                    compareThis.append(i*len(maxLength))
                    compareThat.append(j*len(maxLength))
                    resultStart.append(counter)
                    counter += len(maxLength)
            result = np.zeros((resultSize, len(maxLength)), dtype=np.int32)

            # convert all to uint32
            compareThis = np.array(compareThis, dtype=np.uint32)
            compareThat = np.array(compareThat, dtype=np.uint32)
            resultStart = np.array(resultStart, dtype=np.uint32)
            values = np.array(values, dtype=np.uint32)
            result = np.array(result, dtype=np.uint32)

            # allocate memory on GPU
            compareThis_gpu = cuda.mem_alloc(compareThis.nbytes)
            compareThat_gpu = cuda.mem_alloc(compareThat.nbytes)
            resultStart_gpu = cuda.mem_alloc(resultStart.nbytes)
            values_gpu = cuda.mem_alloc(values.nbytes)
            result_gpu = cuda.mem_alloc(result.nbytes)

            # add all nbytes to GPU_MEM
            sumBytes = compareThis.nbytes + compareThat.nbytes + resultStart.nbytes + values.nbytes + result.nbytes
            if sumBytes > self.__GPU_MEM:
                self.__GPU_MEM = sumBytes

            # copy data to GPU
            cuda.memcpy_htod(compareThis_gpu, compareThis)
            cuda.memcpy_htod(compareThat_gpu, compareThat)
            cuda.memcpy_htod(resultStart_gpu, resultStart)
            cuda.memcpy_htod(values_gpu, values)
            cuda.memcpy_htod(result_gpu, result)

            blockDim = (32, 32, 1)
            gridDim = (resultSize//32 + 1, len(maxLength)//32 + 1, 1)

            dev_Intersection(compareThis_gpu, compareThat_gpu,
                             resultStart_gpu, values_gpu, result_gpu,
                             np.uint32(resultSize), np.uint32(len(maxLength)),
                             block=blockDim, grid=gridDim)

            # copy data back to CPU
            cuda.Context.synchronize()
            cuda.memcpy_dtoh(result, result_gpu)

            # free GPU memory
            cuda.DeviceAllocation.free(compareThis_gpu)
            cuda.DeviceAllocation.free(compareThat_gpu)
            cuda.DeviceAllocation.free(resultStart_gpu)
            cuda.DeviceAllocation.free(values_gpu)
            cuda.DeviceAllocation.free(result_gpu)

            keys = list(data.keys())
            # convert all to string and add " "
            for i in range(len(keys)):
                keys[i] = str(keys[i]) + " "
            data = {}
            index = 0
            for i in range(len(keys)):
                for j in range(i+1, len(keys)):
                    newResult = list(sorted(set(result[index])))
                    newResult = list(filter(lambda x: x > 0, newResult))
                    if len(newResult) >= self.minSup:
                        keyI = keys[i].split()
                        keyJ = keys[j].split()
                        combinedKey = " ".join(list(str(x) for x in (
                            sorted(int(x) for x in (set(keyI) | set(keyJ))))))
                        if combinedKey not in final:
                            data[combinedKey] = newResult
                            final[combinedKey] = len(newResult)
                    index += 1


        self.__time = time.time() - startTime
        self.__memRSS = psutil.Process(os.getpid()).memory_info().rss
        self.__memUSS = psutil.Process(os.getpid()).memory_full_info().uss
        self.Patterns = final


if __name__ == "__main__":
    filePath = "datasets\\transactional_T10I4D100K.csv"
    sep = "\t"
    support = 500
    cudaAprioriTID = cudaAprioriTID(filePath, sep, support)
    cudaAprioriTID.startMine()
    print("Time: ", cudaAprioriTID.get_time())
    print("Memory RSS: ", cudaAprioriTID.get_memRSS())
    print("Memory USS: ", cudaAprioriTID.get_memUSS())
    print("GPU MEM: ", cudaAprioriTID.get_GPU_MEM())
    print("Patterns: ", cudaAprioriTID.get_numberOfPatterns())
