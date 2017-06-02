[Back to top-level README](../../README.md)

TA1 (Database Testing) Results Database
===============================================================================
We store the test results in a sqlite3 database. Sqlite3 is a light-weight database that can be relocated with a simple move or copy/paste operation. We interface with the results database through the Ta1ResultsDB class in `spar_python/report_generation/ta1/ta1_database.py`, which has a few handy methods.

The results database has 9 tables, which are described below.

## `full_to_full_junction`

This table gives all of the (qid, qid) pairs where the first qid corresponds to a P1-dnf (conjunction of disjunctions) query, and the second qid corresponds to a P1-and (conjunction) query which serves as one of its clauses.
- composite_full_query (int) : the query id of the P1-dnf query in question
- base_full_query (int) : the query id of the P1-and query in question

## `full_to_atomic_junction`

This table gives all of the (qid, aqid) pairs where the qid corresponds to a composite query (a query of type P1, P8 or P9) that was run, and the aqid corresponds to one of the atomic queries it consists of.
- full_row_id (int) : the query id of the composite query in question
- atomic_row_id (int) : the query id of the atomic query in question

## `mod_to_full_junction`

This table allows us to correlate a modification with the queries whose results it affects.
- mod (int) : the modification id of the modification in question
- full_query (int) : the query id of the query in question
- pre (text) : a pipe-delimited list of all records that match the query before the modification but not afterwards
- post (text) : a pipe-delimited list of all records that match the query after the modification but not before

## `atomic_queries`

This table stores information about each atomic (i.e. not type P1, P8 or P9) query. This information is specific to a query, not to its execution; e.g. this table contains the number of matching records, but not the associated timing information, etc.
- aqid (int) : the atomic query id of the query in question
- category (text) : the query category (e.g. Eq, P2, P3, P4, P6, P7, P11)
- sub_category (text) : the query subcategory (e.g. 'initial' if the category is P6)
- sub_sub_category (text) : the query subsubcategory (this will usually be a number.)
- db_num_records (int) : the number of records in the database for which this query was generated
- db_record_size (int) : the average size of records in the database for which this query was generated (in bytes)
- where_clause (text) : the text of the query after the word "WHERE (e.g. if the query was "SELECT id FROM main WHERE name='alice'", then the where_clause would be "fname='alice'".)
- num_matching_records (int) : the number of records matching the query in the database for which it was generated
- field (text) : the field over which the query is searching (e.g. if the query was "SELECT id FROM main WHERE fname='alice'", then the field would be 'fname'.)
- field_type (text) : the type of the field over which the query is searching (e.g. if the query was "SELECT id FROM main WHERE fname='alice'", then the field_type would be 'string'.)
- keyword_len (int) : the number of characters in the search term of the query (e.g. if the query was "SELECT id FROM main WHERE CONTAINED_IN(notes1, alice)", then the keyword_len would be 5.)
- range (int) : for P2 queries, this is the number of possible elements matching the query

## `full_queries`

This table stores information about each query (not just atomic queries, like the 'atomic_queries' table). This information is specific to a query, not to its execution; e.g. this table contains the number of matching records, but not the associated timing information, etc.
- qid (int) : the query id of the query in question
- category (text) : the query category (e.g. Eq, P1, P2, P3, P4, P6, P7, P8, P9, P11)
- sub_category (text) : the query subcategory (e.g. 'initial' if the category is P6)
- sub_sub_category (text) : the query subsubcategory (This will usually be a number. Please see the query plan for details.)
- db_num_records (int) : the number of records in the database for which this query was generated
- db_record_size (int) : the average size of records in the database for which this query was generated (in bytes)
- where_clause (text) : the text of the query after the word "WHERE (e.g. if the query was "SELECT id FROM main WHERE name='alice'", then the where_clause would be "fname='alice'".)
- p8_m (int) : the m value of the P8 threshold (m-of-n) query. Note that since P9 queries have a similar structure, this field will be populated for P9 queries as well.
- p8_n (int) : the n value of the P8 threshold (m-of-n) query. Note that since P9 queries have a similar structure, this field will be populated for P9 queries as well.
- p9_matching_record_counts (text) : for P9 queries, a pipe-delimited list of integers. Each integer represents a number of identically-ranked results, the first integer representing the results ranked highest, and the last integer representing the results ranked lowest.
- num_matching_records (int) : the number of records matching the query
- matching_record_ids (text) : a pipe-delimited list of matching record ids
- matching_record_hashes (text) : a pipe-delimited list of matching record hashes (wherein each hash corresponds to the record whose id is at the same index in matching_record_ids)
- p1_and_num_records_matching_first_term (int) : for P1-and queries, an integer indicating the number of records matching the first term of the conjunction.
- p1_negated_term (text) : for P1-negation queries, a pipe-delimited list of indices of negated clauses.
- p1_num_terms_per_clause (int) : for P1-dnf and P1-cnf queries, the number of terms in each clause of the boolean expression.
- p1_num_clauses (int) : for P1-dnf and P1-cnf queries, the number of clauses in the boolean expression.
- rejecting_policies (text) : a pipe-delimited list of policy identifies that reject the query in question.

