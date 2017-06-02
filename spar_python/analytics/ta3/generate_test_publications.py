import argparse
import re
import fileinput
import glob
import os

TEMPORARY_DIRECTORY_FILENAME = '__temporary__directory__'
OUTPUT_FILENAME_NAME = 'PUBLICATIONS.csv'
RESOLVE_TIMESTAMPS_PROGRAM = ''
TEST_NAME = ''
TEMPORARY_DIRECTORY = ''
OUTPUT_FILENAME = ''
LATENCY_FILENAME = 'latency-warnings.log'
LATENCY_FILE = None
LATENCY_THRESHOLD = ''


#
# results
#
# A dictionary indexed by pubID to another dictionary of values.
# The dictionary of values contains:
#   "hash" -> hash string
#   "time" -> time string (including square brackets)
#   "payloadLen" -> the payload length string
#   "expected" -> list of shID,clientID tuples where 
#       shID and clientID are strings
#   "actual" -> list of shID,clientID tuples where 
#       shID and clientID are strings
#   "times" -> list of tuples of (startTime recvTime)
#   "status" -> 'P' if successful, 'F' if failed 
#
results = {}
  
# Dictionaries of publications 
#   Indexed by hash string to another dictionary of values.
#   The nested dictionary of values contains:
#     "pubID" -> string value
#     "payloadLen" -> string value
#     "time" -> the string time which includes the square brackets 
#        e.g. "[1360089945.0922334455]"
#     "status" -> 'P' if passed; 'F' if failed
publications = {}
baselinePublications = {}



