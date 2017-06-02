# *****************************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ABY, NJH
#  Description:        Script to fill a DB with SPAR data and optionally
#                      generate test queries/scripts.
# *****************************************************************************

#!/bin/bash

function usage
{
    echo
    echo "Create SPAR test database and test queries/scripts"
    echo "This should always be run from its original location in the release"
    echo "package (i.e., scripts-config/ta1/scripts)."
    echo
    echo "==== MariaDB Options ===="
    echo "--host                : MariaDB host (default: localhost)"
    echo "-d | --database       : MariaDB database (default: 1krows_100kBpr)"
    echo "-u | --user           : MariaDB user (default: root)"
    echo "-p | --password       : MariaDB password (default: SP@RTEST)"
    echo "==== Distribution Learning Options ===="
    echo "--data-dir            : Location where training data is located
                        (default: ~/spar-testing/data)"
    echo "--allow-missing-files : Allow distributions to be learned with
                        partial training data in --data-dir (default: not set)" 
    echo "==== Row Generation Options ===="
    echo "--data-seed           : Random seed to use for row generation"
    echo "--database-schema     : Database schema to use for row generation
                        (default: ../config/database_schemas/100kBpr_index_all_notes.csv)"
    echo "--num-rows            : Number of rows to generate (default: 1000)"
    echo "--mods-rows           : Number of modification rows to generate (default: 50)"
    echo "--row-width           : Approximate byte width of rows to generate 
                        (default: 100000)"
    echo "--num-processes       : Number of processes to use for row generation
                        (default: 1)"
    echo "--tmp-dir             : Location where temporary files will be generated
                        (default: /tmp/spar_generation_data)"
    echo "--generate-hashes     : Generate row hashes with data (default: not set)"
    echo "==== Query Generation Options ===="
    echo "--generate-queries    : Generate queries with data (default: not set)"
    echo "--query-seed          : Random seed to use for query generation"
    echo "--query-schema        : Query schema to use for query generation
                        (default: ../config/query_schemas/test.csv)"
    echo "--mods-dir            : Location where modifiction rows will be generated
                        (default: ~/spar-testing/mods)"
    echo "--results-dir         : Location where ground truth and test result
                        database will be generated 
                        (default: ~/spar-testing/results/results_databases)"
    echo "==== Test Script Generation Options ===="
    echo "--tests-dir           : Location where queries and test scripts will 
                        be generated (default: ~/spar-testing/tests)"
    echo "--performers          : Comma separated list of performers to generate
                        tests for from set [IBM1,IBM2,COL,MDB] 
                        (default: IBM1,IBM2,COL,MDB)"
    echo "==== Miscellaneous Options ===="
    echo "--prepend-timestamp   : Prepend timestamps to stdout of longer
                        processes; requires 'ts' to be installed (comes with 
                        the 'moreutils' package in Ubuntu) (default: not set)"
    echo "--verbose             : Output debug information (default: not set)"
    echo
}

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default option values
# MariaDB options
host=localhost
database=1krows_100kBpr
user=root
password=SP@RTEST
# Distribution learning options
data_dir=~/spar-testing/data
mods_dir=~/spar-testing/mods
allow_missing_files=0
# Row generation options
data_seed=0
mods_seed=$(($data_seed+42))
database_schema=$script_dir/../config/database_schemas/100kBpr_index_all_notes.csv
num_rows=1000
mods_rows=50
row_width=100000
num_processes=1
tmp_dir=/tmp/pre_test_generation_data
generate_hashes=0
# Query generation options
generate_queries=0
query_seed=0
query_schema=$script_dir/../config/query_schemas/test.csv
results_dir=~/spar-testing/results/results_databases
# Test script generation options
tests_dir=~/spar-testing/tests
performers=IBM1,IBM2,COL,MDB
# Miscellaneous options
prepend_timestamp=0
verbose=0