## `performer_queries`

This table stores information about query executions. Each time a query is executed by a performer or the baseline, timing and results information is stored in this table.
- qid (int) : the query id of the query in question
- performer (text) : the name of the performer (or baseline)
- test_case_id (text) : the id of the test case
- selection_cols (text) : either "*" or "id"
- send_time (real) : a time stamp corresponding to the sending of the query
- results_time (real) : a time stamp corresponding to the receipt of the results
- query_latency (real) : results_time - send_time
- encryption_start_time (real) : N/A
- encryption_end_time (real) : N/A
- encryption_latency (real) : N/A
- decryption_start_time (real) : N/A
- decryption_end_time (real) : N/A
- decryption_latency (real) : N/A
- returned_record_ids (text) : a pipe-delimited list of the record ids returned
- returned_record_hashes (text) : a pipe-delimited list of the record hashes returned (if the query had selection_cols="*")
- mid : a pipe-delimited list of mids corresponding to modifications which were in effect when the query was executed
- num_threads (int) : N/A
- status (text) : if the query failed, the returned FAILED message
- current_policies (text) : a pipe-delimited list of policies in effect when the query was executed
- correctness (bool) : (populated during report generation): a boolean indicating whether or not the correct results were returned

## `mods`

This table stores information about each modification. This information is specific to a modification, not to its execution.
- mid (int) : the modification id of the modification in question
- category (text) : either 'delete', 'insert', or 'update'
- db_num_records (int) : the number of records in the database for which this modification was generated
- db_record_size (int) : the average size of records in the database for which this modification was generated (in bytes)
- record_id (int) : the id of the record which the modification in question targets

## `performer_mods`

This table stores information about modification executions. Each time a modification is executed by a performer or the baseline, timing information is stored in this table.
- performer (text) : the name of the performer (or baseline)
- test_case_id (text) : the id of the test case
- mid (int) : the modification id of the modification in question
- send_time (real) : a time stamp corresponding to the sending of the modification
- results_time (real) : a time stamp corresponding to the receipt of of a DONE message
- mod_latency (real) : results_time - send_time
- encryption_start_time (real) : N/A
- encryption_end_time (real) : N/A
- encryption_latency (real) : N/A
- status (text) : if the modification failed, the returned FAILED message
- correctness (bool) (populated during report generation): a boolean indicating whether or not the modification was correct

## `performer_verifications`

This table stores information about verification executions. Each time a verification is executed by a performer, timing information is stored in this table.

- performer : the name of the performer (or baseline)
- test_case_id : the id of the test case
- record_id : the id of the record which the verification in question targets
- verification : a boolean indicating what the verification returned
- send_time : a time stamp corresponding to the sending of the verification
- results_time : a time stamp corresponding to the receipt of of a DONE message
- verification_latency : results_time - send_time
- status : if the verification failed, the returned FAILED message
- correctness (bool) (populated during report generation): a boolean indicating whether or not the verification was correct

[Back to top-level README](../../README.md)