#----------------------------------------------------------
# 
# main()
#
# Parses the output and produces a csv file
#
# param none
#
# return status 
#
#----------------------------------------------------------
def main():
  parser = argparse.ArgumentParser('Process results appending the ' + \
    'results for this specific test to ' + OUTPUT_FILENAME_NAME)
  parser.add_argument('-t', '--test_directory', dest = 'test_directory',
          required = True, help = 'Location of the test directory.' +\
          ' e.g. ../TC003_130205_115023')
  parser.add_argument('-b', '--baseline_directory', dest = 'baseline_directory',
          required = True, help = 'Location of the baseline test directory.' +\
          ' e.g. ../TC003_130205_115023')
  parser.add_argument('-p', '--resolve_timestamps_program', dest = 'resolve_TS_Program',
          required = True, help = 'Path to the resolve_log_timestamps.py program - full path and filename of the program. e.g. ../resolve_log_timestamps.py')
  parser.add_argument('-o', '--output_directory', dest = 'output_directory',
          required = True, help = 'Location of the output directory.' +\
          ' e.g. ../output')
  parser.add_argument('-c', '--check_latency', dest = 'latency_threshold_value',
          required = False, help = 'Report any latencies above this value' +\
          ' and append them to the ' + LATENCY_FILENAME + \
          ' file in the output_directory.'
          ' e.g. 10.0 ')
  options = parser.parse_args()



  testDirectory = processDirectoryArgument(options.test_directory, \
    "test_directory")
  baselineDirectory = processDirectoryArgument(options.baseline_directory, \
    "baseline_directory")
  global TEST_NAME
  TEST_NAME = os.path.basename(testDirectory)

  outputDirectory = options.output_directory
  outputDirectory = outputDirectory.rstrip('/') # strip off any trailing '/'
  #
  # Make the outputDirectory if necessary
  #
  if not os.path.exists(outputDirectory):
    os.makedirs(outputDirectory)


  global RESOLVE_TIMESTAMPS_PROGRAM
  RESOLVE_TIMESTAMPS_PROGRAM = options.resolve_TS_Program

  global TEMPORARY_DIRECTORY
  TEMPORARY_DIRECTORY = outputDirectory + '/' + TEMPORARY_DIRECTORY_FILENAME
  global OUTPUT_FILENAME
  OUTPUT_FILENAME = outputDirectory + '/' + OUTPUT_FILENAME_NAME


  global LATENCY_THRESHOLD
  global LATENCY_FILE
  if options.latency_threshold_value:
    LATENCY_THRESHOLD = options.latency_threshold_value
    #
    # Open the LATENCY_FILE
    #
    LATENCY_FILE = open(outputDirectory + "/" + LATENCY_FILENAME, 'a')
    print "INFO: Using check_latency threshold value of ", \
      LATENCY_THRESHOLD," to file ",outputDirectory + "/" + LATENCY_FILENAME

  

  #
  # Check arguments
  #
  if not os.path.exists(RESOLVE_TIMESTAMPS_PROGRAM):
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : resolve_timestamps_program does not exist"
    return 1



  print 'generate_test_publications: Processing results from Test Directory=',\
    testDirectory,'and baseline directory=', baselineDirectory,"Output going to ",OUTPUT_FILENAME



  #
  # Make the empty TEMPORARY_DIRECTORY 
  #
  if not os.path.exists(TEMPORARY_DIRECTORY):
    os.makedirs(TEMPORARY_DIRECTORY)
  else:
    os.system('rm -f ' + TEMPORARY_DIRECTORY + '/*')



  #
  # Process Test's Publication script'
  #
  pubFilename = testDirectory + '/' + 'mh-test-logs' + '/' + 'PublishScript*'
  pubScriptFiles = glob.glob(pubFilename)
  if len(pubScriptFiles) < 1:
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
       " : cannot find PublishScript=", pubFilename
    exit(1)

  for pubScriptFile in pubScriptFiles:
    print "INFO: Reading file", pubScriptFile
    parsePublishScript(pubScriptFile, "test")


  #
  # Process the Test's sh-x-test-log files
  #
  shLogFilenames = testDirectory + '/' + 'sh-*-test-log';
  for filename in glob.glob(shLogFilenames):
    parseSlaveHarnessLog(filename, publications, "test")


  #----------------------------------------

  #
  # Process Test's Publication script'
  #
  pubFilename = baselineDirectory + '/' + 'mh-test-logs' + '/' + 'PublishScript*'
  pubScriptFiles = glob.glob(pubFilename)
  if len(pubScriptFiles) < 1:
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : cannot find PublishScript=",pubFilename
    exit(1)

  for pubScriptFile in pubScriptFiles:
    print "INFO: Reading file", pubScriptFile
    parsePublishScript(pubScriptFile, "baseline")



  #
  # Process the Test's sh-x-test-log files
  #
  shLogFilenames = baselineDirectory + '/' + 'sh-*-test-log';
  for filename in glob.glob(shLogFilenames):
    parseSlaveHarnessLog(filename, baselinePublications, "baseline")


  #
  # Add missing publications
  #
  processUnmatchedPublications(publications)

  #dumpResults()  # Debug

  writeOutput()
  

  #
  # Remove the temporary directory
  #
  os.system('rm -rf ' + TEMPORARY_DIRECTORY)


  if LATENCY_FILE:
    LATENCY_FILE.close()


  return 0



#----------------------------------------------------------
# 
# processDirectoryArgument(dirArgument)
#
# Expand for wildcards, expect only one path which 
# must exist. Otherwise it will give a fatal error
#
# param dirArgument the directory to process (a string)
# param description a string description of what this directory
#  is, used in error messages
#
# return the processed directory
#
#----------------------------------------------------------
def processDirectoryArgument(dirArgument, description):

  # resolve wildcards
  dirs = glob.glob(dirArgument)

  # expect only one directory
  if len(dirs) != 1:
    print "ERROR in generate_test_publications" +\
        " : you specified " + dirArgument + " for " + description + \
        " and found",len(dirs),"files when expecting 1"
    exit(1)

  directory = dirs[0]
  directory = directory.rstrip('/') # strip off any trailing '/'

  if not os.path.exists(directory):
    print "ERROR in generate_test_publications"+\
      " : you specified " + dirArgument + " for " + description + \
      " and " + directory + " does not exist"
    exit(1)

  return directory


