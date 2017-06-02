#!/bin/bash

function parse {
   full_dir="/home/y4n9/spar/tests/stealth/"$1"circuit/"
   num_circuits=`expr $(ls -l $full_dir | wc -l) - 1`
   for i in $(seq 1 ${num_circuits})
   do
      circuit=${full_dir}${i}
      echo "Processing ${circuit}"
      python main.py -p $circuit
   done
}

parse "01_one_of_each_small/F=1/"
parse "01_one_of_each_small/F=2/"
parse "01_one_of_each_small/F=3/"
parse "02_one_of_each_medium/F=1/"
parse "02_one_of_each_medium/F=2/"
parse "02_one_of_each_medium/F=3/"
parse "03_one_of_each_large/F=1/"
parse "03_one_of_each_large/F=2/"
parse "03_one_of_each_large/F=3/"
parse "04_single_gate_type/"
parse "05_varying_param/F=1/"

for x in "X=10" "X=100" "X=500" "X=1000"
do
   for fx in "fx=.25" "fx=.0000001"
   do
      parse "05_varying_param/F=2/${x}/${fx}/"
   done
done

parse "05_varying_param/F=3/"

