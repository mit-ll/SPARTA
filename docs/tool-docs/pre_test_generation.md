[Back to top-level README](../../README.md)

pre_test_generation.py
===============================================================================
Combined, the test suite system generates three corpora of data: random database of entries of fictitious people, corresponding SQL queries, and ground truth answers to those queries. The system consists of two distinct systems: the data-generation system, and query-generation system. 

SPARTA's data-generation system uses anonymized demographic information from the United States Census Bureau and other sources to generate unlimited amounts of synthetic, random database entries about fictitious people. It does so spawning off workers to generate rows in batches. In addition to simply generating rows, there is also a map-reduce framework with pluggable aggregators over the generated rows - this allows for (fairly) easy extensibility of the functionality of the data generator. 

Query generation is an extension of data-generation: generating queries according to user-specification, and computing the ground-truth results of those queries over the generated data. The desired queries are specified in an external 'query-schema' file. During data-generation, these query-specifications are matched against the underlying distribution of the source-data. Matching queries are generated and matched against data during generation (using the map-reduce mechanism). 

Though they are distinct systems, both systems have heavy dependencies on one another. Due to this, the query-generator and data-generator are run from the same interface - `pre_test_generation.py`

Ideal use cases for this system is for benchmarking and evaluating database software (secure or not). For example, data generation is capable of generating the contents of a database. Query generation will generate queries for that database, as well as the answers to any queries generated. 

Installation
===============================================================================
## Dependencies
The data/query generator assumes that the [Installation Instructions](../INSTALL.md) have been followed. 

## Build
The data/query generator is written almost entirely in pure Python; however, for efficiency reasons portions of it were written in Cython. Those classes must be compiled by running SCons within an environment with the relevant dependencies installed. Refer to the [Installation Instructions](../INSTALL.md) and [Build Guide](../BUILD.md) for more details. Generally, you should be able to build `pre_test_generation.py` by using the `sparta` virtualenv discussed in the [Installation Instructions](../INSTALL.md) and executing `scons --opt install` from the top-level directory.

## Test
See the [Build Guide](../BUILD.md) for more details. Generally, you should be able to run the relevant unit tests by using the `sparta` virtualenv discussed in the [Installation Instructions](../INSTALL.md) and invoking `nosetests` from the `spar_python/query_generation` directory.

A quick note on unit tests, at the top level in `spar_python` it takes approximately 3 minutes to run all 300 or so unit tests. Some of the unit tests (especially in query_generation) are probabilistic in nature so do fail some portion of the time. Generally, if the same test if failing more than 1 time out of 20, then something is actually broken. 

User Manual 
===============================================================================
In order to run the generators you must retrieve the demographic source-data used to train our system. This is an expensive but one-time operation. See the [Installation Instructions](../INSTALL.md) which details how to fetch this training data.

After retrieving this demographic data, synthetic database entries can be generated at any time. To generate 1,000 100 byte rows and write them to a file, you could do something like the following.

1) If necessary, invoke the relevant virtualenv.

2) Navigate to the directory `spar_python/query_generation`.

3) Execute the command:
```
python pre_test_generation.py -d /path/to/data/directory
                              --line-raw-file=/path/to/desired/file
                              --schema-file=../../scripts-config/ta1/config/database_schemas/100Bpr.csv
                              --num-rows=1000 --row_width=100
```


The `-v` flag can be used to produce more verbose output.

To generate large amounts of data, we recommend that you run more than one process. To generate 1,000,000 100 KB rows using 10 processes, for example, one could run the command:
```
python pre_test_generation.py -d /path/to/data/directory
                              --line-raw-file=/path/to/desired/file
                              --schema-file=../../scripts-config/ta1/config/database_schemas/100Bpr.csv
                              --num-rows=1000000 --num-processes=10 --row_width=100
```

This will actually produce 10 files at the specified `--line-raw-file` location, each with a unique suffix to enforce unique filenames. 