#----------------------------------------------------------
# 
# computeLatency()
#
# Computes the latency from two times
#
# param time1 - the begin time - in string format 
#        e.g. "[1360089945.0922334455]"
# param time2 - the end time - in string format 
#        e.g. "[1360089945.0922334455]"
#
# return the latency - as a string without the square brackets
#
#----------------------------------------------------------
def computeLatency(time1, time2):
  num1 = float(time1[1:-1])
  num2 = float(time2[1:-1])
  return str(num2 - num1)




#----------------------------------------------------------
# 
# writeOutput()
#
# Uses results to output a csv file
#
# return nothing
#
#----------------------------------------------------------
def writeOutput():

  if not os.path.exists(OUTPUT_FILENAME):
    needHeader = 1
  else:
    needHeader = 0

  file = open(OUTPUT_FILENAME, 'a') 
  
  if needHeader:
    header = 'Testname,Dirname,PubID,PayloadLen,Expected,Actual,Latencies,SentTimes,RecvTimes,Status(Pass/Fail)\n';
    file.write(header)

  for pubID, data in results.iteritems():
    payloadLen = data["payloadLen"]
    expected = data["expected"]
    actual = data["actual"]
    latencies = data["times"]
    status = data["status"]

    # testname
    shortTestName = TEST_NAME.split('_')[0]
    line = shortTestName + ','

    # dirname
    line += TEST_NAME + ','

    # pubID
    line += pubID + ','

    # payload length
    line += payloadLen + ','

    # expected
    line += '['
    firstTime = 1
    for listData in expected:
      if firstTime: 
        firstTime = 0
      else: 
        line += ";"
      line += '<' + listData[0] + '#' + listData[1] + '>'
    line += '],'
  
    # actual
    line += '['
    firstTime = 1
    for listData in actual:
      if firstTime: 
        firstTime = 0
      else: 
        line += ";"
      line += '<' + listData[0] + '#' + listData[1] + '>'
    line += '],'
  
    # latencies
    line += '['
    firstTime = 1
    for idx, listData in enumerate(latencies):
      if firstTime: 
        firstTime = 0
      else: 
        line += ";"
      latency = computeLatency(listData[0], listData[1])
      line += latency
      if LATENCY_FILE and float(latency) > float(LATENCY_THRESHOLD):
        # latency, time1, time2, dirname, pubID, shID, clientID, 
        latencyWarning(latency, listData[0][1:-1], listData[1][1:-1], \
          TEST_NAME, pubID, actual[idx][0], actual[idx][1])
    line += '],'

    # sentTime
    line += '['
    firstTime = 1
    for listData in latencies:
      if firstTime: 
        firstTime = 0
      else: 
        line += ";"
      time1 = listData[0][1:-1]  # strip off enclosing square brackets
      line += time1
    line += '],'

    # recvTime
    line += '['
    firstTime = 1
    for listData in latencies:
      if firstTime: 
        firstTime = 0
      else: 
        line += ";"
      time2 = listData[1][1:-1]  # strip off enclosing square brackets
      line += time2
    line += '],'

    # status
    line += status



    line += '\n'

    file.write(line)
    
  file.close()



#----------------------------------------------------------
#
# latencyWarning()
#
# Prints a warning about latency
#
# param latency - the latency as a string
# param time1 - the begin time as a string 
# param time2 - the end time as a string 
# param dirname - the full test directory name
# param pubID - the publication ID
# param shID - the slave harnessID
# param clientID - the client ID
#
# return nothing
#
#----------------------------------------------------------
def latencyWarning(latency, time1, time2, dirname, \
  pubID, shID, clientID):
  
  if not LATENCY_FILE:
    return

  warningMsg = "WARNING Latency exceeded threshold for test=" + dirname + \
    " : Latency=" + latency + " time1=" + time1 + " time2=" + time2 + \
    " pubID=" + pubID + " shID=" + shID + " clientID=" + clientID + "\n"

  LATENCY_FILE.write(warningMsg)

