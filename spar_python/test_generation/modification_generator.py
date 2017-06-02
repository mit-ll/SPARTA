# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Generate modification tests
# *****************************************************************

import sys
import os
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.common.spar_random as sprandom
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.test_generation.test_utils as tu
import spar_python.test_generation.read_lineraw as rl
import spar_python.data_generation.spar_variables as sv

class ModificationGenerator(object):
    '''Creates modification tests for a database'''

    def __init__(self, max_row_id, resultdb, line_raw_file, schema_file, 
                 base_output_dir, \
                 doing_select_star):
        self.resultdb = resultdb  
        self.performer = performer
        self.dbsize_str = dbsize_str

        # base_output_dir ends in performer/dbsize/ 
        self.base_output_dir = base_output_dir
        # make a "mods" directory under base_output_dir
        self.mods_dir = os.path.join(self.base_output_dir, "mods")
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir)

        (self.db_record_size, self.db_num_records) = \
            tu.get_db_size(resultdb)
        
        self.mid_id_generator = tu.IDGenerator()
        self.qid_id_generator = tu.IDGenerator()
        self.test_id_generator = tu.IDGenerator()
        self.lr_test_id_generator = tu.IDGenerator()
        self.row_id_generator = tu.IDGenerator(max_row_id)
        if doing_select_star:
            self.select_str = "SELECT * "
        else:
            self.select_str = "SELECT id "

        self.generate_xtra_rows(line_raw_file, schema_file)


    def generate_xtra_rows(self, lineraw_file, schema_file):
        '''Generate test rows to add to the DB'''
        self.field_order = rl.get_field_order(schema_file)
        lineraw_handle = open(lineraw_file, 'r')
        self.xtra_rows = []
        while True:
            rowid = self.row_id_generator.get_id()
            row = rl.get_row(lineraw_handle, self.field_order, rowid)
            if (row == None):
                break
            self.xtra_rows.append(row)
        lineraw_handle.close()

    def fill_mod_query_table(self, mid, qid, where_clause):
        '''Write to the resultdb MODQUERIES_TABLENAME'''
        data = { rdb.MODQUERIES_QID : qid,
                rdb.MODQUERIES_WHERECLAUSE : where_clause,
                rdb.MODQUERIES_NUMRECORDS : self.db_num_records,
                rdb.MODQUERIES_RECORDSIZE : self.db_record_size, 
                rdb.MODQUERIES_MID : mid }

        self.resultdb.add_row(rdb.MODQUERIES_TABLENAME, data)
    

    def fill_join_table(self, mid, qids):
        '''Fill the M2MQ_TABLENAME resultdb table
        
        qids is a list of qids
        add one entry for each qid
        '''

        assert mid
            

        # Note: it does not fill in the matching ids or matching
        # hashes here they will be calculated once this test is run
        # and filled in later
        for qid in qids:
            assert qid
            data = { rdb.M2MQ_QID : qid,
                     rdb.M2MQ_MID : mid,
                     rdb.M2MQ_PREIDS : [],
                     rdb.M2MQ_PREHASHES : [],
                     rdb.M2MQ_POSTIDS : [],
                     rdb.M2MQ_POSTHASHES : [] }
            self.resultdb.add_row(rdb.M2MQ_TABLENAME, data)

    def fill_mods_table(self, mid, query_type, record_id):
        '''Write to mods table
        type is either "insert", "delete", or "update"
        '''
        data = { rdb.MODS_MID : mid,
                 rdb.MODS_CATEGORY : query_type,
                 rdb.MODS_NUMRECORDS : self.db_num_records,
                 rdb.MODS_RECORDSIZE : self.db_record_size,
                 rdb.MODS_RECORDID : record_id }
        self.resultdb.add_row(rdb.MODS_TABLENAME, data)

    def create_tests(self, number_of_tests):
        '''Top level routine to create modification tests'''
        num_rows_to_do = 1
        for _ in range(number_of_tests):
            self.tests_by_type('insert_delete', num_rows_to_do)
            self.tests_by_type('update')

    def tests_by_type(self, test_type, num_rows_to_do=1):
        '''Generate tests of type insert_delete or update'''
        # get a unique number for this test
        test_id = test_type + "_" + self.test_id_generator.get_id()

        # create a directory for this test
        out_dir = os.path.join(self.base_output_dir, test_id)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # open the testscript file
        testfilename = os.path.join(self.base_output_dir, test_script_name)
        testfile = open(testfilename, 'w')

        for row_count in range(num_rows_to_do):
            new_row= sprandom.choice(self.xtra_rows)

            self.insert_test(new_row, testfile)

            if (test_type == 'update'):
                self.update_test(new_row, testfile)

            self.delete_test(new_row, testfile)
        
        testfile.write('RootModeMasterScript SHUTDOWN\n')
        testfile.close()

    def insert_test(self, new_row, testfile):
        '''Create an insert test'''
        mid = self.mid_id_generator.get_id()
        (qfilename, qid) = self.create_insert_query(mid, new_row, out_dir)
        self.write_query_test(qfilename, testfile)
        self.create_insert_mod(mid, new_row, out_dir, testfile)
        self.fill_mods_table(mid, "insert", new_row['id'])
        self.write_query_test(qfilename, testfile)
        self.fill_join_table(mid, [qid])

    def delete_test(self, new_row, testfile):
        '''Create a delete test'''
        mid = self.mid_id_generator.get_id()
        (qfilename, qid) = self.create_delete_query(mid, new_row, out_dir)
        self.write_query_test(qfilename, testfile)
        self.create_delete_mod(mid, new_row, out_dir, testfile)
        self.fill_mods_table(mid, "delete", new_row['id'])
        self.write_query_test(qfilename, testfile)
        self.fill_join_table(mid, [qid])

    def update_test(self, new_row, testfile):
        '''Create an update test which includes reversing the update'''
        ### TODO It would be nice to have a bunch of fields modified, but lets
        ### start with just one field.

        mod_field = sprandom.choice(tu.HI_ENTROPY_FIELDS)
        new_value = sprandom.choice(tu.HI_ENTROPY_FIELD_VALUES[mod_field])
        orig_value = new_row[mod_field]

        mid = self.mid_id_generator.get_id()
        (qfiles, qids) = \
            self.create_update_queries(mid, mod_field, new_value, orig_value, \
                                       new_row, out_dir)
        
        self.create_update_test_script(mid, qfiles, new_row, mod_field, \
                                           new_value, out_dir, testfile)

        self.fill_join_table(mid, qids)

        #
        # Put it back now
        #
        mid = self.mid_id_generator.get_id()
        (qfiles, qids) = \
            self.create_update_queries(mid, mod_field, orig_value, new_value, \
                                       new_row, out_dir)
        
        self.create_update_test_script(mid, qfiles, new_row, mod_field, \
                                           orig_value, out_dir, testfile)

        self.fill_join_table(mid, qids)

    def create_delete_query(self, mid, new_row, out_dir):
        '''Create a delete query and write to the query file'''
        #choose field randomly from HI_ENTROPY_FIELDS
        rfield = sprandom.choice(tu.HI_ENTROPY_FIELDS)

        #SELECT id FROM main WHERE rfield = new_row[rfield]

        where_clause = self.select_str + 'FROM main WHERE ' + rfield + ' = ' +\
                       "'" + new_row[rfield] + "'"

        qid = self.qid_id_generator.get_id()
        qfilename = os.path.join(out_dir,"delete_query_" + str(qid) + ".q")
        qfile = open(qfilename, 'w')
        self.write_query(qid, where_clause, qfile)
        qfile.close()

        self.fill_mod_query_table(mid, qid, where_clause)
        return (qfilename, qid)

    def create_insert_query(self, mid, new_row, out_dir):
        '''Create an insert query and write to the query file'''
        # Choose field randomly from HI_ENTROPY_FIELDS
        rfield = sprandom.choice(tu.HI_ENTROPY_FIELDS)
        where_clause = self.select_str + 'FROM main WHERE ' + rfield + ' = ' +\
                       "'" + new_row[rfield] + "'"

        qid = self.qid_id_generator.get_id()
        qfilename = os.path.join(out_dir,"insert_query_" + str(qid) + ".q")
        qfile = open(qfilename, 'w')
        self.write_query(qid, where_clause, qfile)
        qfile.close()

        self.fill_mod_query_table(mid, qid, where_clause)
        return (qfilename, qid)

    def write_query_test(self, qfilename, testfile):
        '''Write query test to test file'''
        # The scripts want all paths relative to the directory the script
        # is in. Since qfilename is in the same directory, just remove 
        # the path.
        qbase = os.path.basename(qfilename)
        cmd = 'UnloadedQueryRunner ' + qbase + ' 1'
        testfile.write(cmd + '\n')


    def write_insert_mod(self, mid, new_row, out_dir):
        '''Write insert mod test to test file'''
        
        # create a file to contain the insert commands
        lr_id = self.lr_test_id_generator.get_id()
        rfilename = os.path.join(out_dir, "insert_" + str(lr_id) + '.lr')
        rfile = open(rfilename, 'w')

        rfile.write('UnloadedModifyArgumentScript\n')
        rfile.write(str(mid) + '\n')
        rfile.write('INSERT\n')
        rfile.write(new_row['raw_data'] + '\n')
        rfile.write('ENDDATA\n')

        rfile.close()
        return rfilename

    def create_insert_mod(self, mid, new_row, out_dir, testfile):
        '''create insert mod file and Write insert mod test to test file'''

        rfilename = self.write_insert_mod(mid, new_row, out_dir)
        # The scripts want all paths relative to the directory the script
        # is in. Since rfilename is in the same directory, just remove 
        # the path.
        base = os.path.basename(rfilename)
        testfile.write('CallRemoteScript ' + base + '\n')

    def write_delete_mod(self, mid, new_row, out_dir):
        '''Write delete mod test to test file'''
        
        # create a file to contain the insert commands
        lr_id = self.lr_test_id_generator.get_id()
        rfilename = os.path.join(out_dir, "delete_" + str(lr_id) + '.lr')
        rfile = open(rfilename, 'w')

        rfile.write('VariableDelayModifyArgumentScript\n')
        rfile.write(str(mid) + '\n')
        rfile.write('NO_DELAY\n')
        rfile.write('DELETE\n')
        rfile.write(str(new_row['id']) + '\n')
        rfile.write('ENDDATA\n')

        rfile.close()
        return rfilename

    def create_delete_mod(self, mid, new_row, out_dir, testfile):
        '''create delete mod file and Write delete mod test to test file'''

        rfilename = self.write_delete_mod(mid, new_row, out_dir)
        # The scripts want all paths relative to the directory the script
        # is in. Since rfilename is in the same directory, just remove 
        # the path.
        base = os.path.basename(rfilename)
        testfile.write('CallRemoteScript ' + base + '\n')

    def create_update_test_script(self, mid, qfiles, new_row, mod_field, new_value, \
                                  out_dir, testfile):
        '''Create update test which consists of a set of queries,
           an update and the same set of queries again'''
        for qfilename in qfiles:
            self.write_query_test(qfilename, testfile)
        
        self.create_update_mod(mid, new_row, mod_field, 
                               new_value, out_dir, testfile)

        for qfilename in qfiles:
            self.write_query_test(qfilename, testfile)
        
        self.fill_mods_table(mid, "update", new_row['id'])
        

    def create_update_mod(self, mid, new_row, mod_field, 
                         new_value, out_dir, testfile):
        '''create update mod file and Write update mod test to test file'''

        rfilename = self.write_update_mod(mid, new_row, mod_field, new_value, 
                                     out_dir)
        # The scripts want all paths relative to the directory the script
        # is in. Since rfilename is in the same directory, just remove 
        # the path.
        base = os.path.basename(rfilename)
        testfile.write('CallRemoteScript ' + base + '\n')


    def write_update_mod(self, mid, new_row, mod_field, 
                         new_value, out_dir):
        '''Write update mod test'''
        
        # create a file to contain the insert commands
        lr_id = self.lr_test_id_generator.get_id()
        rfilename = os.path.join(out_dir, "update_" + str(lr_id) + '.lr')
        rfile = open(rfilename, 'w')

        rfile.write('VariableDelayModifyArgumentScript\n')
        rfile.write(str(mid) + '\n')
        rfile.write('NO_DELAY\n')
        rfile.write('UPDATE\n')
        rfile.write(new_row['id'] + '\n')
        rfile.write(mod_field + '\n')
        rfile.write(new_value + '\n')
        rfile.write('ENDDATA\n')

        rfile.close()
        return rfilename
        
    def create_update_queries(self, mid, mod_field, new_value, orig_value, new_row, \
                              out_dir):
        '''Create update queries.  One that matches before the update,
           one after, and one both times'''
        # Put 3 queries in one query file


        # choose a HI_ENTROPY_FIELD other than mod_field
        unmatched_entropy_field = list(tu.HI_ENTROPY_FIELDS)
        try:
            unmatched_entropy_field.remove(mod_field)
        except ValueError:
            # Value wasn't in the list of hi_entropy_fields
            pass
        other_field = sprandom.choice(unmatched_entropy_field)
        other_field_value = new_row[other_field]
        

        qid_list = list()
        # (pre) matches the row before the change
        qid = self.qid_id_generator.get_id()
        qid_list.append(qid)
        # name the query file based on the first qid of the 3 - should be ok
        qfilename = os.path.join(out_dir,"update_query_" + str(qid) + ".q")
        qfile = open(qfilename, 'w')

        # put ZIP last since it will probably have more matches
        if mod_field == sv.enum_to_sql_name(sv.VARS.ZIP_CODE):
            first_pre_and_term = other_field + ' = ' + \
                "'" + other_field_value + "'"
            first_post_and_term = first_pre_and_term
            second_pre_and_term = mod_field + ' = ' + "'" + orig_value + "'" 
            second_post_and_term = mod_field + ' = ' + "'" + new_value + "'" 
        else:
            first_pre_and_term = mod_field + ' = ' + "'" + orig_value + "'" 
            first_post_and_term = mod_field + ' = ' + "'" + new_value + "'" 
            second_pre_and_term = other_field + ' = ' + \
                "'" + other_field_value + "'"
            second_post_and_term = second_pre_and_term

        where_clause = self.select_str + ' FROM main WHERE ' +  \
            first_pre_and_term + ' AND ' + second_pre_and_term 
        self.write_query(qid, where_clause, qfile)
        self.fill_mod_query_table(mid, qid, where_clause)

        # (post) matches the row after the change
        qid = self.qid_id_generator.get_id()
        qid_list.append(qid)
        where_clause = self.select_str + ' FROM main WHERE ' + \
            first_post_and_term + ' AND ' + second_post_and_term 
        self.write_query(qid, where_clause, qfile)
        self.fill_mod_query_table(mid, qid, where_clause)

        # (both) matches the row before and after the change
        qid = self.qid_id_generator.get_id()
        qid_list.append(qid)
        where_clause = self.select_str + ' FROM main WHERE ' + other_field +\
                       ' = ' + "'" + other_field_value + "'"
        self.write_query(qid, where_clause, qfile)
        self.fill_mod_query_table(mid, qid, where_clause)
        
        qfile.close()

        return([qfilename], qid_list)

    def write_query(self, qid, where_clause, qfile):
        '''Write query string with the qid to the query file'''
        qfile.write(str(qid) + " " + where_clause + "\n")
