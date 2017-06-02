The Lincoln baseline consists of two components, a client component and a
server component.  This document contains instructions for running these two
components and using it with the test harness. 

Baseline Operations
=====================================================

The PublishingBroker and SubscribingClient constitute the baseline pub/sub
system. The PublishingBroker consolidates the functionality of a publisher and a
third-party broker (these will be segregated in a later release; for now they
are consolidated into a single entity), while the SubscribingClient represents a
subscribing party. They can be launched in either order.

The PublishingBroker can be instructed to wait until a certain number of
SubscribingClients have connected to it before accepting any commands from the
test harness. This should be done to ensure that test scripts do not run
prematurely under the assumption that all SubscribingClients are up and running.

Refer to the test harness documentation for details on its operation, but
remember that one master harness drives a server SUT (in this case, the
PublishingBroker) as well as one or more slave harnesses, each of which drives one or
more client SUTs (in this case, the SubscribingClients). Each slave harness must
have a unique harness ID, and must know how many client SUTs it is responsible
for spawning and driving.


Detailed Instructions
=======================================================

The steps below give instructions for unpacking and running the Lincoln TA3.1
baseline.  Note that we only provide instructions for running
the test-harness components using the supplied binaries.  The source code is
provided for reference purposes only, to understand how things work, and it is
not recommended to rebuild the binaries.

Initial Setup
-------------------------
See ta3-test-harness.txt for instructions on initial setup.

Building the System
-------------------------

In order to build the test-harness, you will need to have SCons and Java 6 installed. Run

sudo apt-get update
sudo apt-get upgrade
sudo apt-get install scons openjdk-6-jdk openjdk-6-jre

to install all of the necessary components. Go into the java directory.

cd java

Afterward, you should be able to run 

scons -u

to build the baseline *.jar files into the java/jars folder.

Running the Baseline Components
---------------------------------

### Baseline Publisher

The baseline publisher executable is packaged in PublishingBroker.jar. It generally takes
the following parameters (execute 'java -jar PublishingBroker.jar --help) to see complete list of parameters):

  --filename -f value : Metadata schema configuration file name (required)
  --host -h value : Connection address to set up for subscribers (defaults to
                    localhost)
  --port -p value : Port to set up for subscribers (defaults to 61619)

Example usage:

java -jar PublishingBroker.jar -f schema.csv -h 127.0.0.1 -p 61619

### Baseline Subscriber

The baseline subscriber executable is packaged in SubscribingClient.jar. It takes the
following parameters:

  --host -h value : Connection address with which to connect to broker (defaults
                    to localhost)
  --port -p value : Port with which to connect to broker (defaults to 61619)

Example usage:

java -jar SubscribingClient.jar -h 127.0.0.1 -p 61619

### Third Party Broker

In addition to PublishingBroker, there are also two executables that represent
a separate publisher and a separate broker entity. ThirdPartyBroker.jar and
PublishingServer.jar can be invoked similarly to PublishingBroker.jar; just set
the host and port values on the broker to the desired settings, and make sure
that the PublishingServer and SubscribingClients connect with the same settings.

The ThirdPartyBroker is essentially a service that needs to be running as a
daemon while the PublishingServer and SubscribingClients connect/disconnect over
time. The ThirdPartyBroker does not have any automated shutdown designed
currently, and must be manually killed by Ctrl-C or the 'kill' command.

Running Locally with the Test Harness
-------------------

Please refer to the ta3-test-harness.md document for details on test harness
operation. Below is an example invocation of the test harness that will run the
baseline components in such a way as to be able to run a sample script. Note
that the ta3-master-harness command may look like it hasn't finished executing,
but that is because ActiveMQ tends to have some latent log messages that cover
the ready terminal command prompt...just press return, and you should have
control over the terminal again.

Run these commands in separate windows from the
scripts-config/ta3/remote-runner-scripts/ directory. If you want to see the
stdin/out exchange for each harness component be sure to have the appropriate
log folders created.

./ta3-master-harness -p /usr/bin/java -a "-jar PublishingBroker.jar -f ../config/metadata_schema.csv" -c ../test-scripts/sample-simple/sample-simple -d ../logs/mh-std-logs -u

./ta3-slave-harness -p /usr/bin/java -a "-jar SubscribingClient.jar" --connect_addr 127.0.0.1 -d ../logs/sh-0-std-logs -u -n 5 -i sh-0

This will launch a master harness that drives one slave harness and a
PublishingBroker. The PublishingBroker will wait until 5 SubscribingClients have
connected to it before accepting any commands from the test harness (i.e., it
won't send READY until 5 clients are present). The master harness will execute
the contents of sample-simple against the actors it controls, and direct all
stdin/out traffic to the mh-log folder in an unbuffered manner such that the
logs can be analyzed even if any software crashes. Note that the application to
launch is java, and /usr/bin/java should be replaced with wherever your Java
binary is located.

The slave harness has a unique ID (sh-0) and controls five SubscriberClients.
The slave harness will wait for direction from the master harness, and direct
all stdin/out traffic with the SubscribingClients to the sh-0-log/sh-0-X folders
(where X is replaced with the ID of the SubscribingClient that is spawned, which
just counts up from 0). These folders must already exist before running the test
harness to ensure that logs are properly collected.

Alternatively, you may leverage our remote_runner Python script. Please read
the remote_runner README to understand how remote_runner works and the inputs
it requires. 

Put simply, execute something like this from the scripts-config/ta3/remote-runner-scripts
directory: python remote_runner.py -c bll_config.py -m bll-sample-simple_muddler.py

This will launch a detached screen session that contains the contents of a local
test run of the contents of sample-simple. You may access the detached screen by
typing in 'screen -ls' and 'screen -r X', where X is the screen you are looking
for.

To run other tests, follow the same pattern as above. For the config/muddler
files with 'blr' in their titles (for 'baseline remote'), these will SFTP files
to remote hosts specified in a hosts file located in
scripts-config/common/config and specified by a variable in the muddler files.
remote_runner will then launch test harnesses on the appropriate platforms. You
will need to update the host IPs in the hosts files for these to run properly on
your systems. Each invocation of remote runner using the template muddler files
will create a directory under /home/$USER/spar-testing on each remote machine
with a timestamped directory for that particular run of the test script. Again,
please read the remote_runner README for a better understanding of how this
all works.