#----------------------------------------------------------
#
# resolveTimesOnFile()
#
# Resolves the timestamps in the file
#
# param file - is the original file
# param mode - added to the modified filename - used to distinguish 
#  between the test and baseline files. Typically either
#  'test' or 'baseline'
#
# return the name of the modified file
#
#----------------------------------------------------------
def resolveTimesOnFile(file, mode):
  tsModifiedFile = TEMPORARY_DIRECTORY + '/' + os.path.basename(file) + \
    '-' + mode + '-' + 'tsresolved'
  os.system('python ' + RESOLVE_TIMESTAMPS_PROGRAM + ' -i ' + file + ' -o ' +  \
    tsModifiedFile)
  return tsModifiedFile



#----------------------------------------------------------
#
# parseSlaveHarnessLog()
#
# Parses the sh-*-test-log files
#
# param file - is the string filename to parse
# param publications - is the publications dictionary
# param mode - "test" or "baseline"
#
# return nothing, modifies global results dictionary
#
#----------------------------------------------------------
def parseSlaveHarnessLog(file, publications, mode):

  if file is None:
    return  # do nothing


  if mode != 'test' and mode != 'baseline':
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : parseSlaveHarnessLog(): unexpected value for argument mode"
    exit(1)

  # Get shID from file
  base = os.path.basename(file)
  tokens = base.split("-")
  if len(tokens) != 4:
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : parseSlaveHarnessLog(): filename for sh-*-test-log not right, found",\
      file
    exit(1)
  if tokens[0] != "sh" or tokens[2] != "test" or tokens[3] != "log":
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : parseSlaveHarnessLog(): filename for sh-*-test-log not right, found",\
      file
    exit(1)
  shID = tokens[1]

  #
  # Need to resolve timestamps in the file
  #
  tsModifiedFile = resolveTimesOnFile(file, mode)


  # Read the input file...
  for line in fileinput.input(tsModifiedFile):
    #print line # debug

    tokens = line.split() # split on whitespace
    if len(tokens) < 9:
      continue

    # look for "Publication received" lines only
    if tokens[1] != "Publication" or tokens[2] != "received":
      continue
  
    time2 = tokens[0]
    clientID = tokens[5][:-1]  # strip off trailing period
    hash = tokens[8]
    
    # Find hash in publications
    if not hash in publications:
      # A subscriber saw a hash that cannot be found in the
      # PublishScript. While this is indeed not usually supposed to
      # happen, we sometimes abort tests halfway and end up in
      # inconsistent states like this. Gracefully just not process
      # these hashes any further in these situations, that is best.
      print "WARNING in generate_test_publications for test " + TEST_NAME + \
        " : Subscriber shID=",shID,"found hash=", \
        hash,"at time=",time2,"for clientID=",clientID,"but this hash", \
        "is not found in the PublishScripts"
      continue

    # get publication data for this hash
    (pubID, time1, payloadLen, status) = getPubData(hash, publications)
    

    if pubID in results:
      resultsData = results[pubID]
      if mode == 'test':
        actual = resultsData["actual"]
        actual.append((shID,clientID))
        latencies = resultsData["times"]
        latencies.append((time1, time2))
        # set status from the test
        resultsData["status"] = status
      else: 
        # baseline
        expected = resultsData["expected"]
        expected.append((shID,clientID))
    else:
      # Add a new entry for this pubID
      data = {}
      data["hash"] = hash
      data["payloadLen"] = payloadLen

      # use status from the test only
      if (mode == 'baseline'):
        data["status"] = ''
      else:
        data["status"] = status

      expected = list()
      if mode == 'baseline':
        expected.append((shID, clientID))
      data["expected"] = expected

      actual = list()
      if mode == 'test':
        actual.append((shID, clientID))
      data["actual"] = actual

      latencies = list()
      if mode == 'test':
        latencies.append((time1, time2))
      data["times"] = latencies

      results[pubID] = data
      

