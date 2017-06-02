SPARTA Framework
===============================================================================

Copyright (c) 2015, Massachusetts Institute of Technology
[BSD License Information](LICENSE.md)

Developed as a part of MIT Lincoln Laboratory’s test and evaluation role in the [SPAR (Security and Privacy Assurance Research) program](http://www.iarpa.gov/index.php/research-programs/spar), SPARTA (SPAR Testing and Assessment) framework is a set of software applications used to evaluate the functionality and performance of relational database systems (e.g., MySQL/MariaDB) and messaging systems (e.g., ActiveMQ). These utilities were used to evaluate research prototypes for secure and private information retrieval systems as compared to state-of-the-art open source implementations. 

SPARTA includes utilities for test dataset generation (e.g., synthetic SQL databases), test case generation (e.g., SQL queries, publisher/subscriber sets), test execution, system resource monitoring, and test report generation. These utilities can be used to replicate tests executed during SPAR’s test and evaluation, or to evaluate existing relational database and messaging systems. SPARTA can be configured to be a tightly integrated framework that facilitates an entire system evaluation, from the creation of test data to the generation of human-readable test reports. 

SPARTA utilities are useful for general software test and evaluation as well, including data structure libraries for high-performance string I/O, generic synthetic dataset generation capabilities, utilities for remote task execution, and more.

Top-level Documentation
===============================================================================
- [Installation Instructions](docs/INSTALL.md)
- [More Detailed Build Instructions](docs/BUILD.md)
- [Notes for Developers](docs/CONTRIBUTE.md)
- [Key Contributors](docs/ACKNOWLEDGEMENTS.md)

User Manuals
===============================================================================
- [Database Generation](docs/user-manuals/DB_GENERATION.md)
- [Database Test Execution](docs/user-manuals/DB_TEST_EXECUTION.md)
- [Circuit Generation](docs/user-manuals/CIRCUIT_GENERATION.md)
- [Circuit Test Execution](docs/user-manuals/CIRCUIT_TEST_EXECUTION.md)
- [Report Generation](docs/user-manuals/REPORT_GENERATION.md)

In-depth Tool Documentation
===============================================================================
- [pre_test_generation.py](docs/tool-docs/pre_test_generation.md)
- [Performance Monitoring](docs/tool-docs/perf_monitoring.md)
- [remote_runner.py](docs/tool-docs/remote_runner.md)
- [ta1-test-harness](docs/tool-docs/ta1-test-harness.md) (database test harness)
- [TA1 Results Database](docs/tool-docs/ta1-results-database.md) (database for database test results)
- [TA2 Results Database](docs/tool-docs/ta2-results-database.md) (database for circuit test results)
