#!/bin/bash

# Copies all items in the directory name passed into --input-dir from all hosts
# defined in --hosts-file and copies them to --output-dir on the workstation
# this is run from

function usage
{
    echo ""
    echo "Archive SPAR data from multiple hosts"
    echo "--input-dir         : directory to archive on each host"
    echo "--output-dir        : directory to archive to on local host"
    echo "--hosts-file        : hosts file"
    echo "--user              : user to login to remote hosts"
    echo ""
}

# Verify hosts_file exists
if [ ! -f $hosts_file ]; then
  echo
  echo "ERROR: Hosts file could not be found at $hosts_file"
  exit 1
fi

# Command line option parsing
while [ "$1" != "" ]; do
    case $1 in
        --input-dir )           shift
                                input_dir=$1
                                ;;
        --output-dir )          shift
                                output_dir=$1
                                ;;
        --hosts-file )          shift
                                hosts_file=$1
                                ;;
        --user )                shift
                                user=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [ "$input_dir" == "" ]; then
  echo
  echo "ERROR: --input-dir must be defined"
  exit 1
fi
if [ "$user" == "" ]; then
  echo
  echo "ERROR: --user must be defined"
  exit 1
fi

base_input_dir=$(basename $input_dir)
mkdir -p $output_dir/$base_input_dir/
declare -a host_array=( `awk -F, '{ print $1 }' $hosts_file`)
for host in "${host_array[@]}"
do
  if [ "$host" != "localhost" -a "$host" != "host" ]; then
    echo Copying from $user@$host...
    echo Source: $input_dir
    echo Destinaton: $output_dir/$base_input_dir
    scp -o PasswordAuthentication=no -o StrictHostKeyChecking=no -r $user@$host:$input_dir/* $output_dir/$base_input_dir/ 
  fi
done