# Command line option parsing
while [ "$1" != "" ]; do
    case $1 in
        # MariaDB options
        -s | --host )           shift
                                host=$1
                                ;;
        -d | --database )       shift
                                database=$1
                                ;;
        -u | --user )           shift
                                user=$1
                                ;;
        -p | --password )       shift
                                password=$1
                                ;;
        # Distribution learning options
        --data-dir )            shift
                                data_dir=$1
                                ;;
        --mods-dir )            shift
                                mods_dir=$1
                                ;;
        --allow-missing-files ) allow_missing_files=1
                                ;;
        # Row generation options
        --data-seed )           shift
                                data_seed=$1
                                mods_seed=$(($data_seed+42))
                                ;;
        --database-schema )     shift
                                database_schema=$1
                                ;;
        --num-rows )            shift
                                num_rows=$1
                                ;;
        --mods-rows )           shift
                                mods_rows=$1
                                ;;
        --row-width )           shift
                                row_width=$1
                                ;;
        --num-processes )       shift
                                num_processes=$1
                                ;;
        --tmp-dir )             shift
                                tmp_dir=$1
                                ;;
        --generate-hashes )     generate_hashes=1
                                ;;
        # Query generation options
        --generate-queries )    generate_queries=1
                                ;;
        --query-seed )          shift
                                query_seed=$1
                                ;;
        --query-schema )        shift
                                query_schema=$1
                                ;;
        --results-dir )         shift
                                results_dir=$1
                                ;;
        # Test script generation options
        --tests-dir )           shift
                                tests_dir=$1
                                ;;
        --performers )          shift
                                performers=$1
                                ;;
        # Miscellaneous options
        --prepend-timestamp )   prepend_timestamp=1
                                ;;
        --verbose )             verbose=1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

# Print script parameters and other useful information
echo
echo "Date: $(date)"
echo "Parameter values:"
echo "   MariaDB options:"
echo "     --host: $host"
echo "     --database: $database"
echo "     --user: $user"
echo "     --password: $password"
echo
echo "   Distribution learning options:"
echo "     --data-dir: $data_dir"
echo "     --allow-missing-files: $allow_missing_files"
echo
echo "   Row generation options:"
echo "     --data-seed: $data_seed"
echo "     --database-schema: $database_schema"
echo "     --num-rows: $num_rows"
echo "     --row-width: $row_width"
echo "     --num-processes: $num_processes"
echo "     --tmp-dir: $tmp_dir"
echo "     --generate-hashes: $generate_hashes"
echo
echo "   Query generation options:"
echo "     --generate-queries: $generate_queries"
echo "     --query-seed: $query_seed"
echo "     --query-schema: $query_schema"
echo "     --results-dir: $results_dir"
echo
echo "   Test script generation options:"
echo "     --tests-dir: $tests_dir"
echo
echo "   Miscellaneous options:"
echo "     --prepend-timestamp: $prepend_timestamp"
echo "     --verbose: $verbose"
echo
git branch >& /dev/null
if [ $? == 0 ]; then
  echo "Current git information:"
  git_branch=$(git branch | grep "*" | awk '{ print $2 }')
  git_commit=$(git log -1 --pretty=format:"%H | %cd")
  echo "   Branch: $git_branch"
  echo "   Latest commit: $git_commit"
  echo
fi
git svn info >& /dev/null
if [ $? == 0 ]; then
  echo "Current git-svn information:"
  git svn info 
fi

# Establish all hardcoded paths that will be needed later
pickler=$script_dir/../../../spar_python/query_generation/pickler.py
gen_data=$script_dir/../../../bin/pre_test_generation.py
gen_create_sql=$script_dir/../../../bin/sql_generator.py
dir_importer=$script_dir/../../../bin/mysql-directory-importer
hash_matcher=$script_dir/../../../bin/fill_matching_record_hashes.py
ts_generator=$script_dir/../../../bin/create_scripts.py
stopwords=$script_dir/../config/stopwords.txt
results_db=$results_dir/$database.db
query_file=$tests_dir/queries/$database.txt
timings_file=$script_dir/../../../spar_python/test_generation/performer_timing_data.csv
if [ -e $results_db ]; then
  echo
  echo "ERROR: Results database already exists. Please delete/move $results_db"
  exit 1
fi
if [ -e $query_file ]; then
  echo
  echo "ERROR: Query file already exists. Please delete/move $query_file"
  exit 1
fi

# Activate the spar virtualenv
source $WORKON_HOME/sparta/bin/activate
if [ $? != 0 ]; then
  echo
  echo "ERROR: 'sparta' virtualenv does not exist, or \$WORKON_HOME is not set"
  echo "       appropriately. Please refer to the installation instructions."
  exit 1
fi

# Establish the base mysql command for later use
if [ "$password" != "" ]; then
 base_sql_cmd="mysql -u $user -p$password -h $host "
else
 base_sql_cmd="mysql -u $user -h $host "
fi

# Create the database
echo "Initializing MariaDB database..."
$base_sql_cmd -e "CREATE DATABASE $database"
if [ $? != 0 ]; then
  echo
  echo "ERROR: MariaDB database $database could not be created."
  exit 1
fi

# TODO(njhwang) Confirm the schema's last field is the hash field if
# --generate-hashes was specified

# Populate the database with empty tables
verbose_flag=""
if [ $verbose -eq 1 ]; then
  verbose_flag="--log-level DEBUG"
fi
python $gen_create_sql -c -s $database_schema --create-file $script_dir/create_table_$database.sql $verbose_flag
if [ $? != 0 ]; then
  echo
  echo "ERROR: Could not create initial SQL syntax for $database. See help"
  echo "       for $gen_create_sql."
  exit 1