#----------------------------------------------------------
#
# processUnmatchedPublications()
#
# Goes through publications and adds to results for each 
# entry that was not marked as "found"
#
# param publications - is the publications dictionary
#
# return nothing, modifies global results dictionary
#
#----------------------------------------------------------

def processUnmatchedPublications(publications):

  # for each entry in publications
  for hash, pubData in publications.iteritems():

    # skip all marked found
    if "found" in pubData:
      continue;

    pubID = pubData["pubID"]
    time1 = pubData["time"]
    payloadLen = pubData["payloadLen"]
    status = pubData["status"]

    if not pubID in results:
      # Add a new entry for this pubID
      data = {}
      data["hash"] = hash
      data["payloadLen"] = payloadLen
      data["status"] = status

      expected = list()
      data["expected"] = expected

      actual = list()
      data["actual"] = actual

      latencies = list()
      data["times"] = latencies

      results[pubID] = data
      

#----------------------------------------------------------
#
# dumpResults()
#
# Dumps the results - used for debugging
#
#----------------------------------------------------------
def dumpResults():
  for pubID, data in results.iteritems():
    hash = data["hash"]
    payloadLen = data["payloadLen"]
    expected = data["expected"]
    actual = data["actual"]
    times = data["times"]
    status = data["status"]

    print "  "
    print "pubID=",pubID
    print "  hash=",hash
    print "  payloadLen=", payloadLen
    print "  expected="
    for listData in expected:
      print "    shID=",listData[0], "clientID=",listData[1]
    print "  actual="
    for listData in actual:
      print "    shID=",listData[0], "clientID=",listData[1]
    print "  latencies="
    for listData in times:
      latency = computeLatency(listData[1], listData[0])
      print "    time1=",listData[0], "time2=",listData[1], "latency=",latency
    print "  status=",status

#----------------------------------------------------------
#
# parsePublishScriptCommand()
#
# Parses the "Command:" lines from PublishScript files
#
# param line - is the string line to parse
#
# return a tuple of (pubID, hash, payloadLen) where all are strings
#
#----------------------------------------------------------
def parsePublishScriptCommand(line):
  hash = ""
  payloadLen = ""
  tokens = line.split() # split on whitespace
  if len(tokens) < 14:
    print "ERROR in generate_test_publications for test ",TEST_NAME,\
      " : parsePublishScriptCommand(): Command line does not have " + \
      "enough fields. Expected 4 found",len(tokens)
    exit(1)

  pubID = tokens[5][0:-1]  # strip off trailing comma

  for index, token in enumerate(tokens):
    if token == "hash:":
      hash = tokens[index+1][:-1] # strip off training comma
    elif token == "length:":
      payloadLen = tokens[index+1]
  
  return (pubID,hash,payloadLen)


