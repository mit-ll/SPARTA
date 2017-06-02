[Back to top-level README](../../README.md)

Database Generation User Manual
===============================================================================
This covers the usage of the script `scripts-config/ta1/scripts/fill_ta1_db.sh`. 

This script does the following:
- generates rows and inserts them into a MariaDB database
- optionally generates queries alongside the MariaDB database, and inserts these into a sqlite results database
- creates indices and views on the MariaDB database
- populates row hash information in the results database (required for post-test analysis)
 
For those wishing to simply generate line-raw files with the data generator (e.g., generate raw row information without inserting it into a MariaDB database), please refer to the [pre_test_generation.py Documentation](../tools-docs/pre_test_generation.md) for details. 

User Manual
===============================================================================

**1)** Run through the [Installation Instructions](../INSTALL.md). If you deviated from any of the default setup, please keep those in mind as you proceed.

**2)** Run `fill_ta1_db.sh` only from the following directory:
```
cd scripts-config/ta1/scripts
```

**3)** View command line help for `fill_ta1_db.sh`:
```
./fill_ta1_db.sh --help
```

**`NOTE`** It is recommended to conduct all the following within a `screen` or `tmux` session, so you can disconnect from/share/restart sessions without losing progress.

**`NOTE`** From here on, sample command line entries use some default/placeholder values for example purposes. You should replace these with values that make sense for your task.

**4)** If necessary, drop MariaDB databases with the same name of your current generation task (be very careful that you're not dropping something that you don't want to drop):
```
mysql -u <USER> -p<PASSWORD> -e 'drop database <DATABASE_NAME>'
```

**5)** If necessary, remove/backup files from previous runs if you are also generating queries (typically a `.db` Sqlite3 database file containing query information, and a `.txt` file containing plaintext queries. In general, if `fill_ta1_db.sh` was run with default parameters, this can be done as follows:
```
mv ~/spar-testing/results/results_databases/<DATABASE_NAME>.db 
   ~/spar-testing/results/results_databases/<DATABASE_NAME>.db.bkp
mv ~/spar-testing/tests/queries/<DATABASE_NAME>.txt 
   ~/spar-testing/tests/queries/<DATABASE_NAME>.txt.bkp
```

**6)** Update the database schemas in `scripts-config/ta1/config/database_schemas` as needed. Find or create a schema that is relevant to your task. Some notes on the default schemas provided in this repository are below.

The `100kBpr_index_all_notes_with_hashes.csv` and `100Bpr_with_hashes.csv` generally represent the SPAR schemas that were used during formal assessment. The 100Bpr (100 bytes/row) version represents a "skinny" database that only includes fields relevant to the anonymized US Census Data that is used to generate these databases. The 100kBpr (100 kilobytes/row) version represents a "wide" database that also includes textual "notes" fields as well as a binary "fingerprint" field. 

The "notes" fields in the 100kBpr schemas can optionally be indexed to support keyword and stemming queries. If you want these query types to be supported, you must enable indexing on these "notes" fields in your schema (set the last field for those columns to `true`). However, this indexing can take quite a long time, so if you do not intend on supporting these types of queries on your "notes" fields, you may set those columns to `false`.

**7)** Execute `fill_ta1_db.sh` with your desired parameters within a `script` command to save the script's output for your records/debugging purposes. 

**`NOTE`** You must have already downloaded the training data via the installation instructions; you will need to point the `--data-dir` flag for `fill_ta1_db.sh` to your training data directory.

**`KNOWN ISSUE`** In general, to generate databases on the order of several thousand rows with a 100kBpr schema, you will need at least 4 GB of RAM to generate your database (and likely even more if you are also generating queries); otherwise, you will likely encounter a FATAL "out of resources" error midway through database generation, and the script currently does not elegantly fail or notify the operator in every scenario this can happen. Users are advised to review the output of the script and look for FATAL errors to assure nothing has gone wrong. Note that to generate our 10TB database with over a thousand queries, we needed a machine with 96 GB of RAM.

The following is an example invocation:
```
script -c './fill_ta1_db.sh -d 1krows_100kBpr --num-rows 1000 
                                              --row-width 100000 
                                              --num-processes 4 
                                              --generate-queries 
                                              --query-schema ../config/query_schemas/test.csv'
                                              --database-schema ../config/database_schemas/100kBpr_index_all_notes_with_hashes.csv'
                                              --generate-hashes
```

