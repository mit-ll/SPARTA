
The Lincoln TA3 test harness consists of two components, a client component and
a server component. This document contains instructions for running the test
harness components and using it to run systems under test (SUTs). 

Test Harness Operations
=====================================================

The master and slave test harnesses are used to spawn the server and client
software components, respectively. Each harness spawns their SUTs right away,
and then waits to connect to the other harness components over the network.
Nothing will happen until the master and slave test harness components have a
network connection. Thus, you can use this interim period as an opportunity to
start any third party components.

Specifically, if you need to 1) start the server, then 2) start third parties,
then 3) start the clients, you would start the master test harness, which would
start your server. Next, you would start your third parties as the test would
not be running yet. Then, you would start your clients by starting the
appropriate number of slave test harnesses. At that point, the master and slave
harnesses would connect to each other, and the test would start.

Detailed Instructions
=====================================================

The steps below give instructions for unpacking and running the Lincoln release
package. Note that we only provide instructions for running the test harness
components using the supplied binaries. The source code is provided for
reference purposes only, to understand how things work, and it is not
recommended to rebuild the binaries.

Initial Setup
-------------------------
Please follow the default install instructions to set up your environment.

Setting up Remote Runner
-------------------------

In order to use our remote_runner utility, which deploys and executes arbitrary
sets of executables and config files across multiple hosts, you should have the
following installed on all workstations. Note that you will need additional
packages to run the baseline software (see the baseline documentation for
details).

sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen python-paramiko openssl

Building the System
-------------------------

In order to build the test harness, you will need to have SCons, g++, and
several boost libraries installed. You may also want Java installed for building
the baseline (see the baseline documentation for details). 

sudo apt-get install scons g++ libboost-all-dev libevent-dev

To compile the test harness code, change into the cpp/ directory and run

scons -u --opt

to build the test harness master and slave binaries into the
cpp/test-harness/ta3/opt folder.

Running the Harness Components
---------------------------------

### Test-Harness Master

The test harness master binary is called ta3-master-harness. It generally takes
the following parameters (execute with -h to see complete list of parameters):

-p path to SUT server executable (required)
-a arguments to pass to SUT server executable
-c path to a test script file to execute (required)
-d folder in which debug logs are stored; note that currently this folder must
   already exist prior to invoking the master harness
-u option to specify unbuffered debug logs; this will impact performance
--test-log-dir path to where script logs will be placed (required); again, note
               that this folder must already exist prior to invoking the master
               harness

The master will listen for slave connections by default on 127.0.0.1:1234.

### Test-Harness Slaves

The test harness slave binary is called ta3-slave-harness. It generally takes
the following parameters (execute with -h to see complete list of parameters):

-p path to SUT client executable (required)
-a arguments to pass to SUT client executables; note that this can either be a
   single string that will be passed to ALL SUT client executables, or it can be
   a ';' delimited list of strings such that each item in the delimited list
   will be passed to a unique client SUT executable
-i unique id that the master harness can use to identify this slave harness
   (required)
-n number of client SUTs for this slave harness to spawn (required)
-d folder in which debug logs are stored; note that currently this folder must
   already exist prior to invoking the slave harness, and that the slave harness
   will try to write to folders additionally identified by each client SUT ID
   (i.e. if you spawn 3 client SUTs and have identified 'debug' as your logging
   directory, the harness will attempt to write log files to 'debug0', 'debug1',
   and 'debug2', and these directories MUST ALL EXIST prior to running)
-u option to specify unbuffered debug logs; this may impact performance
--connect_addr IP address where master is listening for incoming connections
               (required)
--connect_port IP port where master is listening for incoming connections
               (defaults to 1234)

When spawning multiple slaves, be sure that each has a unique id.

### Dummy Baseline SUTs

Feel free to use the dummy-ta3-server and dummy-ta3-client as sample SUTs with
the test harnesses to familiarize yourself with running the test harness and to
ensure that the components are built properly. 

dummy-ta3-client simply randomly responds to numbered commands with successes
and failures, responds with DONE to CLEARCACHE commands, and exits the
application upon SHUTDOWN.  

dummy-ta3-server does the same, but additionally will randomly inject
PUBLICATION event messages into the test harness stdin.  Note that these dummy
scripts are simply meant to illustrate the API that will be used to communicate
with the SUTs. In particular, any failure messages do not indicate that anything
is wrong, as the dummy scripts just output failure messages 50% of the time to
illustrate what a failure message looks like.

You can use the dummy SUTs to view sample SUT-to-harness traffic with the
following commands after first creating the mh-log and all sh-*-log directories
(see command line option notes about debug directories above). Be sure to update
sample-simple and any other config files appropriately if you decide to run with
different numbers of harnesses/client SUTs.

Run these commands in separate windows from the
scripts-config/ta3/remote-runner-scripts/bin/ directory. If you want to see the
stdin/out exchange for each harness component be sure to have the folders
mh-log, sh1-log0, sh1-log1, sh2-log0, sh2-log1, sh2-log2, and sh2-log3 created
whereever you please (in the commands below, they are in the same directory as
the harness binaries).

