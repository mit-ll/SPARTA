#!/bin/bash

function usage
{
    echo "==== Test Options ===="
    echo "--results-db         : Location of sqlite3 results database"
    echo
}

results_db=""

while [ "$1" != "" ]; do
    case $1 in
        --results-db )          shift
                                results_db=$1
                                ;;
        # Miscellaneous options
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [ "$results_db" == "" ]; then
  echo
  echo "ERROR: --results-db must be defined"
  exit 1
fi

echo "Working on $results_db"

#fixing p1-and-num-records-matching-first-term
echo "Select qid from full_queries where sub_category='eqand';" | sqlite3 $results_db > fqid.txt

while read -r a; 
      do 
	echo "select atomic_row_id from full_to_atomic_junction where full_row_id=$a limit 1;"   | sqlite3 $results_db 
done < "fqid.txt" > aqid.txt

while read -r a; 
      do 
	echo "select num_matching_records from atomic_queries where aqid=$a limit 1;"   | sqlite3 $results_db
done < "aqid.txt" > acount.txt

while read -r a && read -r b <&3; 
      do 
	echo "update full_queries set p1_and_num_records_matching_first_term = $a where qid=$b;"   | sqlite3 $results_db
done < "acount.txt" 3<"fqid.txt" 

rm acount.txt aqid.txt fqid.txt

#fixing p1-or-sum-records-matching-each-term
echo "Select qid from full_queries where sub_category='eqor';" | sqlite3 $results_db > fqid.txt
while read -r a; 
      do 
	echo "select atomic_row_id from full_to_atomic_junction where full_row_id=$a;"   | sqlite3 $results_db 
done < "fqid.txt" > aqid.txt

while read -r a; 
      do 
	echo "select full_row_id from full_to_atomic_junction where full_row_id=$a;"   | sqlite3 $results_db 
done < "fqid.txt" > fmultqid.txt

while read -r a; 
      do 
	echo "select num_matching_records from atomic_queries where aqid=$a limit 1;"   | sqlite3 $results_db
done < "aqid.txt" > acount.txt

while read -r a; 
      do 
	echo "update full_queries set p1_or_sum_records_matching_each_term = 0 where qid = $a;"   | sqlite3 $results_db
done < "fqid.txt"


while read -r a && read -r b <&3; 
      do 
	echo "update full_queries set p1_or_sum_records_matching_each_term = $a + p1_or_sum_records_matching_each_term where qid=$b;"   | sqlite3 $results_db
done < "acount.txt" 3<"fmultqid.txt" 

rm fqid.txt aqid.txt fmultqid.txt acount.txt


#fixing p9_matching_record_counts
echo "Select qid from full_queries where sub_category='eq' and category = 'P9';" | sqlite3 $results_db > fqid.txt

while read -r a; 
      do 
	echo "select num_matching_records from full_queries where qid=$a;"   | sqlite3 $results_db
done < "fqid.txt" > fcount.txt

while read -r a; 
      do 
	echo "select p9_matching_record_counts from full_queries where qid=$a;"   | sqlite3 $results_db
done < "fqid.txt" > fmatch.txt

while read -r a && read -r b <&3 && read -r c <&4; 
      do
	mod=${c//[|]/a}
	if [[ "$mod" != *a* ]];then
	 match_count=$b
	else
	 slash=$'\174' 
	 match_count=$b$slash${c#*$slash}
	fi
	echo "update full_queries set p9_matching_record_counts = '$match_count' where qid=$a;"  | sqlite3 $results_db
done < "fqid.txt" 3<"fcount.txt" 4<"fmatch.txt"

rm fqid.txt fmatch.txt fcount.txt

