import argparse
import re
import fileinput
import glob
import os

TEMPORARY_DIRECTORY_FILENAME = '__temporary__directory__'
OUTPUT_FILENAME_NAME = 'SUBSCRIPTIONS.csv'
RESOLVE_TIMESTAMPS_PROGRAM = ''
TEST_NAME = ''
TEMPORARY_DIRECTORY = ''
OUTPUT_FILENAME = ''


#
# results
#
# A list of string. Each string is a csv list
# Each scv list contains:
#   testname (short name)
#   dirname (same as TEST_NAME)
#   shID
#   clientID
#   subscription expression
#
results = []
  
subscriptions = {}
logResults = []
logIndex = 0


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
  parser.add_argument('-p', '--resolve_timestamps_program', dest = 'resolve_TS_Program',
          required = True, help = 'Path to the resolve_log_timestamps.py program - full path and filename of the program. e.g. ../resolve_log_timestamps.py')
  parser.add_argument('-o', '--output_directory', dest = 'output_directory',
          required = True, help = 'Location of the output directory.' +\
          ' e.g. ../output')

  options = parser.parse_args()

  testDirectory = processDirectoryArgument(options.test_directory, \
    "test_directory")
  global TEST_NAME
  TEST_NAME = os.path.basename(testDirectory)
  global RESOLVE_TIMESTAMPS_PROGRAM
  RESOLVE_TIMESTAMPS_PROGRAM = options.resolve_TS_Program

  outputDirectory = options.output_directory
  outputDirectory = outputDirectory.rstrip('/') # strip off any trailing '/'

  global TEMPORARY_DIRECTORY
  TEMPORARY_DIRECTORY = outputDirectory + '/' + TEMPORARY_DIRECTORY_FILENAME
  global OUTPUT_FILENAME
  OUTPUT_FILENAME = outputDirectory + '/' + OUTPUT_FILENAME_NAME

  #
  # Check arguments
  #
  if not os.path.exists(RESOLVE_TIMESTAMPS_PROGRAM):
    print "ERROR in generate_test_publications for test " + TEST_NAME + \
      " : resolve_timestamps_program does not exist"
    return 1


  #
  # Make the outputDirectory if necessary
  #
  if not os.path.exists(outputDirectory):
    os.makedirs(outputDirectory)


  print 'generate_test_subscriptions: Processing results from Test Directory=',\
    testDirectory,"Output going to",OUTPUT_FILENAME


  #
  # Make the empty TEMPORARY_DIRECTORY 
  #
  if not os.path.exists(TEMPORARY_DIRECTORY):
    os.makedirs(TEMPORARY_DIRECTORY)
  else:
    os.system('rm -f ' + TEMPORARY_DIRECTORY + '/*')



  #
  # Get the sub directory from the test name
  #
  tokens = TEST_NAME.split('_')
  if len(tokens) < 3:
    print "ERROR in generate_test_subscriptions for test " + TEST_NAME +\
      " : test directory " \
      + testDirectory + " does not have the expected name"
    return 1
  subdir = tokens[0]
  if not os.path.exists(testDirectory + '/' + subdir):
    print "ERROR in generate_test_subscriptions for test " + TEST_NAME +\
      " : directory " \
      + testDirectory + '/' + subdir + " does not exist"
    return 1



  #
  # Process the all the sh files
  #
  for sh in range(30):
    processSubscriptions(str(sh), testDirectory, subdir)



  writeOutput()

  
  #
  # Remove the temporary directory
  #
  os.system('rm -rf ' + TEMPORARY_DIRECTORY)


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
    print "ERROR in generate_test_subscriptions" +\
        " : you specified " + dirArgument + " for " + description + \
        " and found",len(dirs),"files when expecting 1"
    exit(1)

  directory = dirs[0]
  directory = directory.rstrip('/') # strip off any trailing '/'

  if not os.path.exists(directory):
    print "ERROR in generate_test_subscriptions"+\
      " : you specified " + dirArgument + " for " + description + \
      " and " + directory + " does not exist"
    exit(1)

  return directory



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
    header = 'Testname,Dirname,SlaveHarnessID,ClientID,SubscriptionID,CommandID,CommandType,SubscriptionExpression,Latency,SentTime,RecvTime,Status(Pass/Fail),max_or_fan_in,max_and_fan_in,circuit_depth,M,N\n';
    file.write(header)

  for data in results:
    file.write(data + '\n')
    
  file.close()