## Command Line Options
The options for `pre_test_generation.py` are below:
```
  -h, --help
       Show a short help message and exit.

  -v, --verbose         
       Verbose output

  -d DATA_DIR, --data-dir=DATA_DIR
      Specify the location of the source-data files. Note: this should be the
      directory given to get_data.py, and will be the directory containing the
      directories 'pums', 'names', 'pums', etc.

  --allow-missing-files
      By default, the data-generator will terminate with error if any of the
      expected source-data files are missing. This flag suppresses this
      behavior, allowing data-generation to continue (if possible) on
      incomplete data. Though the generated data will be incorrect, this mode
      of operation may be useful for debugging or testing. (See
      'Test-executions' above.)


  --line-raw-file=LINE_RAW_FILE
      Write LineRaw formatted data between INSERT/ENDINSERT pairs to this
      file.  Requires the presence of the --schema-file flag. Note: in
      multi-processor mode, will generate multiple files with names derived
      from the one specified
  
  --schema-file=SCHEMA_FILE
      Path to the schema file. We recommend against writing your own. Just use
      the one at spar-git/scripts-config/ta1/config. 

   --named-pipes       
      Use named pipes instead of regular files. This will *greatly speed up*
      data-generation, but the resulting 'files' will not be persistent.

  --seed=RANDOM_SEED  
      Random seed for generation. Must be a number, and defaults to 0. Note:
      is converted to an integer via the python int() function before use, and
      so will be rounded down to the next integer. Numbers between 0 and 1,
      therefore, will all collapse to the default. We guarantee that re-use of
      the same seed will result in the same data, even if other options change
      between executions. (We do not guarantee that the data will be allocated
      to the processes or files, just that the final set of entries will be
      the same.)

   --num-processes=NUM_PROCESSES
      The number of processes to spawn when parallelization is desired. We
      suggest that you experiment with this parameter to maximize efficiency.

   --num-rows=NUM_ROWS
      The number of rows (fictitious people) to create.

   --row_width=ROW_WIDTH
      The average width of rows in the database, given in bytes

   --generate-queries  
      Toggle switch to generate queries on this run of data generation.
      Defaults to false. This flag must be present if any of the other query
      specific flags are used. 

   --query-generation-seed=QUERY_SEED
      The seed for query generation. Defaults to 0. Note: is converted to an
      integer via the python int() function before use, and so will be rounded
      down to the next Integer. Numbers between 0 and 1, therefore, will all
      collapse to the default. We guarantee that re-use of the same seed will
      result in the same queries, if all other options remain constant.
      (NOTE: This includes the same training data and the EXACT same query
      schema file.)  
                   
   --query-schema-file=Q_SCHEMA_FILE
      Path to the schema file for queries, this is used to determine which
      queries need to be generated. Expanded instructions for the query schema
      file are included below. This file should be in .csv format. Example
      schema can be found in spar_python/query_generation/test_schemas    
   
   --result-database-file=RESULT_DATABASE_FILE
      Path to the file where the ground truth database will be written to.
      This generated file is in MySQL format and is used in the generation of
      the final pdf report. After query generation is run, the following
      fields in the results/ground truth database are populated:
   	 * Atomic: aqid, category, sub_catagory, db_num_records, db_record_size,
   	   where_clause, num_matching_records, field, field_type, keyword_len
   	   range
   	 * Full: qid, category, sub_category, db_num_records, db_record_size,
   	   where_clause, num_matching_records, matching_record, ids, 
   	   matching_record_hashes
   	 * Full to atomic: atomic_row_id, full_row_id
   
   --list-of-queries-file=LIST_OF_QUERIES_FILE
      Path to the file which will be generated containing the list of queries
      generated. They will be in the format ingestible by the test harness:
         (qid) SELECT * FROM main WHERE (where_clause)
```

Before each new run of data/query generation, the files indicated by `Q_SCHEMA_FILE` and `RESULT_DATABASE_FILE` above must not previously exist. 

## Invocation Examples
What it looks like on the command line when executing from `spar_python/query_generation` without queries; 10,000 rows with a row-width of 100 bytes:
```
python pre_test_generation.py -d /path/to/data/directory
                              --line-raw-file=/path/to/desired/file
                              --schema-file=../../scripts-config/ta1/config/database_schemas/100Bpr.csv
                              --num-rows=10000 --row-width=100 --seed=14
```

What it looks like on the command line when executing from `spar_python/query_generation` and generating queries; 10,000 rows with a row-width of 100 bytes.
```
python pre_test_generation.py -d /path/to/data/directory
                              --line-raw-file=/path/to/desired/file
                              --schema-file=../../scripts-config/ta1/config/database_schemas/100Bpr.csv
                              --num-rows=10000 --generate-queries 
                              --query-schema=/path/to/query/schema/file
                              --result-database-file=resultsdb.db
                              --list-of-queries=queries.txt
                              --row-width=100 --query-generation-seed=12 --seed=14
```

## Query Schema File

