#!/bin/bash

# Switch to the sparta virtualenv
source $WORKON_HOME/sparta/bin/activate

python stealth_generate.py phase1_tests/01_one_of_each_small/F=1 
python stealth_generate.py phase1_tests/01_one_of_each_small/F=2 
python stealth_generate.py phase1_tests/01_one_of_each_small/F=3
python stealth_generate.py phase1_tests/02_one_of_each_medium/F=1 
python stealth_generate.py phase1_tests/02_one_of_each_medium/F=2 
python stealth_generate.py phase1_tests/02_one_of_each_medium/F=3
python stealth_generate.py phase1_tests/03_one_of_each_large/F=1 
python stealth_generate.py phase1_tests/03_one_of_each_large/F=2 
python stealth_generate.py phase1_tests/03_one_of_each_large/F=3
python stealth_generate.py phase1_tests/04_single_gate_type
python stealth_generate.py phase1_tests/05_varying_param/F=1 
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=10/fx=.0000001 
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=10/fx=.25
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=100/fx=.0000001 
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=100/fx=.25
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=500/fx=.0000001 
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=500/fx=.25
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=1000/fx=.0000001 
python stealth_generate.py phase1_tests/05_varying_param/F=2/X=1000/fx=.25
python stealth_generate.py phase1_tests/05_varying_param/F=3
python stealth_generate.py phase1_tests/06_large/F=1 
python stealth_generate.py phase1_tests/06_large/F=2 
python stealth_generate.py phase1_tests/06_large/F=3
python stealth_generate.py phase1_tests/07_one_of_each_very_large
python stealth_generate.py phase1_tests/08_very_large

# Exit the virtualenv
deactivate