#----------------------------------------------------------
#
# resolveTimesOnFile()
#
# Resolves the timestamps in the file
#
# param file - is the original file
#
# return the name of the modified file
#
#----------------------------------------------------------
def resolveTimesOnFile(file):
  mode = "subscriptions"
  tsModifiedFile = TEMPORARY_DIRECTORY + '/' + os.path.basename(file) + \
    '-' + mode + '-' + 'tsresolved'
  os.system('python ' + RESOLVE_TIMESTAMPS_PROGRAM + ' -i ' + file + ' -o ' +  \
    tsModifiedFile)
  return tsModifiedFile



#----------------------------------------------------------
# 
# findMatchingParen()
#
# Finds the matching closing paran ')' in the string
#
# param str - the string to search
# param startIdx - the location of the beginning paran '(' to 
#  match
#
# return the index of the closing param or -1 if not found
#
#----------------------------------------------------------
def findMatchingParen(str, startIdx):
  if str[startIdx:startIdx+1] != '(':
    print "ERROR in findMatchingParen, startIdx must point to a '('"
    return -1
  idx = startIdx + 1
  counter = 1
  while idx<len(str):
    if str[idx:idx+1] == '(':
      counter += 1
    elif str[idx:idx+1] == ')':
      counter -= 1
      if counter == 0:
        break;
    idx += 1
  return idx


#----------------------------------------------------------
# 
# analyzeExpression()
#
# Analyzes a filter expression
# Note: - assumes only 1 M_OF_N in the entire expr
#
# param str - the string to search
# param maxor - the current number of max or fanins found
# param maxand - the current number of max and fanins found
# param depth - the current depth count
# param mValue - the M value from the M_OF_N term
# param nValue - the N value from the M_OF_N term
#
# return a tuple of integers: (maxor, maxand, depth)
# where maxor is the max number of OR fanins
# where maxand is the max number of AND fanins
# where depth is the circuit depth
# where mValue is the M from the M_OF_N term
# where nValue is the N from the M_OF_N term
#
#
# Notes: this is a recursive method so pass maxor, maxand, and depth as
# 0 the first time called.
#
#----------------------------------------------------------
def analyzeExpression(str,maxor, maxand, depth, mValue, nValue):
  #print "str=",str
  ors = 0
  ands = 0
  idx = 0

  while idx<len(str):

    if str[idx:idx+1] == '(':
      idx2 = findMatchingParen(str, idx)
      if idx2 == -1:
        print 'ERROR - no matching paren'
        exit(1)
      (maxor,maxand,depth,mValue,nValue) = \
        analyzeExpression(str[idx+1:idx2], maxor, maxand, depth, mValue, nValue)
      idx = idx2+1;

    elif str[idx:idx+2] == 'OR':
      ors += 1
      idx += 2

    elif str[idx:idx+3] == 'AND':
      ands += 1
      idx += 3

    elif str[idx:idx+6] == 'M_OF_N':
      idx += 6  # move to open paren
      idx2 = findMatchingParen(str, idx)
      print "INFO: found ",str[idx-6:idx2+1]
      if idx2 == -1:
        print 'ERROR'
        exit(1)

      # Get M and N values
      tokens = str[idx+1:idx2].split(',')
      if len(tokens) < 3:
        print 'ERROR M_OF_N string=',str[idx+1:idx2]," split len=", \
        len(tokens)
        exit(1) 
      mValue = tokens[0]
      nValue = tokens[1]

      # skip everything inside the parens
      idx = idx2+1

    else:
      idx += 1

  if (ors + ands) > 0:
    depth += 1

  # add in the first operand, this just counts operators
  # and fanin should count operands 
  if ors > 0:
    ors += 1
  if ands > 0:
    ands += 1

  maxor = max(maxor, ors)
  maxand = max(maxand, ands)

  return (maxor, maxand, depth, mValue, nValue)


