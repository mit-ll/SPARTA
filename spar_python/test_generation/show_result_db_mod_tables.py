from optparse import OptionParser
import sys
import os

this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database



def dump_full_query_table(resultdb):

    get_these = []
    for field, dtype in rdb.DBF_FIELDS_TO_TYPES.iteritems():
        print field,dtype
        print type(field)
        print type(dtype)
        qfield = "\'" + field + "\'"
        get_these.append(field)

    cmd = "SELECT " + ", ".join(get_these) + " FROM full_queries"

    resultdb._execute(cmd)
    answer = resultdb._fetchall()

    print "*** Found ", len(answer),"queries"
    for line  in answer:
        print "--------------------"
        for field, name in zip(line, get_these):
           print name,"=",field
    print "*** Found ", len(answer),"queries"


def dump_table(table_name, table_fields_to_types, resultdb, show_types=True):

    print "\n**** Table ",table_name
    if (show_types):
        print "** Expected types for table:"

    get_these = []
    for field, dtype in table_fields_to_types.iteritems():
        if show_types:
            print field,rdb.FIELD_TYPES.to_string(dtype)
        get_these.append(field)

    cmd = "SELECT " + ", ".join(get_these) + " FROM " + table_name

    resultdb._execute(cmd)
    answer = resultdb._fetchall()

    print "** Found", len(answer),"rows in table:",table_name
    for line  in answer:
        print "--------------------"
        for field, name in zip(line, get_these):
           print name,"=",field,type(field)





def main():

    #
    # Specify options
    #

    parser = OptionParser()
    parser.add_option('-d', '--result_database',
                      dest="resultdb_name",
                      help='path to the result database')
    (options, args) = parser.parse_args()



    resultdb = ta1_database.Ta1ResultsDB(options.resultdb_name)


    dump_table(rdb.MODS_TABLENAME, rdb.MODS_FIELDS_TO_TYPES, resultdb)

    dump_table(rdb.MODQUERIES_TABLENAME, rdb.MODQUERIES_FIELDS_TO_TYPES, 
               resultdb)

    dump_table(rdb.M2MQ_TABLENAME, rdb.M2MQ_FIELDS_TO_TYPES, resultdb)

    resultdb.close()


if __name__ == "__main__":
    main()