./ta3-master-harness -p dummy-ta3-server -c ../../test-scripts/sample-simple/sample-simple -d mh-log -u
./ta3-slave-harness -i sh-0 -n 5 -p dummy-ta3-client --connect_addr 127.0.0.1 -d sh-0-log -u

Writing Scripts
-----------------------------------

### Master Harness Scripts
Please refer to the example sample-simple script delivered in
scripts-config/ta3/test-scripts/sample-simple for a concrete example. 

The following are the script commands that can be included in a script file that
is fed to the master harness via the –c option:

- UpdateNetworkMap slave-harness-count client-sut-count
This always needs to be the first command run in a script. This updates the
master harness' internal information on what slave harnesses and client SUTs it
can talk to. The arguments specify the number of expected slave harnesses and
total number of client SUTs that should be connected to the master harness
before anything is run. The arguments provided must match the number of slave
harness instances that are running, and also match the total number of SUTs that
are spawned by the slave harnesses.

- CallRemoteScript target-harness script-file
This runs the contents of script-file against a slave harness identified by
target-harness. target-harness must be a valid harness ID that was specified by
the –i option. script-file needs to be located in the same directory as the file
that is fed to the master harness via the –c option. The first line of the
script file needs to be the name of the script to run, and the lines below are
the arguments for that script. Note that in our setup, this is always used to
run a script against a client SUT, so script-file should only contain scripts
that are runnable against a client SUT (see more info below on what scripts can
be run by a slave harness).

- WaitScript seconds
Simply pauses the master harness for seconds.

- PublishScript publications-file delay-function random-seed mean-payload-size
This commands the server SUT to publish all publications specified in
publications-file. The publications will be separated by delays specified by
delay-function (values can either be NO_DELAY or EXPONENTIAL_DELAY followed by a
mean delay in microseconds). The contents of publications-file must be a
sequence of METADATA specifications.  Refer to the mh-publications example file
in sample-simple folder. random-seed is used by the master harness to generate
random payload bytes, as well as random payload sizes. mean-payload-size will be
the mean payload size with a Poisson distribution around that mean (but will not
be allowed to be less than 1).

- PublishAndModifySubscriptionsScript background-pubs-file delay-function random-seed mean-payload-size modification-script
This commands the system to perform a more elaborate test, whereby all
publications in background-pubs-file are started in a separate thread with the
provided delay-function, random-seed, and mean-payload-size (see PublishScript
notes above). Then, all items in modification-script, which can be either
WaitScript, CallRemoteScript, or additional PublishAndModifySubscriptionsScript
commands, will be executed in order. The background publications will be
terminated upon completion of modification-script. When using this script
command, one will generally want to precede it with some background subscription
commands, a WaitScript command to allow the background traffic to start
matching, then a call to PublishAndModifySubscriptionsScript. The call to
PublishAndModifySubscriptionsScript should generally apply some subscriptions of
interest, then send additional publications to verify that that subscription
took effect.

- RootModeMasterScript root-mode-command
This sends root-mode-command to both the server SUT, and to all connected client
SUTs. This is typically used to send SHUTDOWN to everything at the end of a
test, or to send CLEARCACHE to everything during a test.

### Slave Harness Scripts

The following are the script commands that can be run against a slave harness
via a CallRemoteScript from the master harness:

- SubscribeScript
  target-sut subscription-id subscription-filter
  target-sut1 subscription-id1 subscription-filter1
  ...
When a slave harness spawns its client SUTs, they are simply numbered in the
order that they were spawned in. target-sut is a number that specifies which
client SUT to apply the subscription to; therefore, if a slave harness has
spawned 5 client SUTs, target-sut can be [0, 4]. subscription-id is just a
number that uniquely identifies a subscription for a particular SUT (so the same
number should not be used twice for the same target-sut). subscription-filter is
a SQL where clause that specifies the filter. Refer to the sh*-subscriptions
example files in the config/ folder of this release.

Multiple subscriptions can be performed by a single SubscribeScript call by
having them on separate lines.

Recall that SubscribeScript will only be run when the master harness executes a
CallRemoteScript call. So for example, the master harness could execute
'CallRemoteScript sh1 sh1-subscriptions', and this would run tell the slave
harness identified by 'sh1' to execute the contents of 'sh1-subscriptions'.
'sh1-subscriptions' could have the following text to instruct sh1 to execute a
SubscribeScript on its client SUTs...this would tell the first client SUT to
subscribe to "lname = 'ADAMS'", the second SUT to subscribe to "fname =
'DONNA'", etc.
    SubscribeScript
    0 0 lname = 'ADAMS'
    1 0 fname = 'DONNA'
    2 0 lname = 'MARTIN'
    3 0 fname = 'CATHERINE'
    4 0 lname = 'TORRES'

- UnsubscribeScript
  target-sut subscription-id
  target-sut1 subscription-id1
  ...
This is very similar to SubscribeScript, except that it does not require any
subscription filter arguments. Refer to the description of SubscribeScript
above.