#----------------------------------------------------------
#
# parseSlaveHarnessLog()
#
# Parses the sh-*-test-log files
#
# param file - is the string filename to parse
# param shID - is the slave harness number (it can get this from the 
#  filename but the caller knows it so it is easier to pass it thru)
#
# return a list containing tuples of:
#   (cmdType, clientID, cmdID, sentTime, recvTime, latency, status)
#     where cmdType is 'S' for subscribe and 'U' for unsubscribe
#     where clientID is the ID as a string
#     where cmdID is the command number as a string
#     where sentTime is a string time (without [])
#     where recvTime is a string time (without [])
#     where latency is a string time (without [])
#     where status is 'P' for passed and 'F' for failed
#
# Note:
# sentTime is from the first command and receivedTime is from the 
# second command:
#   [1360093869.641853571] SubscribeScript command #1 to SUT 1 STARTED
#   [1360093870.829708815] Command 1 complete. Results: DONE
#
#----------------------------------------------------------
def parseSlaveHarnessLog(file, shID):

  if file is None:
    return  # do nothing

  results = []
  
  #
  # Need to resolve timestamps in the file
  #
  tsModifiedFile = resolveTimesOnFile(file)

  #
  # Expecting lines like this in this order:
  # 
  #[1360093869.641853571] SubscribeScript command #1 to SUT 1 STARTED
  #[1360093869.641886473] Command: SUBSCRIBE, command id: 1
  #[1360093870.829708815] Command 1 complete. Results: DONE
  #[1360093870.829731941] SubscribeScript command #1 to SUT 1 FINISHED
  #

  state = 0
  cmdType = ''
  cmdScriptType = ''
  cmdNum = ''
  cmdID = ''
  clientID = ''
  sentTime = ''
  recvTime = ''
  status = ''
  # Read the input file...
  for line in fileinput.input(tsModifiedFile):
    #print line # debug
    #print "state=",state

    tokens = line.split() # split on whitespace
    if len(tokens) < 6:
      continue

    if state == 0:
      # look for SubscribeScript command line
      if (tokens[1] == "SubscribeScript" or \
          tokens[1] == "UnsubscribeScript") and \
         tokens[2] == "command" and \
         tokens[7] == "STARTED":
        if tokens[1] == "SubscribeScript": 
         cmdType = "SUBSCRIBE,"
         cmdScriptType = "SubscribeScript"
        else:
         cmdType = "UNSUBSCRIBE,"
         cmdScriptType = "UnsubscribeScript"
        sentTime = tokens[0][1:-1]
        cmdNum = tokens[3]
        clientID = tokens[6]
        state = 1
    elif state == 1:
      # look for Command: {UN}SUBSCRIBE line
      if tokens[1] == "Command:" and tokens[2] == cmdType:
        cmdID = tokens[5]
        state = 2
    elif state == 2:
      # look for Command complete line
      if tokens[1] == "Command" and tokens[3] == "complete.":
        recvTime = tokens[0][1:-1]
        if cmdID != tokens[2]:
          print "ERROR in generate_test_subscriptions for test " + TEST_NAME + \
            " : parseSlaveHarnessLog(): " + \
            "Error on Command complete line. Expecting command ID=" + cmdID + \
            " but instead found " + tokens[2] + " while reading " + \
            file + " for shID=",shID,"clientID=",clientID
          exit(1)
        if tokens[5] == "DONE":
          status = 'P'
        else:
          status = 'F'

          # print warning
          print "WARNING: Subscription failed for shID=", \
            shID,"clientID=",clientID,"cmdID=",cmdID, \
            "sentTime=",sentTime

        state = 3
    else:
      # look for {Un}SubscribeScript command FINISHED line
      if tokens[1] == cmdScriptType and \
         tokens[2] == "command" and \
         tokens[7] == "FINISHED":
        if cmdNum != tokens[3]:
          print "ERROR in generate_test_subscriptions for test " + TEST_NAME + \
            " : parseSlaveHarnessLog(): " + \
            "Error on " + cmdScriptType + " command FINISHED line.", \
            "Expecting cmdNum=" + cmdNum + \
            " but instead found " + tokens[3] + " while reading " + \
            file + " for shID=",shID,"clientID=",clientID
          exit(1)
        if clientID != tokens[6]:
          print "ERROR in generate_test_subscriptions for test " + TEST_NAME + \
            " : parseSlaveHarnessLog(): " + \
            "Error on " + cmdScriptType + " command FINISHED line.", \
            "Expecting clientID=" + clientID + \
            " but instead found " + tokens[6] + " while reading " + \
            file + " for shID=",shID,"clientID=",clientID
          exit(1)

        # save results
        latency = str(float(recvTime)-float(sentTime))
        results.append((cmdType[0:1], clientID, cmdID, sentTime, recvTime, latency, status))

        # null out result variables
        cmdType = ''
        cmdScriptType = ''
        cmdNum = ''
        cmdID = ''
        clientID = ''
        sentTime = ''
        recvTime = ''
        status = ''
        state = 0

  return results


