import os
import sys
# Note that realpath (as opposed to abspath) also expands symbolic
# links so the path points to the actual file. This is important when
# installing scripts in the install directory.  Scripts will be
# symbolic linked to the install directory. When a script is run from
# the install directory, realpath will convert it to the actual path
# where the script lives. Appending base_dir to sys.path (as done
# below) allows the imports to work properly.
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
import spar_python.report_generation.ta1.ta1_database as ta1_database
import re
import spar_python.query_generation.query_ids as qids
FIELD_TO_TYPE = {'lname' : "string",
                 'foo' : "integer",
                 'dob' : 'date',
                 'city' : 'string',
                 'zip' : 'string',
                 'income' : 'integer',
                 'fname' : 'string',
                 'address' : 'string',
                 'weeks_worked_last_year' : 'integer',
                 'hours_worked_per_week' : 'integer'}
def main():
    parser = OptionParser()    
    input_group = OptionGroup(parser, 'Options')
    input_group.add_option("-r", "--results-db", dest="rdb",
                      help="Results_db to fix the atomic queries")
    parser.add_option_group(input_group)
    (cl_flags, _) = parser.parse_args()
    if not cl_flags.rdb:
        print "ERROR: No results_db specified. Specify --results-db"
        exit()
    #set up database connection
    resultdb = ta1_database.Ta1ResultsDB(cl_flags.rdb)
    #get record size and num records
    cmd = "select db_record_size, db_num_records from atomic_queries limit 1"
    resultdb._execute(cmd)
    [(record_size, num_records)] = resultdb._fetchall()
    #get all the where clauses for P1 queries
    cmd = "select qid, where_clause from full_queries where (sub_category = 'eqand' or"+\
    " sub_category = 'eqor' or sub_category = 'eq') and supported_by_ibm_ta2 = 0"
    resultdb._execute(cmd)
    qid_wheres = resultdb._fetchall()
    
    #split the where_clauses into their component parts and insert them 
    #into the atomic queries table if they don't already exist 
    for (qid, where_clause) in qid_wheres:
        #clean out the full_to_atomic_junction table for that query
        cmd = "delete from full_to_atomic_junction where full_row_id = " + str(qid)
        print cmd
        resultdb._execute(cmd)
        null = resultdb._fetchall()
        where_clause = where_clause.replace(")", "")
        where_clause = where_clause.replace("(", "")
        where_clause = where_clause.replace("ORDER BY", "#")
        where_clause = where_clause.split("#")[0].strip()
        where_clause = re.sub("M_OF_N[0-9]+, [0-9]+,", '', where_clause)
        where_clause = where_clause.replace(" AND ", ",")
        where_clause = where_clause.replace(" OR ", ",")
        atomic_where_clauses = where_clause.split(",")
        process_atomic_wheres(atomic_where_clauses, resultdb, record_size, num_records, qid)
    
    cmd = "select qid, where_clause from full_queries where (sub_category = 'eqand' or"+\
    " sub_category = 'eqor' or sub_category = 'eq') and supported_by_ibm_ta2 = 1"
    resultdb._execute(cmd)
    qid_wheres = resultdb._fetchall()

    #split the where_clauses into their component parts and insert them 
    #into the atomic queries table if they don't already exist 
    for (qid, where_clause) in qid_wheres:
        #clean out the full_to_atomic_junction table for that query
        cmd = "delete from full_to_atomic_junction where full_row_id = " + str(qid)
        print cmd
        resultdb._execute(cmd)
        null = resultdb._fetchall()
        where_clause = where_clause.replace(" AND ", "#")
        atomic_temp = iter(where_clause.split("#"))
        atomic_where_clauses = [w+" AND "+next(atomic_temp, '') if "BETWEEN" in w else w for w in atomic_temp]
        process_atomic_wheres(atomic_where_clauses, resultdb, record_size, num_records, qid)
    
def process_atomic_wheres(atomic_where_clauses, resultdb, record_size, num_records, qid):
        for atomic_where_clause in atomic_where_clauses:
            atomic_where_clause = atomic_where_clause.strip()
            cmd = "select aqid from atomic_queries where where_clause = \"" + atomic_where_clause + "\""
            resultdb._execute(cmd)
            aqid = resultdb._fetchall()
            if aqid == []:
                afield = atomic_where_clause.split( )[0].strip();
                afield_type = FIELD_TO_TYPE[afield]
                atomic_where_aqid = qids.query_id()
                cmd = "insert into atomic_queries (where_clause, db_record_size,"+\
                " db_num_records, category, field_type, field, num_matching_records, aqid) values "+\
                "(\""+str(atomic_where_clause)+"\", "+str(record_size)+", "+str(num_records)+", \"EQ\",\""+str(afield_type)+"\",\""+str(afield)+\
                "\", 1, "+str(atomic_where_aqid)+")"
                print cmd
                resultdb._execute(cmd)
                atomic_ids = resultdb._fetchall()
            else:
                atomic_where_aqid = aqid[0][0]
            #rebuild mapping between full and atomic queries
            cmd = "insert into full_to_atomic_junction (full_row_id, atomic_row_id) values ("+\
            str(qid)+","+str(atomic_where_aqid)+")"
            print cmd
            resultdb._execute(cmd)
            null = resultdb._fetchall()        
    
if __name__ == "__main__":
    main()