Some notes on the above command parameters:
- `--num-processes`
    - Dictates how many threads will be dedicated to data generation. This is 1 by default, and will have the least likelihood of causing issues, but will have the slowest run-time. We typically run this with the same number of CPU cores of the system running the script.
- `--generate-queries`
    - If not specified, only rows will be generated and inserted into MariaDB; otherwise, queries will also be populated, which significantly increases the run-time and memory requirements of the script.
- `--query-schema`     
    - If `--generate-queries` is specified, a schema file must be provided to specify what types of queries will be generated. Please refer to [pre_test_generation.py Documentation](../tools-docs/pre_test_generation.md) for more information on how to define a query schema. Some sample schemas can be found in `scripts-config/ta1/config/query_schemas`.
- `--generate-hashes`     
    - In order to validate when a database system returns the expected row content for a particular test query, we generate hashes of the contents of each row to make this validation simpler. You must include this flag if you want to generate a database of row hashes (which is required for some post-test analysis if you want to perform this validation), and you must also use a `--database-schema` that specifies a table and set of rows to store these hash values as well. Some of the example database schemas accommodate this (they are named with the `_with_hashes.csv` suffix.

If for any reason `fill_ta1_db.sh` hangs, you may `Ctrl-C` the process if you are sure generation has stalled or already completed. 

**8)** You can check whether the number of rows you've generated has been inserted into your database by performing:
```
mysql -u root -p -D 1krows_100kBpr -e 'select count(*) from base'

# If you used a 100kBpr schema, you should also check the notes and fingerprint 
# fields
mysql -u root -p -D 1krows_100kBpr -e 'select count(*) from notes'
mysql -u root -p -D 1krows_100kBpr -e 'select count(*) from fingerprint'
```
**`KNOWN ISSUE`** `fill_ta1_db.sh` has commented out code that generates database modification tests (i.e., involving INSERT, UPDATE, and DELETE commands in addition to SELECT commands). You may uncomment these to try and run this automatically after database and query generation completes, but note that it has been commented out since it 1) takes a long time to run (it re-runs our machine learning code, which is redundant with the machine learning done to generate the database), and 2) has had stability issues in the past (tends to hang before successfully generating the test scripts).

Wrap-up
===============================================================================
If all went well, you should now have the following data available:
- Populated and indexed MariaDB database with the name provided via `-d` or `--database`
- If queries were generated, an Sqlite3 database with query information in the `results_databases/` directory under the path specified by `--results-dir` (`~/spar-testing/results/` by default). 
    - See the [TA1 Results Database Documentation](../tools-docs/ta1-results-database.md) for more information on what's inside this database. Basically, information on the queries generated lives here, and is used for later analysis. You may query this database yourself if you'd like to see more information on the generated queries. Refer to online documentation for Sqlite syntax.
- If queries were generated, a `.txt` file in the `queries/` directory under the path specified by `--tests-dir` (`~/spar-testing/tests/` by default). This is simply a list all the generated queries, with a unique identifier on each line before the SQL syntax.
- If queries were generated, there will be populated directories under the path specified by `--tests-dir` corresponding to different sets of test scripts that were supported by each performer on the SPAR project. Each performer directory will have separate directories for each database that test scripts have been generated for. Please refer to the [Database Test Execution Guide](DB_TEST_EXECUTION.md) for details.

Troubleshooting
=============================================================================

Below are some more detailed notes on the operation of the fill_ta1_db.sh script for troubleshooting purposes:

The script first creates a database with the appropriate schema. 

Then, a Python application is launched that will learn various distributions from `--data-dir` and begins generating rows based on these distributions. If `--generate-queries` was specified, this Python application is also aggregating statistics to determine answers for each of the generated queries.

Meanwhile, a C++ application is running in the background to insert these rows into MariaDB. Both applications should exit after generation/insertion is complete. Note that this may take a very long time (on the order of days for larger DBs).

When both applications have exited, indices and views are created over the newly generate database. 

Then, if `--generate-queries` and `--generate-hashes` were specified, some hashing of each row is performed to expedite query correctness checking in later analysis.

Finally, test scripts are generated if `--generate-queries` was specified.

If you want the initial machine learning process to go faster, you may make a copy of your `--data-dir` and delete some of the files in the PUMS directory. You must then specify the `--allow-missing-files` flag, and must also update the `--data-dir` option to point to your pruned version of the data directory.

If you are still having trouble generating data, try a fewer number of processes and smaller databases with fewer rows. Also try reducing the number of rows/fields specified in your database, and the number/types of queries in your query schema.

[Back to top-level README](../../README.md)
