#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Started running at `date`"
echo "Arguments to this script:"
for a in "$@"
do
   echo "Arg: $a"
done

echo "My current directory: " `pwd`
echo "The script is in $SCRIPT_DIR"

echo "The following files exist:"

find .

echo "Done!"