#----------------------------------------------------------
#
# parsePublishScript()
#
# Parses the PublishScript file
#
# param file - is the string filename
# param mode - is either "test" or "baseline"
#
# return nothing - modifies global dictionaries
#  publications and baselinePublications
#
# Expect lines like this:
# [349456.269157159] PublishScript publish command #4 STARTED
# [349456.269300299] Command: PUBLISH, command id: 18, metadata: CARLIE,SMITHEN,896583646,1857-11-19,158 Star St,Tullos,Tennessee,83500,Male,Two_or_More_Races,Widowed,Nursery_or_Preschool,No,208762,Under_17,BURMESE,66,47, payload hash:66a9054907857d106da8f09b2815f43e, payload length: 9906
# [349456.299005339] Command 18 complete. Results: DONE
# [349456.269157159] PublishScript publish command #4 FINISHED
#
#----------------------------------------------------------
def parsePublishScript(file=None, mode='test'):
  #print "in parsePublishScript file=", file

  if file is None:
    return  # do nothing

  if mode != "test" and mode != "baseline":
    print "ERROR in generate_test_publications for test " + \
       TEST_NAME + " : parsePublishScript(): invalid value for mode of", \
       mode
    exit(1)


  #
  # Need to resolve timestamps in the file
  #
  tsModifiedFile = resolveTimesOnFile(file, mode)

  
  # Read the input file...
  pubID = "" 
  cmdNum = ""
  time = ""
  hash = ""
  payloadLen = ""
  status = ""
  state = 0
  for line in fileinput.input(tsModifiedFile):
    #print line # debug
    #print "state=",state

    tokens = line.split() # split on whitespace
    if len(tokens) < 2:
      continue


    if state == 0:
      # look for PublishScript command STARTED
      if tokens[1] == "PublishScript" and tokens[-1] == "STARTED" :
        if len(tokens) < 5:
          print "ERROR in generate_test_publications for test " + \
            TEST_NAME + " : parsePublishScript(): line does" + \
            " not have enough fields","Line=",line
          exit(1)
        time = tokens[0]
        cmdNum = tokens[4]
        state = 1
    elif state == 1:
      # Look for Command: PUBLISH line
      if tokens[1] == "Command:" and tokens[2] == "PUBLISH,":
        (pubID, hash, payloadLen) = parsePublishScriptCommand(line)
        state = 2
    elif state == 2:
      # look for Command Complete line
      if tokens[1] == "Command" and tokens[3] == "complete.":
        if len(tokens) < 5:
          print "ERROR in generate_test_publications for test " + \
            TEST_NAME + " : parsePublishScript(): line does" + \
            " not have enough fields","Line=",line
          exit(1)
        if tokens[2] != pubID:
          print "ERROR in generate_test_publications for test " + \
            TEST_NAME + " : parsePublishScript(): pubID on FINSHED is ",\
            tokens[4], "but pubID on START is ", pubID
          exit(1)
        if tokens[5] == "DONE":
          status = 'P'
        else:
          status = 'F'
        state = 3
    elif state == 3:
      # look for PublishScript command FINISHED
      if tokens[1] == "PublishScript" and tokens[-1] == "FINISHED" :
        if len(tokens) < 5:
          print "ERROR in generate_test_publications for test " + \
            TEST_NAME + " : parsePublishScript(): FINISHED line does" +\
            " not have enough fields"
          exit(1)
        if tokens[4] != cmdNum:
          print "ERROR in generate_test_publications for test " + \
            TEST_NAME + " : parsePublishScript(): cmdNum on FINSHED is ",\
            tokens[4], "but cmdNum on START is ", cmdNum
          exit(1)
        data = {}
        data["pubID"] = pubID
        data["time"] = time
        data["payloadLen"] = payloadLen
        data["status"] = status
        if mode == "test":
          publications[hash] = data
        else:
          baselinePublications[hash] = data
        state = 0
        #print "FINAL ",hash, data  # debug
        #print " "  # debug

        # Reset values
        pubID = ""
        time = ""
        hash = ""
        payloadLen = ""
        status = ""
         

#----------------------------------------------------------
#
# getPubData()
#
# Finds the data for the given hash
#
# param hash - is the string hash to find the data for
# param publications - is the publications dictionary to search
#
# return a list of tuples for (pubID, time, payloadLen, status)
#
#----------------------------------------------------------
def getPubData(hash, publications):
  data = publications[hash]
  data["found"] = 1
  return (data["pubID"], data["time"], data["payloadLen"], data["status"])


#----------------------------------------------------------
#
# getPubID()
#
# Finds the pubID for the given hash
#
# param hash - is the string hash to find the pubID for
# param publications - is the publications dictionary to search
#
# return the pubID string
#
#----------------------------------------------------------
def getPubID(hash, publications):
  return publications[hash]["pubID"]



#----------------------------------------------------------
# Main program
#
# param 
#
# return 
#
#----------------------------------------------------------
if __name__ == '__main__':
  main()