Included in the repository are several example query_schema files for each type  of supported query (located in `spar_python/query_generation/test_schemas`). The basic structure for the schemas are:
```
*
cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper']",
EQ,eq,"['LL','COL','IBM1']","['fname','lname']","[10,1,10]","[5,11,100]"
...(more query specifications)
*
cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']"
P1,eq-and,"['LL','COL','IBM1']","['ALL']","[1,1,10,2,1,10]","[1,11,100,2,11,100]"
...(more query specifications)
```

### Field Definitions
The `*` indicates that the next row is a definition of the fields needed for a particular query type (details on each particular query type are outlined below). The only field that should change across query types is what is contained in the `other_columns` list (the comma-separated list within brackets in the second line of the example shown above).

For the `cat` column in the field definition, the current valid values are:
```
EQ, P1, P2, P3, P4, P6, P7, P8, P9, P11  
```

Valid values for the `sub_cat` column in the field definition are outlined within the specific query type sections below.

`perf` is the list of performers that support each set of queries. The list of eligible values for performer is `LL`, `COL`, `IBM1`, and `IBM2`.

Valid values for the `fields` column in the field definition are generally the below (but may be restricted for different query types, as discussed later in this document):
* `fname`
* `lname`
* `ssn`
* `zip`
* `city`
* `address`
* `state`
* `sex`
* `age`
* `race`
* `marital_status`
* `school_enrolled`
* `education`
* `dob`
* `citizenship`
* `income`
* `military_service`
* `language`
* `hours_worked_per_week`
* `weeks_worked_per_year`
* `foo`
* `last_updated`
* `notes1`
* `notes2`
* `notes3`
* `notes4`

There can be as many fields specified in `fields` as are supported within the list of fields (as shown above with the listing of `fname` and `lname`, but one could also include in that list `ssn`, `foo`, `address`, etc.). 

The final field is referred to as `other_columns`; it is a comma-separated enclosed in brackets that represent fields that are only relevant for the query type specified by `cat` and/or `sub_cat`. In the above example, this includes `no_queries`, `r_lower`, and `r_upper` for `EQ` queries. 

In summary, for the above example, there will be a total of 15 `EQ` queries generated, 10 of which return between 1 and 10 records and 5 of which return between 11 and 100 records. If one appended `[5,101,1000]` to the `EQ` line, there would be an additional 5 queries generated that all return between 101 and 1000 records. 

``*WARNING*`` It is important not to set result set sizes larger than there are rows in the database you are testing. A checker module will point out the line in question and exit query generation. 

After the field definition line, one or more lines may specify requests to generate queries of that query type until another `*` is hit or the end of the file is reached. It is important to have no blank lines in the schema.

Each line that is not a `*` or field definition represents a set of queries to be generated. 

``*NOTE*`` It tends to be easiest to create schema files within an editor like Excel rather than a simple text editor. 
The process of learning the distributions, generating queries, and generating data will not happen unless provided a correctly formatted query schema file. The checker module will halt with  an error and the line of the error should the schema file be incorrectly formatted. 

Finally, note that though one may request 10 equality queries, 10 equality queries may not be output. The program will first generate the requested number of queries that it believes meets the requested number of records returned, but will usually end up eliminating some queries that do not actually match the requested number of records returned. That being said, it is usually worth requesting more queries than you actually need. 

### Query Type Details
The details of the schema for each of the supported types are below.

#### EQ
```
Example query:

    43 SELECT * FROM main WHERE fname = 'LISA'
    
Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper']",
    EQ,eq,"['LL','COL','IBM1']","['fname','lname']","[10,1,10]","[5,11,100]","[5,101,1000]",

Other_columns: (order must be maintained)
    *'no_queries' - the number of queries that return the specified result set
     sizes
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
    *'r_upper' - the upper end of the range of result set size

Valid sub_cats:
    *'eq'
    
Valid fields:
    *'fname'		*'city'
    *'lname'		*'zip'
    *'ssn'			*'income'
    *'address'      *'foo'
    *'dob'          *'last_updated'
```

