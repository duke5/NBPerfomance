# Create by Tony Che at 2020-02

# MongoDBStatisticsLoggingAnalysis.py
# Feature description

import os
import re
import queue
import threading
import datetime
from time import localtime, strftime, time, sleep
from colorama import Fore, Back, Style
from multiprocessing import Pool as ThreadPool
import concurrent.futures

'''
Count  means how many times to access the collection by the operation,  If you found the count is very huge, that means we should pay attention, and find the way to optimize it.
Total(ms)  means the total time in micro second the operation  expended
Average(ms)  is means  the  Total(ms) /Count,    If it too large like more then 100 ms,  we need pay attention  to check db performance  and if index created well
Longest(ms)  is means the longest one of the operation,  If it is too large like more then 1000 ms,  we need check if some query do not use index
'''
logPath = r'\\192.168.31.221\C$\Program Files\NetBrain\Worker Server\log\2020-04-06'
maxCount = 10000
maxAverage = 100
maxLongest = 1000
maxThread = 30
inputQueue = queue.Queue()
outputQueue = queue.Queue()

def main():
    start = time()
    for folder in os.listdir(logPath):
        # print(folder)
        if not 'WorkerShell_' in folder:
            continue
        logFilename = os.path.join(logPath, folder, 'log', 'NBLog.log')
        # FindMongoDBStatistics1(logFilename, maxCount=10000, maxAverage=100, maxLongest=1000)
        inputQueue.put(logFilename)
        # print(logFilename, '\n')

    diff = time() - start
    print('find ', str(inputQueue.qsize()), 'log files in ', str(datetime.timedelta(seconds=int(diff))), '.\n')

    start = time()
    for i in range(maxThread):
        t = threading.Thread(target=WorkerThread, args=(maxCount, maxAverage, maxLongest))
        t.daemon = True
        t.start()

    o = threading.Thread(target=OutputThread)
    o.daemon = True
    o.start()

    inputQueue.join()  # Block until all tasks are done
    outputQueue.join()

    diff = time() - start
    print('spend', str(datetime.timedelta(seconds=int(diff))), 'to analysis the log files.\n\n')

def PrintMessage(message, level=''):
    currenttime = localtime()  # gmtime(): UTC time
    if (re.search('Error', level, re.IGNORECASE)):
        print(Fore.LIGHTYELLOW_EX + Back.RED, strftime("%Y-%m-%d %H:%M:%S", currenttime), message + Style.RESET_ALL)
    elif (re.search('Warning', level, re.IGNORECASE)):
        print(Fore.LIGHTWHITE_EX + Back.YELLOW, strftime("%Y-%m-%d %H:%M:%S", currenttime), message + Style.RESET_ALL)
    else:
        print(strftime("%Y-%m-%d %H:%M:%S", currenttime), message)

def ReadLogFile(filePath):
    text = ''
    with open(filePath, 'r') as fp:
        text = fp.read()

    return text

def GetStatValue(text):
    findit = re.match('\w*\s*(\d+)\s*(\d+[\.|\d]*)\s*(\d+[\.|\d]*)\s*(\d+[\.|\d]*)', text)
    if(findit):
        count = int(findit[1])
        total = float(findit[2])
        average = float(findit[3])
        longest = float(findit[4])
        return (count, average, total, longest)
    return (0, 0, 0, 0)

def FindMongoDBStatistics1(logFilename, maxCount=10000, maxAverage=100, maxLongest=1000):
    count = longest = 0
    c = a = t = l = 0
    logContents = [logFilename, ]
    logFileContents = ReadLogFile(logFilename)
    findit = re.findall(".*run task begin.*", logFileContents, re.IGNORECASE and re.MULTILINE) #(.*run task begin.*|.*MongoDB Statistics.*)
    for line in findit:
        logContents.append(line)

    findit = re.match("[\w\W]*MongoDB Statistics\s+-*\s+([\w\W]*)\n\n\n", logFileContents, re.IGNORECASE) #MongoDB Statistics --*\s*(\w*\W*)\d+\s\d+\s\d+:\d+:\d+\s
    if (findit):
        for line in list(filter(None, findit[1].split('\n'))):
            if not re.search('\d', line):
                continue
            c, a, t, l = GetStatValue(line)
            count += c
            if(l > longest):
                longest = l
        logContents.append(''.join(['count=', str(count), ', average=', str(a), ', total=', str(t), ', longest=', str(longest)]))
    if (c <= 0 or t <= 0):
        return
    for line in logContents:
        if(longest < maxLongest and a < maxAverage and count < maxCount):
            PrintMessage(line)
        else:
            PrintMessage(line, 'Error')

def FindMongoDBStatistics2(logFilename, maxCount=10000, maxAverage=100, maxLongest=1000):
    count = longest = averagest = 0
    c = a = t = l = 0
    logContents = [logFilename, ]
    logFileContents = ReadLogFile(logFilename)
    findit = re.findall(".*run task begin.*", logFileContents, flags=re.IGNORECASE | re.MULTILINE) #(.*run task begin.*|.*MongoDB Statistics.*)
    for line in findit:
        logContents.append(line)

    findit = re.match("[\w\W]*MongoDB Statistics\s+-*\s+([\w\W]*)\n\n\n", logFileContents, re.IGNORECASE) #MongoDB Statistics --*\s*(\w*\W*)\d+\s\d+\s\d+:\d+:\d+\s
    if (findit):
        for line in list(filter(None, findit[1].split('\n'))):
            if not re.search('\d', line):
                continue
            c, a, t, l = GetStatValue(line)
            count += c
            if(l > longest):
                longest = l
            if (a > averagest):
                averagest = a
        logContents.append(''.join(['countAll=', str(count), ', maxAverage=', str(averagest), ', maxLongest=', str(longest)])) # , ', total=', str(t)
    if (c <= 0 or t <= 0):
        return
    #for line in logContents:
    if(longest < maxLongest and averagest < maxAverage and count < maxCount):
        #PrintMessage(line)
        outputQueue.put({'logLevel':'Info', 'message': logContents})
    else:
        #PrintMessage(line, 'Error')
        outputQueue.put({'logLevel':'Error', 'message': logContents})

def WorkerThread(maxCount=10000, maxAverage=100, maxLongest=1000):
    while True:
        logFilename = inputQueue.get()
        FindMongoDBStatistics2(logFilename, maxCount, maxAverage, maxLongest)
        inputQueue.task_done()

def OutputThread():
    while True:
        #print(''.join(['input queue: ', str(inputQueue.qsize()), '; output queue: ', str(outputQueue.qsize())]))
        logContents = outputQueue.get()
        for line in logContents['message']:
            PrintMessage(line, logContents['logLevel'])
        outputQueue.task_done()


if __name__ == '__main__':
    main()
