[Back to top-level README](../../README.md)

Report Generation User Manual
===============================================================================
This covers the usage of `spar_python/report_generation/generate_report.py` as it pertains to generating "TA1" reports (i.e., database test result reports) and "TA2" reports (i.e., circuit evaluation test result reports).

The report generator generally does the following:
- Reads data from an SQLite results database
- Computes aggregate statistics and pretty graphs on test results
- Pushes some of aggregate statistics back into the SQLite database for future reference
- Creates LaTeX files to produce PDF reports

Prerequisites
===============================================================================
The following must be done prior to proceeding:

- Execute all relevant steps in [Installation Instructions](../INSTALL.md) (including the setup of MariaDB).
    - If you don't want to do an entire install, you can just ensure that the Jinja2 and SciPy Python modules are installed.
- Either have a...
    - SQLite results database that was produced by following the instructions in [Database Test Execution](DB_TEST_EXECUTION.md). By default, these are located in `~/spar-testing/results/results_databases/`. Note that you should have two different sets of "performer" data in the SQLite database. When executing tests, you had the option of labeling each invocation of `exec_ta1_test.sh` with a certain "performer" label. This label is used to differentiate between what the "baseline" technology is that will used to assess the performance of your "research prototype." For example, you could have run one set of tests against MariaDB and labeled those results "MDB", and then another set of tests against Postgres and labeled those results "POS". 
    - SQLite results database that was produced by following the instructions in [Circuit Test Execution](CIRCUIT_TEST_EXECUTION.md). You should have used different choices for the `-p` flag during different versions of these tests so you acquired a "baseline" set of results and a different "performer" set of results.

User Manual
===============================================================================
You can generate a report by running the following from the `spar_python/report_generation` directory:
```
python generate_report.py -c <CONFIG_FILE> -d <DESTINATION>
```

`<CONFIG_FILE>` should be the location of a configuration file (without the `.py` extension). Look at `a_*_ta1_config.py` and `a_ta2_config.py` as examples. Please refer to `ta1/ta1_config.py` and `ta2/ta2_config.py` files to learn about the details of all the parameters that can be provided in a configuration file. Since configuration files tend to be very specific to particular types of tests, we do not recommend using the existing configuration files as is. Please make a copy and tailor them to your own project.

`<DESTINATION>` should be the name of the location where you would like the generated report to reside (without the `.pdf` extension). By default, the file name will be determined based on the TA number (i.e., if a TA1 configuration file was used for database testing, or if a TA2 configuration file was used for circuit testing), and the file will be generated in the current directory.

``*WARNING*`` The report generator for TA2 does not robustly handle FAILED test results, and will typically crash on an error like "cannot convert str to float." If this happens, you'll need to do some manual SQLite3 queries on the results database (e.g., `SELECT * FROM performer_circuit_ingestation WHERE status = 'FAILED'`) to determine what test logs are being problematic. You will then need to manually delete rows from the results database and/or sanitize or remove the logs in question and/or re-parse logs via the instructions in [Circuit Test Execution](CIRCUIT_TEST_EXECUTION.md).

Note that all of the following parameters are set in the configuration files, but specifying them on the command line when invoking `generate_report.py` will override the configuration file specifications.
```
-i <IMGDIR>
-r <RESULTSDBPATH>
-p <PERFORMERNAME>
-performerprototype <PERFORMERPROTOTYPE>
-b <BASELINENAME>
-m <MONITORIMGDIR>
```

`<IMGDIR>` should be the path to the directory where images for the report should be stored. Users should be careful to not have images for multiple reports stored in the same directory, because there is a risk that they will override one another.

`<RESULTSDBPATH>` should be the path to the location of the results database used. Refer to the [TA2 Results Database Documentation](../tools-docs/ta2-results-database.md) to learn more about results databases.

`<PERFORMERNAME>` should be a string representing the name of the performer or category of test scripts that you ran. It needs to match the values stored in the results database; these are determined by the values used during test execution. See [Database Test Execution](DB_TEST_EXECUTION.md) for more details.

`<PERFORMERPROTOTYPE>` should be a string representing the name of the research prototype under evaluation.

`<BASELINENAME>` should be a string representing the name of the baseline technology used to evaluate the research prototype. It needs to match the values stored in the results database; again, see [Database Test Execution](DB_TEST_EXECUTION.md) for more details.

`<MONITORIMGDIR>` should be the path to the location of the performer monitoring images (note this is generaly not a documented feature in this release, but you are free to explore the code in `spar_python/perf_monitoring`).

[Back to top-level README](../../README.md)
