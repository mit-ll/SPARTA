#!/bin/bash

username='TBD'                 # Needs to be set to the local user name
performer='bll'                # Needs to match the general naming convention of
                               # muddler and test-gen files
testname='sample-simple'       # Needs to match the test that is being run by
                               # the relevant muddler file
num_clients=5                  # Number of subscribers. Default: 5. ROE variable n.
num_pubs=10000                 # Number of publications. 
subs_per_client='CONSTANT 1'   # Default: 'POISSON 2' (ROE variable gamma)
disjunction_prob='0.5'         # Default: 0.5
threshold_prob=0               # Default: 0.0
conjunction_size='POISSON 2'
disjunction_size='POISSON 2'
unique_matches='CONSTANT 2'    # Default: 'POISSON 2' (ROE variable beta) 
                               # [max = #of fields - conjunction_size + 1]
replication_factor=1           # Put > 1 for higher match rates; make it 
                               # divisible by num_clients * subs_per_client)
overgeneration_factor='1.3'    # Keep this at 1 if doing CONSTANT stuff, and 
                               # > 1 if doing POISSON. Making this too large
                               # will deflate observed match rate
keep_exhausted_fields='False'  # Set this to true iff using a high 
                               # conjunction_size (i.e., close to # of fields)
rand_seed=$RANDOM              # Default: 0 ($RANDOM generates 0-32767)
num_pubs_per_conj=20           # Used only for mixed pub-sub tests. Default: 0.
test_script_dir="/home/$username/trunk/scripts-config/ta3/test-scripts"
archive_dir="/home/$username/spar-archive"
runner_dir="/home/$username/trunk/scripts-config/ta3/remote-runner-scripts"
fields_dir="/home/$username/spar-fields"
generator_path="/home/$username/trunk/cpp/test-harness/ta3/pub-sub-gen/opt/ta3-test-generator"
log_collector_dir="/home/$username/trunk/scripts-config/common/scripts"

# NOTE some rules of thumb for num_pubs_per_conj settings 
# and WAIT settings in the muddler...
#   num_clients * avg_subs_per_client = total_num_subs
#   min(total_num_subs * PERCENT_BACKGROUND_SUBS / NUM_UPDATE_SETS,
#       avg_subs_per_harness) = num_subs_per_set
#   num_subs_per_set * avg_conj_per_sub * num_pubs_per_conj = 
#       duration of verification publication sequence
# PRE_MODIFY_WAIT should be long enough for a few verification publications 
#   to be observed before a subscription set gets applied
# MODIFY_WAIT should be such that PRE_MODIFY_WAIT + MODIFY_WAIT + 
#   subscription_latency * num_subs_per_set is longer than the duration
#   of the verification publication sequence 

# Making sure required directories exist
mkdir -p $test_script_dir/$testname
mkdir -p $archive_dir/$testname

# Archiving initial test artifacts
# Copying this file
cp $runner_dir/test-gen-$performer-$testname.sh $archive_dir/$testname/
# Copying the muddler file
cp $runner_dir/$performer-${testname}_muddler.py $archive_dir/$testname/
# Copying the config file
cp $runner_dir/${performer}_config.py $archive_dir/$testname/

echo
echo "Creating test script files for $testname..."
# The test script file generation must be done from within the fields directory
cd $fields_dir
# Here is the command to make the test pubs and subs.
generator_cmd="$generator_path -f fields.config -o $test_script_dir/$testname/ -c $num_clients -p $num_pubs --rand_seed $rand_seed --subs_per_client '$subs_per_client' --disjunction_prob $disjunction_prob --conjunction_size '$conjunction_size' --disjunction_size '$disjunction_size' --match_rate '$unique_matches' --num_pubs_per_conj '$num_pubs_per_conj' --replication_factor '$replication_factor' --overgeneration_factor '$overgeneration_factor' --threshold_prob $threshold_prob"
if [ $keep_exhausted_fields == 'False' ]
  then
    script -c "$generator_cmd" $archive_dir/$testname/test-gen_${testname}_log.txt
  else
    script -c "$generator_cmd --keep_exhausted_fields" $archive_dir/$testname/test-gen_${testname}_log.txt
fi

echo
echo "Executing $testname..."
sleep 1;
cd $runner_dir
script -c "python remote_runner.py -c ${performer}_config.py -m ${performer}-${testname}_muddler.py -u $username -p SPARtest -l WARNING" $archive_dir/$testname/rr_log.txt

# If we are running locally, test scripts need to be manually copied to archive
# directory
cp -r $test_script_dir/$testname $archive_dir/$testname

# Finally, once the test ends, copy everything over to the local directory
#
# cd $log_collector_dir
# ./archive_test_artifacts.sh TCXXX_YYMMDD_HHMMSS
#
# Note: on the prior line, the directory name is supposed to be $testname followed by a timestamp.
#
# cd $runner_dir

# Delete empty logging directories created by remote_runner
rm -rf empty_log_dirs
