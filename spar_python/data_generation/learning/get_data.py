# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Get PUMS data files
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 Sept. 2012 JCH            Original file, though derived from
#                                Oliver's bash script
#  20 Sept.      JCH            Now gets zip codes and names
# *****************************************************************

"""
Gets the data files which are used to train the data-generator.  Use
command-line options to set the destination directory for the files,
and to control the verbosity of the output. Files are stored under
a temporary *.download name until download is complete, at which time
they are re-named to their correct name. 

Notes: Expects to get proxy information from the $http_proxy envrionment 
variable. Also, this reads URLs from the dict in url_dict.py. If that dict
specifies that the URL for a file is None, then the file will actually be
copied from the same directory as this file.
"""

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import urllib
import datetime
from optparse import OptionParser
import logging
import hashlib
import shutil

from url_dict import url_dict



percent_downloaded = 0
time_download_started = None
curr_state = None

def _urllib_reporter(count, blocksize, file_size):    
    """
    Used by urllib.retrieve to keep the user informed of the status of
    the download.
    """
    global time_download_started
    global percent_downloaded
    global curr_state

    if time_download_started == None:
        time_download_started = datetime.datetime.now()
        
    bytes_so_far = count * blocksize
    percent_downloaded_now = (float(bytes_so_far) / file_size) * 100 

    if percent_downloaded_now - percent_downloaded > 1:
        now = datetime.datetime.now()
        elapsed = now - time_download_started
        elapsed_sec = (elapsed.seconds + float(elapsed.microseconds) / 1000000)
        rate = bytes_so_far / elapsed_sec
        remaining_sec = (file_size - bytes_so_far) / rate
        logging.info("%s: %d percent complete. Estimated time remaining:"\
                     "%d seconds." % \
                     (curr_state, percent_downloaded_now, remaining_sec))
        percent_downloaded = percent_downloaded_now


def get_file(file_spec, dest_dir, data_file):
    """
    Get a file from the web. If url is None, then copy from the same 
    directory as this file. Returns a list of errors encountered
    """
    
    (filename, url, _) = file_spec
    temp_filename = filename + '.download'

    filepath = os.path.join(dest_dir, filename)
    temp_filepath = os.path.join(dest_dir, temp_filename)

    errors_encountered = []
    if url is None:
        this_file_dir = os.path.dirname(os.path.realpath(__file__))
        logging.info("No URL provided for %s (%s) copying from %s."
                     % (filename, data_file, this_file_dir))

        source_file = os.path.join(this_file_dir, filename)
        shutil.copy(source_file, dest_dir)
    else:


        logging.info("Getting data for %s at %s. "\
                     "This may take a long time." %\
                     (data_file, url))
        try:
            # Get the file, store under temporary name
            urllib.urlretrieve(url, temp_filepath, _urllib_reporter)                
        except urllib.ContentTooShortError:
            logging.warning("File %s (%s) shorter than expected, "
                            "probably due to download interruption."
                            % (filename, data_file))
            errors_encountered.append( (data_file, filename, url) )
        except IOError as err:
            logging.warning("Cannot download file %s (%s). "
                            "Diagnostic information: \n%s"
                            % (filename, data_file, str(err)))
            errors_encountered.append( (data_file, filename, url) )
        else:
            # Download successful (we assume-- see documentation
            # for urllib.urlretrieve). Rename the file.
            os.rename(temp_filepath, filepath)

    return errors_encountered
    
    

def main():
    global percent_downloaded
    global time_download_started
    global curr_state
    
    parser = OptionParser()

    parser.add_option('-f', "--force", dest="force_download",
                      action="store_true", default=False,
                      help="Force downloading of PUMS data files."\
                      "Will erase existing files")
    parser.add_option("-d", "--dest", dest="destination",
                      default="./data",
                      help="Destination directory for PUMS files")
    parser.add_option("-v", '--verbose', dest="verbose",
                      action="store_true", default=False,
                      help="Verbose output")
    parser.add_option('--test-data-only', dest="test_only",
                      action="store_true", default=False,
                      help="Get only one PUMS file (useful for testing)")

    (options, args) = parser.parse_args()


    if options.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    logging.debug("Starting!")
    # Establish that destination direcory exists. If not, make it.
    top_dir = options.destination
    if not os.path.exists(top_dir):
        logging.warning("Cannot find directory %s. Making." %\
                        top_dir)
        os.mkdir(top_dir)
        
    errors_encountered = []

    # Go through URL dictionary, getting each entry
    for data_type in url_dict:
        file_dict = url_dict[data_type]
        # Make the subdirectory
        dest_dir = os.path.join(top_dir, data_type)
        if not os.path.exists(dest_dir):
            logging.warning("Cannot find directory %s. Making." %\
                            dest_dir)
            os.mkdir(dest_dir)

        num_fetched = 0
        for data_file in file_dict:

            if options.test_only \
               and (data_type == 'PUMS') \
               and (num_fetched > 0):

                # We're fetching PUMS files, we already got
                # at least one, and the user wants test
                # data only. Skip.

                logging.info("Skipping %s (test-data-only run).", data_file)

                break
            file_spec = file_dict[data_file]
            (filename, url ,hashval) = file_spec
            filepath = os.path.join(dest_dir, filename)

            # Do we already have the file?
            have_file_already = os.path.isfile(filepath)

            file_errors = []

            if options.force_download or (not have_file_already):
                
                file_errors = get_file(file_spec, dest_dir, data_file)
                errors_encountered += file_errors
            
            else:                
                if have_file_already:
                    logging.info("File %s (%s) already exists." %\
                                 (filename, data_file))

                    
            # Get the hash of the file and compare to that in url_dict                    
            if len(file_errors) == 0:
                with open(filepath, 'r') as f:
                    logging.info("Checking hash on %s", data_file)
                    download_hashval = hashlib.sha1(f.read()).hexdigest() 
                    if download_hashval != hashval:
                        logging.warning("Bad hash for file %s. %s did not match"
                                        " expected value of %s. Deleting file.",
                                        filename, download_hashval, hashval)
                        os.remove(filepath)
                        errors_encountered.append( (filename, 
                                                    data_file, 
                                                    url) )
                    else:
                        logging.info("Hash OK")
                        
            # Reset for the next download
            percent_downloaded = 0
            time_download_started = None
            num_fetched += 1
        
    if errors_encountered:
        logging.warning("Errors encountered while downloading the following "
                        "files. Try running this script again.")

        for (data_file, filename, url) in errors_encountered:
            logging.warning("%s (%s, %s)" % (data_file, filename, url))



if __name__ == "__main__":
    main()