#### P1
```
Example queries:

    71 SELECT * FROM main WHERE dob = '1923-06-30' AND fname = 'ADAM' AND sex = 'Male'
    80 SELECT * FROM main WHERE military_service = 'Previous_Active_Duty' OR dob = '1972-06-16'


Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']",,,,,
    P1,eq-and,"['LL','COL','IBM1']",['ALL'],"[1,1,10,2,1,10]","[1,11,100,2,11,100]",,,,
    P1,eq-or,"['LL','COL','IBM1']",['ALL'],"[1,1,10,2,1,10]","[1,11,100,2,11,100]",,,,

Other_columns: (order must be maintained)
    
    *'no_queries' - the number of queries that return the specified result set
     sizes for each value with that specified range. This is best illustrated
     through an example. Take the set no_queries = 1, r_exp_lower = 2, and
     r_exp_upper = 10. This would generate 1 query for every range exponent in
     the range 2 to 10 (for a total of 9). Each of which would return generally
     the same number of records.
         
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
      
    *'r_upper' - the upper end of the range of result set size
    
    *'num_clauses' - the number of clauses in the query
    
    *'tm_lower'/'tm_upper' - for 'and-eq' it is the upper and lower ranges of
     first term matches number of records, for 'eq-or' it is the total sum of
     records that each individual clause returns

Valid sub_cats:
    *'eq-and' - simple equality conjunctions
    *'eq-or' - simple equality distjunctions
    
Valid fields:
    *'ALL' - this denotes that all fields are eligible, performer limitations
     are hardcoded
```

#### P2 (non-foo fields)
```	
Example queries:

    600 SELECT * FROM main WHERE ssn >= '899770662'
    601 SELECT * FROM main WHERE ssn >= '899428230'

Example of a csv file:
    *,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','type']",,
    P2,range,"['LL','COL','IBM1']","['ssn']","[10,1,10,'less']",,,

Other_columns: (order must be maintained)
    
    *'no_queries' - the number of queries that return the specified result set
     sizes 
         
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
      
    *'r_upper' - the upper end of the range of result set size
    
    *'type' - These correspond to the sub_categories listed below:
        ~'range' - Corresponds to range, indicates a two-side range query
        ~'greater' - Corresponds to greater than, indicates a single sided
                     greater than query
        ~'less' - Corresponds to less than, indicates a single sided less than
                  query

Valid sub_cats:
    *'range'
    
Valid fields:
    *'fname'         *'lname'
    *'zip' 	         *'city'
    *'last_updated'  *'ssn'
    *'income'	
```

#### P2 (field 'foo' specific)
```	
Example queries:

    150 SELECT * FROM main WHERE foo BETWEEN 74 AND 184
    312 SELECT * FROM main WHERE foo >= 4207324304514021946

Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','r_exp_lower','r_exp_upper','type']",,,,,
    P2,foo-range,"['LL','COL','IBM1']",['foo'],"[1,1,10,2,50,'range']",,,,
    P2,foo-greater,"['LL','COL','IBM1']",['foo'],"[1,1,10,2,50,'greater-than']",,,,

Other_columns: (order must be maintained)
    
    *'no_queries' - the number of queries that return the specified result set
     sizes for each value with that specified range. This is best illustrated
     through an example. Take the set no_queries = 1, r_exp_lower = 2, and
     r_exp_upper = 10. This would generate 1 query for every range exponent in
     the range 2 to 10 (for a total of 9). Each of which would return generally
     the same number of records.
         
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
      
    *'r_upper' - the upper end of the range of result set size
    
    *'r_exp_lower' - The lower exponent for the range value. This indicates the
     bit length of the range generated. For greater-than types of queries, this
     is ignored beyond the effects on the aforementioned number of queries
     generated. 
    
    *'r_exp_lower' - The lower exponent for the range value. This indicates the
     bit length of the range generated. For greater-than types of queries, this
     is ignored beyond the effects on the aforementioned number of queries
     generated. 
    
    *'type' - These correspond to the sub_categories listed below:
        ~'range' - Corresponds to foo-range, indicates a two-side range query
        ~'greater-than' - Corresponds to foo-greater, indicates a single sided
         greater than query. 

Valid sub_cats:
    *'foo-range' - two-sided range query
    *'foo-greater' - single sided greater than query
    
Valid fields:
    *'foo'
```
	