fi

echo "Running the following commands to initialize tables:"
cat $script_dir/create_table_$database.sql
echo

$base_sql_cmd -D $database < $script_dir/create_table_$database.sql
if [ $? != 0 ]; then
  echo
  echo "ERROR: MariaDB database $database could not be created. Inspect"
  echo "       create_table_$database.sql file for errors."
  exit 1
fi

# Remove temporary directory if leftover from previous run
if [ -d "$tmp_dir" ]; then
  rm -rf $tmp_dir
fi

# Create directories
mkdir -p $tmp_dir
mkdir -p $results_dir/pickles
mkdir -p $tests_dir/queries
mkdir -p $mods_dir

# Determine optional pipe to timestamp utility
ts_flag="ts"

# Determine optional flags to data generator
gen_queries_flag=""
if [ $generate_queries -eq 1 ]; then
  gen_queries_flag="--generate-queries --query-generation-seed=$query_seed --query-schema-file=$query_schema --result-database-file=$results_db --list-of-queries-file=$query_file"
fi
missing_files_flag=""
if [ $allow_missing_files -eq 1 ]; then
  missing_files_flag="--allow-missing-files"
  echo "***********************************************"
  echo "*WARNING: ALLOWING MISSING DATA TRAINING FILES*"
  echo "*         RESULTS MAY NOT BE REPRODUCABLE     *"
  echo "***********************************************"
fi
verbose_flag=""
if [ $verbose -eq 1 ]; then
  verbose_flag="--verbose"
fi

# Update the number of workers so $dir_importer doesn't wait for more files than
# necessary
num_batches=`expr $num_rows / 1000`
if [ $num_batches -eq 0 ]; then
  num_processes=1
elif [ "$num_batches" -lt "$num_processes" ]; then
  num_processes=$num_batches
fi

# Start the data generator
echo
echo "Starting data generator..."
# TODO(njhwang) is there a cleaner way to conditionally pipe the command to
# $ts_flag if $prepend_timestamp is set?
if [ $prepend_timestamp -eq 1 ]
then
  python $gen_data $missing_files_flag --data-dir=$data_dir --seed=$data_seed --schema-file=$database_schema --num-rows=$num_rows --row_width=$row_width --num-processes=$num_processes --line-raw-file=$tmp_dir/spar_data.lineraw --named-pipes $gen_queries_flag $verbose_flag 2>&1 | $ts_flag &
else
  python $gen_data $missing_files_flag --data-dir=$data_dir --seed=$data_seed --schema-file=$database_schema --num-rows=$num_rows --row_width=$row_width --num-processes=$num_processes --line-raw-file=$tmp_dir/spar_data.lineraw --named-pipes $gen_queries_flag $verbose_flag &
fi

# Wait a bit and check if $gen_data returned any errors before continuing
dg_pid=$!
sleep 2
ps -p $dg_pid -o pid= >& /dev/null
if [ $? != 0 ]; then
  echo
  echo "ERROR: Data generator could not be started. See help for $gen_data."
  exit 1
fi

# Start the MariaDB data inserter
maria_pass_flags=""
if [ "$password" != "" ]; then
  maria_pass_flags="--pwd $password"
fi
gen_hashes_flag=""
if [ $generate_hashes -eq 1 ]; then
  gen_hashes_flag="--hash-rows"
fi
verbose_flag=""
if [ $verbose -eq 1 ]; then
  verbose_flag="--log-level 0"
fi
echo
echo "Started data inserter..."
if [ $prepend_timestamp -eq 1 ]
then
  $dir_importer --host $host --db $database --user $user $maria_pass_flags --schema-file $database_schema --num-files $num_processes --data-dir=$tmp_dir $gen_hashes_flag $verbose_flag --stopwords $stopwords 2>&1 | $ts_flag &
else
  $dir_importer --host $host --db $database --user $user $maria_pass_flags --schema-file $database_schema --num-files $num_processes --data-dir=$tmp_dir $gen_hashes_flag $verbose_flag --stopwords $stopwords &
fi

# Wait a bit and check if $gen_data returned any errors before continuing
di_pid=$!
sleep 2
ps -p $di_pid -o pid= >& /dev/null
if [ $? != 0 ]; then
  echo
  echo "ERROR: Data inserter could not be started. See help for $dir_importer."
  kill $dg_pid
  exit 1
fi

# Wait for processes to complete
echo
echo "Waiting for processes to complete..."
for job in `jobs -p`
do
  echo "Waiting for $job"
  wait $job
done