def processSubscriptions(shID, testDirectory, subdir):

  # Get all subscriptions and unsubscriptions in the sh log file
  shLogFile = testDirectory + '/' + "sh-" + shID + "-test-log"
  if not os.path.exists(shLogFile):
    return
  global logResults
  global logIndex
  logResults = parseSlaveHarnessLog(shLogFile, shID)
  logIndex = 0
  if len(logResults) <= logIndex:
    print "WARNING no subscription entries for file",shLogFile
    return

  subscriptions.clear() 

  # Read sh-SHID-subscriptions file
  filename = testDirectory + '/' + subdir + '/' + \
      'sh-'+ shID + '-subscriptions';
  if os.path.exists(filename) :
    processSubFile(shID, filename)

  # Read sh-SH#-background file
  filename = testDirectory + '/' + subdir + '/' + \
      'sh-'+ shID + '-background-subscriptions';
  if os.path.exists(filename) :
    processSubFile(shID, filename)

  # Read any update subscription files  
  filename = testDirectory + '/' + subdir + '/' + \
    'set-*-sh-'+ shID + '-update-subscriptions';
  files = glob.glob(filename)
  sorted_files = sorted(files, key=lambda x: int(x.split('-')[1]))
  #print "XXXX sorted_files=",sorted_files
  for filename in sorted_files:
    processSubFile(shID, filename)


def processSubFile(shID, filename):
  global logIndex
  global logResults

  #print "XXX processSubFile ",filename

  if logIndex >= len(logResults):
    print "ERROR ran out of log entries"
    exit(1)

  subscribe = 0
  unsubscribe = 0
  commandType = 'S'

  # Read the input file...
  for line in fileinput.input(filename):

    if line == "SubscribeScript\n":
      subscribe = 1
      commandType = 'S'
      continue
    elif line == "UnsubscribeScript\n":
      unsubscribe = 1
      commandType = 'U'
      continue

    tokens = line.split() # split on whitespace
    if subscribe and len(tokens) < 3:
      continue
    elif unsubscribe and len(tokens) < 2:
      continue

    clientID = tokens[0]
    subscrID = tokens[1]
 
    if subscribe:
      filter = ' '.join(tokens[2:])
      subscriptions[(clientID, subscrID)] = filter
    else:
      filter = subscriptions[(clientID, subscrID)]

    # process filter
    (maxOrFanIn, maxAndFanIn, circuitDepth, mValue, nValue) =  \
       analyzeExpression(filter, 0, 0, 0, 0, 0)
    mStringVal = ''          
    if int(mValue) != 0:
      mStringVal = mValue
    nStringVal = ''          
    if int(nValue) != 0:
      nStringVal = nValue
  
    # get corresponding line in sh log 
    (cmdType, logClientID, cmdID, sentTime, recvTime, latency, status) = \
       logResults[logIndex]
    logIndex += 1

    # should match
    if clientID != logClientID or cmdType != commandType:
      print "ERROR 2"
      exit(1)

    data = \
      TEST_NAME.split('_')[0] + ',' + \
      TEST_NAME + ',' + \
      shID + ',' + \
      clientID + ',' + \
      subscrID + ',' + \
      cmdID + ',' + \
      cmdType + ',' + \
      filter + ',' + \
      latency + ',' + \
      sentTime + ',' + \
      recvTime + ',' + \
      status + ',' + \
      str(maxOrFanIn) + ',' + \
      str(maxAndFanIn) + ',' + \
      str(circuitDepth) + ',' + \
      mStringVal + ',' + \
      nStringVal
    results.append(data);




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

