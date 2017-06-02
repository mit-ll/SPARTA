# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Classes to write query aggregator results 
#                      to the result database
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.query_generation.query_schema as qs
import abc
import spar_python.query_generation.query_ids as qids
import itertools

SELECT_STAR_CUTOFF = 10000
EVERY_XTH = 5
_query_number = itertools.count(0)
    
def _select_star(matching_records):
    '''
    Returns a boolean if the query in question should also
    be a select * query
    '''
    if matching_records < SELECT_STAR_CUTOFF:
        number = _query_number.next()
        return (number % EVERY_XTH) == 0
    return False

class QueryResultBase(object):
    """ Base class to write query results to the results database """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, query, result, db_object, top):
        '''
        query is a dictionary
        result was produced by an aggregator and is a dictionary
        db_object is the open results database to write the query results to
        top is False for nested queries and True for top level queries
        '''
        self._query = query
        self._result = result
        self._db_object = db_object
        self._top = top

    @abc.abstractmethod
    def process_query(self):
        '''
        Prepares the new rows for the result database tables for the 
        query result.
        Returns a tuple of: 
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry)
        each of which is a row dictionary. Some of them may be empty.
        '''
        pass

    def write_query(self):
        ''' Write the query result to all the result database tables '''

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            self.process_query()

        if atomic_entry:
            self._db_object.add_row(rdb.DBA_TABLENAME, atomic_entry)
        if full_entry:
            self._db_object.add_row(rdb.DBF_TABLENAME, full_entry)
        if full_to_atomic_entry:
            self._db_object.add_row(rdb.F2A_TABLENAME, full_to_atomic_entry)
        if full_to_full_entry:
            self._db_object.add_row(rdb.F2F_TABLENAME, full_to_full_entry)
        

    #
    # static methods to write to the full, full_to_atomic, and 
    # full_to_full tables used for compound queries like P1, P8, P9
    #

    @staticmethod
    def _pre_write_to_full_table(query, result):
        qid = query[qs.QRY_QID]
        if qids.full_qid_seen(qid):
            return {}
        matching_record_ids = result[rdb.DBF_MATCHINGRECORDIDS]
        matching_records =  len(matching_record_ids)
        full_entry = \
            { rdb.DBF_FQID : qid,
              rdb.DBF_CAT : query[qs.QRY_CAT],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in query[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in query[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in query[qs.QRY_PERF],
              rdb.DBF_SUBCAT : query[qs.QRY_SUBCAT].replace('-',''),
              rdb.DBF_NUMRECORDS : query[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : query[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : query[qs.QRY_WHERECLAUSE],
              rdb.DBF_NUMMATCHINGRECORDS : matching_records, 
              rdb.DBF_MATCHINGRECORDIDS : matching_record_ids, 
              rdb.DBF_SELECTSTAR : _select_star(matching_records)}

        if query[qs.QRY_CAT] == "P1":
            full_entry[rdb.DBF_P1NUMTERMSPERCLAUSE] = \
                query[qs.QRY_NUMTERMSPERCLAUSE]
            full_entry[rdb.DBF_P1NUMCLAUSES] = query[qs.QRY_NUMCLAUSES]
            # add num records matching first term for all P1s
            if query[qs.QRY_ENUM]== qs.CAT.P1_EQ_AND:
                full_entry[rdb.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM] = \
                    result[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM]
            if query[qs.QRY_ENUM]==qs.CAT.P1_EQ_OR:
                full_entry[rdb.DBF_P1ORSUMRECORDSMATCHINGEACHTERM] =\
                    result[qs.QRY_SUMRECORDSMATCHINGEACHTERM]
            if query[qs.QRY_ENUM] == qs.CAT.P1_EQ_NOT:
                full_entry[rdb.DBF_P1NEGATEDTERM] = query[qs.QRY_NEGATEDTERMS]
        if query[qs.QRY_CAT] in ["P8","P9"]:
            full_entry[rdb.DBF_P8M] = query[qs.QRY_M]
            full_entry[rdb.DBF_P8N] = query[qs.QRY_N]
        if query[qs.QRY_CAT] == "P9":
            full_entry[rdb.DBF_P9MATCHINGRECORDCOUNTS] = \
                result[qs.QRY_MATCHINGRECORDCOUNTS]
        return full_entry

    @staticmethod
    def write_to_full_table(query, result, db_object):
        entry = \
            QueryResultBase._pre_write_to_full_table(query, result)
        if entry:
            db_object.add_row(rdb.DBF_TABLENAME, entry)



    @staticmethod
    def _pre_write_to_full_to_atomic_table(query, result):
        entries = []
        fqid = query[qs.QRY_QID]
        for sub_result in result[qs.QRY_SUBRESULTS]: 
            aqid = sub_result[qs.QRY_QID]
            if not qids.full_to_atomic_qids_seen(fqid, aqid):
                entries.append( { rdb.F2A_FQID : fqid, rdb.F2A_AQID : aqid } )
        return entries

    @staticmethod
    def write_to_full_to_atomic_table(query, result, db_object):
        entries = \
            QueryResultBase._pre_write_to_full_to_atomic_table(query, result)
        for entry in entries:
            db_object.add_row(rdb.F2A_TABLENAME, entry)




    @staticmethod
    def _pre_write_to_full_to_full_table(query, result):
        entries = []
        fqid = query[qs.QRY_QID]
        for sub_result in result[qs.QRY_SUBRESULTS]: 
            sqid = sub_result[qs.QRY_QID]
            if not qids.full_to_full_qids_seen(fqid, sqid):
                entries.append( { rdb.F2F_BASEQID : fqid, 
                                  rdb.F2F_COMPOSITEQID : sqid } )
        return entries

    @staticmethod
    def write_to_full_to_full_table(query, result, db_object):
        entries = \
            QueryResultBase._pre_write_to_full_to_full_table(query, result)
        for entry in entries:
            db_object.add_row(rdb.F2F_TABLENAME, entry)


    

class AtomicQueryResultBase(QueryResultBase):
    ''' 
    Atomic query base class to write query results to the results database
    '''
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def process_query(self):
        '''
        Prepares the new rows for the result database tables for the 
        query result.
        Returns a tuple of: 
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry)
        each of which is a row dictionary. Some of them may be empty.
        '''
        if self._result is None:
            matching_record_ids = set()
            matching_records = 0
        else:
            matching_record_ids = self._result[rdb.DBF_MATCHINGRECORDIDS]
            matching_records =  len(matching_record_ids)
        qid = self._query[qs.QRY_QID]
            
        # For the Atomic Query Table
        if qids.atomic_qid_seen(qid):
            atomic_entry = {}
        else:
            atomic_entry = { rdb.DBA_AQID : qid,
                         rdb.DBA_CAT : self._query[qs.QRY_CAT],
                         rdb.DBA_SUBCAT : self._query[qs.QRY_SUBCAT].replace('-',''),
                         rdb.DBA_NUMRECORDS : self._query[qs.QRY_DBNUMRECORDS],
                         rdb.DBA_RECORDSIZE : self._query[qs.QRY_DBRECORDSIZE],
                         rdb.DBA_WHERECLAUSE : self._query[qs.QRY_WHERECLAUSE],
                         rdb.DBA_FIELD : self._query[qs.QRY_FIELD],
                         rdb.DBA_FIELDTYPE : self._query[qs.QRY_FIELDTYPE],
                         rdb.DBA_NUMMATCHINGRECORDS : matching_records }

        full_entry = {}
        full_to_atomic_entry = {}
        if self._top and not qids.full_qid_seen(qid):
            # When an atomic query is at the top level (not nested) must
            # add it to the full and full_to_atomic tables also

            # For the Full Query Table
            full_entry = \
                { rdb.DBF_FQID : qid,
                  rdb.DBF_CAT : self._query[qs.QRY_CAT],
                  rdb.DBF_SUBCAT : self._query[qs.QRY_SUBCAT].replace('-',''),
                  rdb.DBF_IBM1SUPPORTED : "IBM1" in self._query[qs.QRY_PERF],
                  rdb.DBF_IBM2SUPPORTED : "IBM2" in self._query[qs.QRY_PERF],
                  rdb.DBF_COLUMBIASUPPORTED : "COL" in self._query[qs.QRY_PERF],
                  rdb.DBF_NUMRECORDS : self._query[qs.QRY_DBNUMRECORDS],
                  rdb.DBF_RECORDSIZE : self._query[qs.QRY_DBRECORDSIZE],
                  rdb.DBF_WHERECLAUSE : self._query[qs.QRY_WHERECLAUSE],
                  rdb.DBF_NUMMATCHINGRECORDS : matching_records, 
                  rdb.DBF_MATCHINGRECORDIDS : matching_record_ids,
                  rdb.DBF_SELECTSTAR : _select_star(matching_records) }
      
            # For the Full to Atomic Junction Table
            full_to_atomic_entry = { rdb.F2A_AQID : qid, rdb.F2A_FQID : qid }

        return (atomic_entry, full_entry, full_to_atomic_entry, {})


class EqualityQueryResult(AtomicQueryResultBase):
    ''' 
    class to write equality query results to the results database
    '''
    def process_query(self):
        return super(EqualityQueryResult, self).process_query()


class P2QueryResult(AtomicQueryResultBase):
    ''' 
    class to write P2 query results to the results database
    '''
    def process_query(self):
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) =\
            super(P2QueryResult, self).process_query()

        # Add the range specific data
        if atomic_entry:
            atomic_entry[rdb.DBA_RANGE] = self._query[qs.QRY_RANGE]

        return (atomic_entry, full_entry, 
                full_to_atomic_entry, full_to_full_entry)


class P3P4P6P7QueryResult(AtomicQueryResultBase):
    ''' 
    class to write search queries (p3, P4, P6, P7) results to the
    results database
    '''
    def process_query(self):
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) =\
            super(P3P4P6P7QueryResult, self).process_query()

        # Add the search specific data
        if atomic_entry:
            atomic_entry[rdb.DBA_KEYWORDLEN] = self._query[qs.QRY_KEYWORDLEN]

        return (atomic_entry, full_entry, 
                full_to_atomic_entry, full_to_full_entry)
        
class P9AlarmQueryResult(AtomicQueryResultBase):
    ''' 
    class to write search queries (p9) results to the
    results database
    '''
    def process_query(self):
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) =\
            super(P9AlarmQueryResult, self).process_query()

        # Add the search specific data
        if full_entry:
            full_entry[rdb.DBF_P9MATCHINGRECORDCOUNTS] = \
                self._result[qs.QRY_MATCHINGRECORDCOUNTS]

        return (atomic_entry, full_entry, 
                full_to_atomic_entry, full_to_full_entry)


