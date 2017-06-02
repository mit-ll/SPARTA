This is where all SPAR Python code should go. All directories should contain an __init__.py file (even an empty one) so we have proper packages and modules.

Note that currently there is some Python code scattered about in other locations. All of that code will eventually be moved under spar_python, restructured for better code re-use, and improved to comply with the style guide.

====

Failing unit tests

server parse method...not sure what's up with this, looks like unit test was not updated for new log format
fill_matching_record_hashes needs a fake MariaDB database for unit test
remote_runner looks like we need special kill functionality for locally spawned tasks
xml query generation sometimes fails...fairly rare that it does

====

Issues

need to have remote runner tests not generate files in root directory...
