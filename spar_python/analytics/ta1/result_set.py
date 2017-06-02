# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Represents a set of test results. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  02 Dec 2012   omd            Original Version
# *****************************************************************

import logging
import re
import functools
import shelve
import tempfile
import os
import sys

logger = logging.getLogger(__name__)

class ResultSet(object):
    """This needs to be cleaned up. For now this assumes the answer to a query
    is always the same. We'll need a different sub-class to handle the
    modification scripts."""
    QUERY_LINE_RE = re.compile(r'\[([\d.]+)\] Command: \[\[([^\]]+)\]\], '
            'command id: (\d+)')
    QUERY_RESULT_LINE_RE = re.compile(
            r'\[([\d.]+)\] Command (\d+) complete. Results:')

    def __init__(self):
        # Use a shelf or we run out of memory *fast* when processing big files.
        # Python kinda sucks that way :(
        self.__shelf_path = tempfile.mktemp()
        self.__results = shelve.open(self.__shelf_path)
        logger.debug('Using %s as a data cache', self.__shelf_path)
    
    def __del__(self):
        logger.debug('Deleting data cache %s', self.__shelf_path)
        os.remove(self.__shelf_path)

    def get_query_results(self):
        return self.__results

    def add(self, file_obj):
        query_id_map = {}
        # A function that will handle the next line read from the file. The
        # function must accept a single string and return a new function that
        # will be used to handle the next line or None if the normal "root mode"
        # handling should be done instead.
        handler = None

        for line in file_obj:
            line = line.strip()

            qlm = self.QUERY_LINE_RE.match(line)
            if qlm:
                assert not qlm.group(3) in query_id_map
                query_id_map[qlm.group(3)] = qlm.group(2)
                continue

            rlm = self.QUERY_RESULT_LINE_RE.match(line)
            if rlm:
                assert rlm.group(2) in query_id_map
                query = query_id_map[rlm.group(2)]
                del query_id_map[rlm.group(2)]
                q_results_dict = self.__parse_results_lines(file_obj)
                # Be careful not to assign to the dict until all the results are
                # ready. Otherwise they won't get stored in the shelf!
                if query in self.__results:
                    # We must be re-running a query. Make sure the results
                    # didn't change.
                    logger.debug('Repeat of query %s', query)
                    if q_results_dict != self.__results[query]:
                        logger.critical(
                                'Results for query "%s" changed!', query)
                        # TODO(odain): This should be more elegant!!
                        sys.exit(1)
                self.__results[query] = q_results_dict
                continue
            else:
                logger.debug('Skipping line: "%s"', line)

    def __parse_results_lines(self, file_obj):
        """Give file_obj, a file object whose internal pointer is such that
        file_obj.next() is expected to return query results, populate and return
        a dictionary with key == row_id and value == either the hash of the row,
        if the query was "select *", or None, if the query was "select id"."""
        result = {}
        for line in file_obj:
            line = line.strip()
            if len(line) == 0:
                return result

            parts = line.split(' ')
            assert len(parts) in (1, 2), 'Unexpected results line: %s' % line
            assert len(parts[0]) > 0

            if len(parts) == 1:
                parts.append(None)

            result[parts[0]] = parts[1]

        logger.warning('EOF while parsing result set.')
        return result