#### P3/P4
```
Example queries:

    372 SELECT * FROM main WHERE CONTAINED_IN(notes4, 'characterized')
    377 SELECT * FROM main WHERE CONTAINS_STEM(notes4, 'watching')
    
Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','keyword_len','type']",,,,,
    P3,word,,"['LL','COL','IBM1']"['notes4'],"[5,11,100,10,'word']",,,,,
    P4,stem,,"['LL','COL','IBM1']"['notes4'],"[5,11,100,10,'stem']",,,,,

Other_columns: (order must be maintained)
    *'no_queries' - the number of queries that return the specified result
     set sizes
    *'r_lower' - the lower end of the range of result set size one is 
      interested in (number of records returned by that query)
    *'r_upper' - the upper end of the range of result set size
    *'keyword_len' - the length of keyword to be searched for (for example
      'apple' would have a keyword_len of 5)
    *'type' - Corresponds to the sub_categories listed below, indicates
      which type of query to be generated
        ~'word' - Corresponds to word
        ~'stem' - Corresponds to stem

Valid sub_cats:
    *'word' - Indicates P3 queries
    *'stem' - Indicates P4 queries
    
Valid fields:
    *'notes1'		*'notes3'
    *'notes2'		*'notes4' 
```
	
#### P6
```
Example queries:

    15 SELECT * FROM main WHERE fname LIKE '_ACQUELINE'
    17 SELECT * FROM main WHERE fname LIKE 'JACQUEL_NE'
    24 SELECT * FROM main WHERE fname LIKE 'JACQUELIN_'
    
Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','keyword_len','type']",,,,,
    P6,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'initial-one']",,
    P6,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'middle-one']",,
    P6,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'final-one']",,

Other_columns: (order must be maintained)
    *'no_queries' - the number of queries that return the specified result set
     sizes
    *'r_lower' - the lower end of the range of result set size one is 
      interested in (number of records returned by that query)
    *'r_upper' - the upper end of the range of result set size
    *'keyword_len' - the length of keyword to be searched for (for example
      'app%' would have a keyword_len of 4). It includes any wildcard 
      characters
    *'type' - Indicates which type of query to be generated, corresponds with
     the sub_catagories listed in the query test plan
        ~'initial-one' - replaces one character with _ at beginning of word
        ~'middle-one' - replaces one character with _ in middle of word
        ~'final-one' - replaces one character with _ at end of word

Valid sub_cats:
    *'wildcard'
    
Valid fields:
    *'fname'
    *'lname'
    *'address'
```
	
#### P7
```
Example queries:

    31 SELECT * FROM main WHERE address LIKE '%81 Curve Ln'
    34 SELECT * FROM main WHERE address LIKE '% Vinyard%'
    41 SELECT * FROM main WHERE address LIKE '62 Alfred C%'

Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','keyword_len','type']",,,,,
    P7,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'initial']","[2,11,100,10,'initial']",,,,
    P7,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'both']","[2,11,100,10,'both']",,,,
    P7,wildcard,"['LL','COL','IBM1']","['fname']","[2,1,10,10,'final']","[2,11,100,10,'final']",,,,

Other_columns: (order must be maintained)
    *'no_queries' - the number of queries that return the specified result set
     sizes
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
    *'r_upper' - the upper end of the range of result set size
    *'keyword_len' - the length of keyword to be searched for (for example
     'app%' would have a keyword_len of 4). It includes any wildcard characters
    *'type' - Indicates which type of query to be generated, corresponds with
     the sub_categories listed in the query test plan
        ~'initial' - Queries of the form %stuff
        ~'both' - Queries of the form %stuff%
        ~'final' - Queries of the form stuff%

Valid sub_cats:
    *'wildcard'
    
Valid fields:
    *'fname'      *'notes1'      *'notes4'
    *'lname'      *'notes2'
    *'address'    *'notes3'
```

#### P8/P9
```
Example queries:

38 SELECT * FROM main WHERE M_OF_N(2, 3, dob = '1923-09-05', fname = 'NICK', sex = 'Male')
92 SELECT * FROM main WHERE M_OF_N(2, 3, fname = 'RILEY', fname = 'GERARD', sex = 'Male')
   ORDER BY M_OF_N(2, 3, fname = 'RILEY', fname = 'GERARD', sex = 'Male') DESC

Example of a csv file:
    *,,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries','r_lower','r_upper','m','n','tm_lower','tm_upper']",,,,,
    P8,threshold,"['LL','COL','IBM1']",['ALL'],"[20,1,10,2,3,1,10]","[10,1,10,2,3,11,101]",,


Other_columns: (order must be maintained)
    
    *'no_queries' - the number of queries that return the specified result
     set sizes for each value with that specified range. This is best
     illustrated through an example. Take the set no_queries = 1,
     r_exp_lower = 2, and r_exp_upper = 10. This would generate 1 query for
     every range exponent in the range 2 to 10 (for a total of 9).  Each of
     which would return generally the same number of records.
         
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
      
    *'r_upper' - the upper end of the range of result set size
    
    *'m'/'n' - Matches m clauses out of a total n, in the example above it
     would be 2 and 3 respectively. 
    
    *'tm_lower'/'tm_upper' - the sum of matching records for the first
     n-m+1 clauses

Valid sub_cats:
    *'threshold'
    
Valid fields:
    *'ALL' - this denotes that all fields are eligible, performer
     limitations are hardcoded

Note: P9 queries are the exact same queries run for P8 but with ranking syntax
appended, so generating P8 queries will also always generate P9 queries. 
```

