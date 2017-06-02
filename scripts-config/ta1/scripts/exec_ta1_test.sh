# *****************************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            NJH
#  Description:        Script to execute a SPAR database test.
# *****************************************************************************

#!/bin/bash

function usage
{
    echo
    echo "Execute a TA1 test, archive artifacts, parse, and perform analysis."
    echo "This should always be run from its original location in the release"
    echo "package (i.e., scripts-config/ta1/scripts)."
    echo
    echo "==== Remote Host Options ===="
    echo "--client-host-th     : client hostname for test harness use
                       (default: localhost)"
    echo "--client-host-perf   : client hostname for performer use
                       (default: localhost)"
    echo "--server-host-th     : server hostname for test harness use
                       (default: localhost)"
    echo "--server-host-perf   : server hostname for performer use
                       (default: localhost)"
    echo "--tp-hosts           : third party hostnames; comma separated, no
                       spaces (default: not set)"
    echo "-u | --user          : user name for all hosts involved in test
                       (default: lincoln)"
    echo "-p | --password      : password for --user (default: not set)"
    echo "--run-hosts-file     : hosts file to use for running SUT components
                       (default: ../../common/config/hosts/localhost_only.csv)"
    echo "--archive-hosts-file : hosts file to use for test artifact retrieval
                       (default: ../../common/config/hosts/localhost_only.csv)"
    echo "==== Test Options ===="
    echo "--performer          : performer under test (default: MDB)"
    echo "-t | --test-case     : test case name"
    echo "--rr-config          : Location where remote_runner config file is
                       located"
    echo "-D | --database      : MariaDB database for test"
    echo "--results-db         : Location of sqlite3 results database"
    echo "--throughput         : Will treat tests as throughput tests during
                       parsing"
    echo "--performance        : Will enable event message reporting in SUTs"
    echo "==== TA1 Baseline Options ===="
    echo "--db-user            : user for --database (default: root)"
    echo "--db-password        : password for --database (default: SP@RTEST)"
    echo "--schema             : database schema to use during test
                       (default: ../config/database_schemas/100kBpr_index_all_notes.csv)"
    echo "==== Base Directory Options ===="
    echo "--local-trunk-dir    : Location where trunk is located
                       (default: ~/spar-testing/trunk)"
    echo "--local-test-dir     : Location where test scripts are located
                       (default: ~/spar-testing/tests)"
    echo "--local-results-dir  : Location where results directories are located
                       (default: ~/spar-testing/results)"
    echo "--local-debug-dir    : Location where debug information will be
                       generated (default: ~/spar-testing/debug)"
    echo "--local-archive-dir  : Location where test artifacts will be archived
                       (default: ~/spar-testing/archive)"
    echo "==== Miscellaneous Options ===="
    echo "--verbose            : Output debug information (default: not set)"
    echo
}

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default option values
# Remote host options
client_host_th="localhost"
client_host_perf="localhost"
server_host_th="localhost"
server_host_perf="localhost"
tp_hosts=""
user=lincoln
password=""
run_hosts_file=$script_dir/../../common/config/hosts/localhost_only.csv
archive_hosts_file=$script_dir/../../common/config/hosts/localhost_only.csv
# Test options
performer="MDB"
test_case=""
rr_config=$script_dir/../remote_runners/exec_ta1_test/baseline_config.py
database=""
results_db=""
throughput=0
performance=0
baseline_mods=0
# TA1 baseline options
db_user=root
db_password=SP@RTEST
schema=$script_dir/../config/database_schemas/100kBpr_index_all_notes.csv
stopwords=$script_dir/../config/stopwords.txt
# Base directory options
local_trunk_dir=$script_dir/../../..
local_test_dir=~/spar-testing/tests
local_results_dir=~/spar-testing/results
local_debug_dir=~/spar-testing/debug
local_archive_dir=~/spar-testing/archive
# Miscellaneous options
verbose=0

# Command line option parsing
while [ "$1" != "" ]; do
    case $1 in
        # Remote host options
        --client-host-th )      shift
                                client_host_th=$1
                                ;;
        --client-host-perf )    shift
                                client_host_perf=$1
                                ;;
        --server-host-th )      shift
                                server_host_th=$1
                                ;;
        --server-host-perf )    shift
                                server_host_perf=$1
                                ;;
        --tp-hosts )            shift
                                tp_hosts=$1
                                ;;
        -u | --user )           shift
                                user=$1
                                ;;
        -p | --password )       shift
                                password=$1
                                ;;
        --run-hosts-file )      shift
                                run_hosts_file=$1
                                ;;
        --archive-hosts-file )  shift
                                archive_hosts_file=$1
                                ;;
        # Test options
        --performer )           shift
                                performer=$1
                                ;;
        -t | --test-case )      shift
                                test_case=$1
                                ;;
        --rr-config )           shift
                                rr_config=$1
                                ;;
        -D | --database )       shift
                                database=$1
                                ;;
        --results-db )          shift
                                results_db=$1
                                ;;
        --throughput )          throughput=1
                                ;;
        --performance )         performance=1
                                ;;
        --baseline-mods )       baseline_mods=1
                                ;;
        # TA1 baseline options
        --db-user )             shift
                                db_user=$1
                                ;;
        --db-password )         shift
                                db_password=$1
                                ;;
        --schema )              shift
                                schema=$1
                                ;;
        # Base directory options
        --local-trunk-dir )     shift
                                local_trunk_dir=$1
                                ;;
        --local-test-dir )      shift
                                local_test_dir=$1
                                ;;
        --local-results-dir )   shift
                                local_results_dir=$1
                                ;;
        --local-debug-dir )     shift
                                local_debug_dir=$1
                                ;;
        --local-archive-dir )   shift
                                local_archive_dir=$1
                                ;;
        # Miscellaneous options
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