# Remove temporary files
rm $tmp_dir/*
rmdir $tmp_dir

# Verify that database was fully generated before continuing
# TODO should add checks for the notes and fingerprint columns as well for
# 100kBpr schemas; this will help detect "out of resources" errors during
# database generation
actual_rows=$($base_sql_cmd -D $database -e "SELECT COUNT(*) FROM base" | cut -d"	" -f 3 | tail -n +2)
if [ $? != 0 ]; then
  echo
  echo "ERROR: Could not count rows in base table of $database."
  exit 1
fi
if [ $actual_rows != $num_rows ]; then
  echo
  echo "ERROR: Only $actual_rows/$num_rows were generated in $database."
  exit 1
fi

# Create MariaDB indices and 'main' view
echo
echo "Creating MariaDB indices and views..."
verbose_flag=""
if [ $verbose -eq 1 ]; then
  verbose_flag="--log-level DEBUG"
fi
pass_flag=""
if [ "$password" != "" ]; then
  pass_flag="-p $password"
fi
python $gen_create_sql -i -s $database_schema --index-view-file $script_dir/create_index_view_$database.sql -D $database --db-host $host -u $user $pass_flag $verbose_flag
if [ $? != 0 ]; then
  echo
  echo "ERROR: Could not create index and view SQL syntax for $database. See "
  echo "       help for $gen_create_sql."
  exit 1
fi

echo "Running the following commands to initialize indices and views:"
cat $script_dir/create_index_view_$database.sql
echo

$base_sql_cmd $database < $script_dir/create_index_view_$database.sql
if [ $? != 0 ]; then
  echo
  echo "ERROR: MariaDB indices for $database could not be created. Inspect"
  echo "       create_index_view_$database.sql file for errors (note this "
  echo "       file will usually be removed after successful database "
  echo "       creation)."
  exit 1
fi
rm $script_dir/create_index_view_$database.sql

# Load the xml_value stored function
$base_sql_cmd -D $database < $script_dir/xml_value.sql
if [ $? != 0 ]; then
  echo
  echo "ERROR: Could not load XML functionality into $database."
  exit 1
fi

# TODO Modification generation is commented out and disabled for now. This is because it is time-consuming (learning has to be completely re-run in a new instance to generate the mods.lineraw file, which is redundant) and there seem to be stability problems with this consistently completing.

# Generate modifications
#python $gen_data $missing_files_flag --data-dir=$data_dir --seed=$mods_seed --schema-file=$database_schema --num-rows=$mods_rows --row_width=$row_width --num-processes=1 --line-raw-file=$mods_dir/mods.lineraw --named-pipes $gen_queries_flag $verbose_flag 2>&1

# Wait for modifications to complete
#echo "Modification generation starting. Waiting for it to complete"
#for job in `jobs -p`
#do
#  echo "Waiting for $job"
#  wait $job
#done

# Verify mods were produced correctly
#num_mods_produced=$(grep -c ^INSERT$ $mods_dir/mods.lineraw)
#if [ $num_mods_produced != $mods_rows ]; then
#    echo "ERROR: Incorrect number of modification rows produced"
#    echo "Expected $mods_rows, found $num_mods_produced"
#    echo "Aborting"
#    exit 1
#fi

if [ $generate_queries -eq 1 ]; then
  if [ $generate_hashes -eq 1 ]; then
    # Fill the results database with row hash information
    echo
    echo "Populating row hash information in $results_db..."
    cp $results_db $results_db.pre-hash
    verbose_flag=""
    if [ $verbose -eq 1 ]; then
      verbose_flag="--log-level DEBUG"
    fi
    pass_flag=""
    if [ "$password" != "" ]; then
      pass_flag="-p $password"
    fi
    python $hash_matcher --row-host $host -D $database -u $user $pass_flag -r $results_db $verbose_flag
    if [ $? != 0 ]; then
      echo
      echo "ERROR: Could not populate row hash information in $results_db."
      echo "       'SELECT *' queries may not have complete ground truth."
      exit 1
    fi
  fi

  # Make sure test script directories don't already exist
  performer_list=$(echo $performers | sed 's/,/\n/g')
  for performer in $performer_list; do
    if [ -d "$tests_dir/$performer/$database" ]; then
      echo
      echo "ERROR: Test scripts already exist for "
      echo "       $tests_dir/$performer/$database."
      echo "       Please delete move existing test scripts and run"
      echo "       $ts_generator again."
      exit 1
    fi
  done

  # Generate test scripts
  echo
  echo "Generating test scripts in $tests_dir..."
  python $ts_generator -r $results_db -p $performers -o $tests_dir -t $timings_file
  if [ $? != 0 ]; then
    echo
    echo "ERROR: Could not generate test scripts. See help for $ts_generator."
    exit 1
  fi
fi

deactivate

echo
echo "Done: $(date)"