#### P11
```
Example queries:
    22 SELECT * FROM main WHERE xml_value(xml,'//fname', 'DUNCAN')
    47 SELECT * FROM main WHERE xml_value(xml,'/xml/a3/b2/age',39)

Example of a csv file:
    *,,,,,,,,
    cat,sub_cat,perf,fields,"['no_queries', 'r_lower', 'r_upper', 'path_type']",,,,,
    P11,xml,"['LL','COL']",['xml'],"[20,1,10,'short']","[20,11,100,'short']",,,
    P11,xml,"['LL','COL']",['xml'],"[20,1,10,'full']","[20,11,100,'full']",,,

Other_columns: (order must be maintained)
    *'no_queries' - the number of queries that return the specified result set
     sizes
    *'r_lower' - the lower end of the range of result set size one is
     interested in (number of records returned by that query)
    *'r_upper' - the upper end of the range of result set size
    *'path_type' - Indicates which type of path the query contains:
        ~'short' - Queries of the form xml//leaf_node
        ~'full' - Queries of the form xml/node1/node2/leaf_node

Valid sub_cats:
    *'xml'
    
Valid fields:
    *'xml'
```

Known Issues/TODOs
===============================================================================
This section contains a list of tasks that we had in mind to improve the data/query generator before the conclusion of the project prevented us from doing so. 

1. *Change the format of query schema file from CSV.* At the moment the queries are input into the generator in a csv formatted file. This format, while easy to parse, is not easy to edit without a working knowledge of the format. Ideally, it would be possible to change the format of this file to make it easier for the user to specify what queries they wished to generate. 

2. *Create a command line flag to control the maximum size of the fingerprint field.* At the moment the fingerprint field (the random binary field to increase the size of the field from 100 B to 100 kB, rows with the field are 100 kB and rows without are 100 B) is only one size. In order to control what size each row is, we had envisioned adding a command line flag that would specify the size of the fingerprint field to generate. This value would have to be passed through in the generation options to the generator_worker class. 

3. *Refine logging in the data generator.* Currently all logging statements in the data generator go to standard error. It would be ideal if the statements classified as INFO and DEBUG messages went to standard-out while those classified as WARNING and ERROR went to standard error. 

4. *Support NOT query type.* At this point the functionality to negate terms is not present in conjunctions. It does not make sense given the distribution of the fields to negate single terms except on small scale databases - but it would be nice to support them in conjunctions. This could be done pretty simply by extending equality query generator and subtracting the desired query weight from one (essentially taking the inverse) 

5. *Support DNF query type.* DNF format was proposed but not actually implemented. Of all the extended query types here this would probably be the most difficult one. It would be accomplished by extending the functionality of the compound query generator and compound query batch. 

6. *Support other P1 query types.* At this point boolean queries only consist of equality terms. Because all query batches have the same interface it should be fairly easy to extend the compound query generator to support non-equality terms such as wildcards or substrings. 

Making Your Own Aggregators
===============================================================================
Why you'd want to do this - At the moment the only aggregators being run are the query aggregators (if query generation is enabled) and the line-raw aggregators. However, if one wanted to have custom functionality, such as computing aggregate values or creating a custom output format, creating and running one's own aggregator would be a fairly straightforward way of accomplishing this.

How you can do this - Aggregator are all extensions of the `base_aggregator` class which can be found in `spar_python/common/aggregators`. As long as the aggregator one implements extends this base class it should be able to function within the existing framework. To actually run this aggregator one has to make some changes to `pre_test_generation.py` which is found in `spar_python/query_generation`. 

1. Around line 106 in `pre_test_generation.py` one can see that `options.aggregators` is defined as the combination of `queryset_aggregators` and `options.aggregators`. It is important that any new aggregators are placed in the `options.aggregators` (defined around line 201) for maintained functionality.

2. If your aggregator has any results that need to be handled after rows are generated they will be returned as part of agg_results on line 151. The invariant is that the results of the aggregator will be ordered in the same ordering as the initial aggregators. 