# Validate required input parameters
if [ "$client_host_th" == "" ]; then
  echo
  echo "ERROR: --client-host-th must be defined"
  exit 1
fi
if [ "$client_host_perf" == "" ]; then
  echo
  echo "ERROR: --client-host-perf must be defined"
  exit 1
fi
if [ "$server_host_th" == "" ]; then
  echo
  echo "ERROR: --server-host-th must be defined"
  exit 1
fi
if [ "$server_host_perf" == "" ]; then
  echo
  echo "ERROR: --server-host-perf must be defined"
  exit 1
fi
if [ "$performer" == "" ]; then
  echo
  echo "ERROR: --performer must be defined"
  exit 1
fi
if [ "$test_case" == "" ]; then
  echo
  echo "ERROR: --test-case must be defined"
  exit 1
fi
if [ "$rr_config" == "" ]; then
  echo
  echo "ERROR: --rr-config must be defined"
  exit 1
fi
if [ "$database" == "" ]; then
  echo
  echo "ERROR: --database must be defined"
  exit 1
fi
if [ "$results_db" == "" ]; then
  echo
  echo "ERROR: --results-db must be defined"
  exit 1
fi

# Validate command line arguments representing paths
if [ ! -f $run_hosts_file ]; then
  echo
  echo "ERROR: Hosts file could not be found at $run_hosts_file"
  exit 1
fi
if [ ! -f $archive_hosts_file ]; then
  echo
  echo "ERROR: Hosts file could not be found at $archive_hosts_file"
  exit 1
fi
if [ ! -f $rr_config ]; then
  echo
  echo "ERROR: remote_runner config file could not be found at $rr_config"
  exit 1
fi
if [ ! -f $results_db ]; then
  echo
  echo "ERROR: Results database could not be found at $results_db"
  exit 1
fi
if [ ! -f $schema ]; then
  echo
  echo "ERROR: Database schema could not be found at $schema"
  exit 1
fi
if [ ! -f $stopwords ]; then
  echo
  echo "ERROR: Stopwords file could not be found at $stopwords"
  exit 1
fi
if [ ! -d $local_trunk_dir ]; then
  echo
  echo "ERROR: Local trunk could not be found at $local_trunk_dir"
  exit 1
fi
if [ ! -d $local_test_dir ]; then
  echo
  echo "ERROR: Local tests could not be found at $local_test_dir"
  exit 1
fi

# Print script parameters and other useful information
echo
echo "Date: $(date)"
echo "Parameter values:"
echo "  Remote host options:"
echo "    --client-host-th: $client_host_th"
echo "    --client-host-perf: $client_host_perf"
echo "    --server-host-th: $server_host_th"
echo "    --server-host-perf: $server_host_perf"
echo "    --tp-hosts: $tp_hosts"
echo "    --user: $user"
echo "    --password: $password"
echo "    --run-hosts-file: $run_hosts_file"
echo "    --archive-hosts-file: $archive_hosts_file"
echo "  Test options:"
echo "    --performer: $performer"
echo "    --test-case: $test_case"
echo "    --rr-config: $rr_config"
echo "    --database: $database"
echo "    --results-db: $results_db"
echo "    --throughput: $throughput"
echo "    --performance: $performance"
echo "    --baseline-mods: $baseline_mods"
echo "  TA1 baseline options:"
echo "    --db_user: $db_user"
echo "    --db_password: $db_password"
echo "    --schema: $schema"
echo "  Base directory options"
echo "    --local-trunk-dir: $local_trunk_dir"
echo "    --local-test-dir: $local_test_dir"
echo "    --local-results-dir: $local_results_dir"
echo "    --local-debug-dir: $local_debug_dir"
echo "    --local-archive-dir: $local_archive_dir"
echo "  Miscellaneous options"
echo "    --verbose: $verbose"
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
rr_exec=$script_dir/../../../bin/remote_runner.py
rr_muddler=$script_dir/../remote_runners/exec_ta1_test/muddler.py
rr_parser=$script_dir/../remote_runners/exec_ta1_test/arg_parser.py
archive_exec=$script_dir/../../common/scripts/archive_test_artifacts.sh
client_parse_exec=$script_dir/../../../bin/parse_client_harness_log.py
server_parse_exec=$script_dir/../../../bin/parse_server_harness_log.py

# Make necessary directories if they don't already exist
mkdir -p $local_results_dir
mkdir -p $local_archive_dir
mkdir -p $local_debug_dir

# Back up the existing results database
cp $results_db $results_db.$(date +%Y%m%d_%H%M%S).bkp
if [ $? != 0 ]; then
  echo
  echo "ERROR: Could not back up $results_db."
  exit 1
fi

# Activate the sparta virtualenv
source $WORKON_HOME/sparta/bin/activate
if [ $? != 0 ]; then
  echo
  echo "ERROR: 'sparta' virtualenv does not exist, or \$WORKON_HOME is not set"
  echo "       appropriately. Please run the appropriate setup script from "
  echo "       scripts-config/common/scripts/initial_env_setup."
  exit 1
fi

# Execute remote_runner for the specified test case
tp_args=""
if [ "$tp_hosts" != "" ]; then
  tp_args="--tp-hosts $tp_hosts"
fi
performance_flag=""
if [ $performance -eq 1 ]; then
  performance_flag="--enable-eventmsg"
fi
verbose_flag=""
if [ $verbose -eq 1 ]; then
  verbose_flag="-l DEBUG"
fi
debug_flag=""
if [ $verbose -eq 1 ]; then
  debug_flag="--debug"
fi

rr_extra_args="--extra-args=-p $performer -t $test_case --hosts-file $run_hosts_file --client-host-th $client_host_th --client-host-perf $client_host_perf --server-host-th $server_host_th --server-host-perf $server_host_perf $tp_args $performance_flag -D $database --db-user $db_user --db-password $db_password --db-schema-file $schema --local-trunk-dir $local_trunk_dir --local-test-dir $local_test_dir --local-results-dir $local_results_dir --local-debug-dir $local_debug_dir $debug_flag --stopwords-file $stopwords"

if [ "$password" != "" ]; then
  rr_output=$(python $rr_exec -c $rr_config "$rr_extra_args" -m $rr_muddler -a $rr_parser -u $user -p $password --screen rr_$test_case $verbose_flag 2>&1 | tee /dev/stderr)
else
  rr_output=$(python $rr_exec -c $rr_config "$rr_extra_args" -m $rr_muddler -a $rr_parser -u $user --screen rr_$test_case $verbose_flag 2>&1 | tee /dev/stderr)
fi

# TODO(njhwang) this doesn't properly handle failures in remote_runner, probably
# due to the pipe and tee; need to make sure the script exists here so the
# archiver doesn't start archiving the entire filesystem
if [ $? != 0 ]; then
  echo
  echo "ERROR: remote_runner did not successfully complete. Aborting script."
  exit 1
fi

# Define and create archive paths
local_results_dir=$(echo "$rr_output" | grep "Local results will be stored in " | sed 's/^INFO: Local results will be stored in \(.*\)\s*$/\1/')
local_results_dirname=$(basename $local_results_dir)
remote_results_dir=$(echo "$rr_output" | grep "Remote results will be stored in " | sed 's/^INFO: Remote results will be stored in \(.*\)\s*$/\1/')
remote_results_dirname=$(basename $remote_results_dir)
archive_results_dir=$local_archive_dir/$performer/$database/$remote_results_dirname
mkdir -p $local_archive_dir/$performer/$database

# Archive test artifacts from all machines specified in hosts file
$archive_exec --hosts-file $archive_hosts_file --input-dir $remote_results_dir --output-dir $local_archive_dir/$performer/$database --user $user

# Archive local test artifacts
# TODO do better error handling if this fails (or is not applicable)
cp -r $local_results_dir/* $archive_results_dir

echo Archived all test results to $archive_results_dir

# Parse the test results into the results database
throughput_flag=""
if [ $throughput -eq 1 ]; then
  throughput_flag="--throughput"
fi
baseline_mods_flag=""
if [ $baseline_mods -eq 1 ]; then
  baseline_mods_flag="--baseline"
fi
python $client_parse_exec -i $archive_results_dir -o $results_db $throughput_flag $baseline_mods_flag
if [ $? != 0 ]; then
  echo
  echo "ERROR: Test result parsing could not be completed. See help for "
  echo "$client_parse_exec."
  exit 1
fi
python $server_parse_exec -i $archive_results_dir -o $results_db
if [ $? != 0 ]; then
  echo
  echo "ERROR: Test result parsing could not be completed. See help for "
  echo "$server_parse_exec."
  exit 1
fi

deactivate

echo
echo "Done: $(date)"
