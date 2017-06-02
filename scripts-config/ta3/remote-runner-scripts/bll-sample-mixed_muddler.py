import logging
import datetime
import copy
import os
import errno
import random

# Helper function that makes sure both the file specified by filepath, and all
# the intermediate directories in between, exist. Useful for initializing log
# directory hierarchies.
def make_sure_file_exists(filepath):
  try:
    os.makedirs('/'.join(filepath.split('/')[:-1]))
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise
  fd = open(filepath, "w")
  fd.write("")
  fd.close()

def muddle(config, options):
  logger = logging.getLogger(__name__)

  # ===========================================================================
  # NOTE These generally need to be different for every test.
  DEBUG_ENABLED = True
  # TODO CORE_PIN = False currently doesn't work; if you'd like to effectively
  # disable corepinning, leave this as True and proceed to request as many
  # clients as you desire. Clients will be assigned to cores on a host with the
  # least number of tasks, even if a client is already attached to these cores.
  CORE_PIN = False
  # If False, will NOT create new script files in scripts-config/ta3/test-scripts
  CREATE_NEW_SCRIPTS = True
  # TEST_SCRIPT must be the name of the test script's directory within
  # scripts-config/ta3/test-scripts/, and must also be the name of the
  # test script itself
  TEST_SCRIPT = "sample-mixed" 
  HOST_INFO_FILE = "../../common/config/host_info_local.txt"
  # CLIENT_HOST_MODEL specifies the allowed models that can be used for client
  # SUTs. Can be set to "*" if model doesn't matter.
  CLIENT_HOST_MODEL = "local"
  # This will be either NO_DELAY or EXPONENTIAL_DELAY X, where X is a mean
  # publication delay in microseconds
  PUBLICATION_DELAY = "EXPONENTIAL_DELAY 1000000" # ROE variable delta
  # RNG seed used for payload generation
  PAYLOAD_SEED = str(random.randint(1,2000000000))
  print "Payload generation seed:",PAYLOAD_SEED
  # Mean payload sizes in bytes for payload generation. Unless LOADED_SUBS =
  # True, this will send the same publication sequence multiple times with
  # these different mean payload sizes.
  PAYLOAD_SIZES = ["1000"]
  # This is the test log capture period for test logs in seconds
  TIMESTAMP_PERIOD = "15"
  # This is the amount of time to wait for publications to complete before
  # performing any shutdown/cleanup of the test.
  PUB_WAIT = 20
  # This is the amount of time to wait at the end of the test after SHUTDOWNs
  # have been sent.
  END_WAIT = 15

  # Enable this to make this a loaded subscription test. The following
  # parameters will then be used to characterize the loaded subscription test.
  # These parameters do not impact anything if LOADED_SUBS = False.
  LOADED_SUBS = True
  # Mean payload size to use for all publications in this loaded test
  LOADED_PAYLOAD_SIZE = "1000"
  # If this is set, the sets of subscription modifications that will be applied
  # will all be UNsubscriptions.
  TEST_UNSUBS = False
  # Percentage of all subs that will be loaded to facilitate background traffic
  PERCENT_BACKGROUND_SUBS = 0.2
  # Number of sets the remaining subs will be split into. Each set will
  # represent a batch of subs to add while background traffic is occuring. This
  # should usually be set to the number of total subscriptions that are NOT
  # background subscriptions, so as to isolate a single subscription in each
  # set.
  NUM_UPDATE_SETS = 4
  # Number of seconds to wait before starting to apply sets of subs to the
  # background traffic.
  BACKGROUND_WAIT = 5
  # Number of seconds to wait AFTER verification publications have begun for a
  # new set of subs before actually applying the new set of subs.
  PRE_MODIFY_WAIT = 6
  # Number of seconds to wait AFTER a new set of subs has been applied before
  # moving on to the next set of subs. It doesn't hurt to make this large, but
  # will make the test take longer.
  MODIFY_WAIT = 15
  # NOTE that there are some race conditions to consider when changing the delay
  # times above. When a test is generated, one specifies the number of
  # verification publications to generate for each conjunctive equality. Since
  # the number of conjunctive equalities assigned to a client can be random, the
  # total number of verification publications that are sent can vary widely.
  # Also note that it is desirable for some of these verification publications
  # to go out BEFORE a new subscription set is applied, as well as AFTER the new
  # subscription set is applied, so as to confirm that the subscriptions receive
  # no matches before the SUT reports that the set has been applied, and that
  # the subscriptions DO receive matches after the SUT reports as such.
  # Therefore, it is safest to set --num_pubs_per_conj relatively high,
  # PRE_MODIFY_WAIT relatively low, and MODIFY_WAIT relatively high to have a
  # greater chance of desirable test sequencing.
  # ===========================================================================

  # ===========================================================================
  # NOTE These might need to change as directory structures change.
  HARNESS_BIN_DIR = "../../../cpp/test-harness/ta3/opt/"
  LOCAL_CONFIG_DIR = "../config/"
  LOCAL_SCRIPT_DIR = "../test-scripts/" + TEST_SCRIPT + "/"
  # TODO make some better defaults dependent on if we're running locally or
  # remotely...
  #assert options.ssh_user, "Must specify an SSH user to run with"
  #REMOTE_BASE_DIR   = "/home/" + options.ssh_user + "/spar-testing/"
  REMOTE_BASE_DIR = "/home/njhwang/Documents/spar-git/scripts-config/ta3/remote-runner-scripts/"
  REMOTE_BIN_DIR    = REMOTE_BASE_DIR + "bin/"
  REMOTE_CONFIG_DIR = LOCAL_CONFIG_DIR
  # This ensures each invocation of remote_runner with this muddler generates a
  # unique, timestamped directory on remote workstations where test logs will be
  # generated
  #REMOTE_LOG_DIR = REMOTE_BASE_DIR + TEST_SCRIPT + "_" + \
  #                 datetime.datetime.today().strftime('%y%m%d_%H%M%S') + "/"
  REMOTE_LOG_DIR = "/home/njhwang/Documents/spar-archive/" + TEST_SCRIPT + "_" + \
                   datetime.datetime.today().strftime('%y%m%d_%H%M%S') + "/"
  os.makedirs(REMOTE_LOG_DIR)
  #REMOTE_SCRIPT_DIR = REMOTE_LOG_DIR + TEST_SCRIPT + "/"
  REMOTE_SCRIPT_DIR = "/home/njhwang/Documents/spar-git/scripts-config/ta3/test-scripts/" + TEST_SCRIPT + "/"
  # ===========================================================================

  # Load host information from HOST_INFO_FILE
  # TODO check that HOST_INFO_FILE exists
  HOST_INFO = {}
  for line in open(HOST_INFO_FILE):
    items = line.strip().split(' ')
    assert len(items) == 4, "Host info file must have 4 items per " + \
                            "line: IP, num_cores, model, hyperthreaded [y/n]"
    cpu_allocation = {}
    for i in range(int(items[1])):
      cpu_allocation[i] = 0
    HOST_INFO[items[0]] = {"num_cores" : int(items[1]), "model" : items[2],
                           "cpu_allocation" : cpu_allocation, 
                           "hyperthreaded" : True if items[3] == "y" else False}

  # Verify previously loaded config has components defined for all relevant
  # actors
  server = None
  client = None
  third_parties = []
  for c in config.all_components():
    if (c.name == "server"):
      assert not server, "Config can only include one component named 'server'"
      server = c
    elif (c.name == "client"):
      assert not client, "Config can only include one component named 'client'"
      client = c
    elif (c.name.startswith("third-party")):
      third_parties.append(c)
    else:
      logger.critical("Component names can only be 'server', 'client', "
                      "or 'third-party-X'")
      sys.exit(1)
  assert server, "Config must include a component with name 'server'"
  assert client, "Config must include a component with name 'client'"
  assert server.host in HOST_INFO, "Server host not defined in host info file"
  for tp in third_parties:
    assert tp.host in HOST_INFO, "Third party host not defined in host " + \
                                 "info file"
  # Clear config, because we will be creating our own components now
  config.clear_components()

  # Make sure proper test data files are present in the test directory
  assert os.path.isfile(LOCAL_SCRIPT_DIR + "all-subscriptions")
  assert os.path.isfile(LOCAL_SCRIPT_DIR + "all-publications")
  f = open(LOCAL_SCRIPT_DIR + "all-subscriptions", "r")
  last_line = None
  NUM_SUBSCRIPTIONS = 0
  for line in f:
    last_line = line
    NUM_SUBSCRIPTIONS += 1
  f.close()
  NUM_CLIENTS = int(last_line.split(' ')[0]) + 1

  # ===========================================================================
  # NOTE the args for each SUT should be 'muddled' as needed for each performer
  # ===========================================================================

  # Update number of available cores in HOST_INFO
  # Test harnesses each occupy one core
  host_info_copy = copy.deepcopy(HOST_INFO)
  host_info_copy[server.host]["num_cores"] -= server.num_cores + 1
  for tp in third_parties:
    host_info_copy[tp.host]["num_cores"] -= tp.num_cores
  possible_clients = 0
  CLIENT_HOSTS = []
  for host, info_dict in host_info_copy.iteritems():
    if (CLIENT_HOST_MODEL == "*" or \
        CLIENT_HOST_MODEL == info_dict["model"]):
      if (CORE_PIN and \
            info_dict["num_cores"] >= 1 + client.num_cores) or \
          not CORE_PIN:
        possible_clients += (info_dict["num_cores"] - 1) / client.num_cores
        CLIENT_HOSTS.append(host)
  if CORE_PIN:
    assert NUM_CLIENTS <= possible_clients, \
        "Insufficient cores on client hosts for " + str(NUM_CLIENTS) + \
        " clients" 
    assert host_info_copy[server.host]["num_cores"] >= 0, \
        "Insufficient cores on server host"
    for tp in third_parties:
      assert host_info_copy[tp.host]["num_cores"] >= 0, \
        "Insufficient cores on third party host"
  assert len(CLIENT_HOSTS) > 0

  # Distribute the clients on as many hosts as possible
  NUM_SLAVE_HARNESSES = min(len(CLIENT_HOSTS), NUM_CLIENTS)
  NUM_CLIENTS_PER_HOST = [NUM_CLIENTS/NUM_SLAVE_HARNESSES]*NUM_SLAVE_HARNESSES
  for i in range(NUM_CLIENTS % NUM_SLAVE_HARNESSES):
    NUM_CLIENTS_PER_HOST[i] += 1

  if CREATE_NEW_SCRIPTS:
    if LOADED_SUBS:
      VERIFY_PAYLOAD_SIZE = LOADED_PAYLOAD_SIZE
      VERIFY_PAYLOAD_SEED = int(PAYLOAD_SEED)
      assert PERCENT_BACKGROUND_SUBS <= 1.0
      num_background_subs = int(NUM_SUBSCRIPTIONS*PERCENT_BACKGROUND_SUBS)
      num_modify_subs = NUM_SUBSCRIPTIONS - num_background_subs
      assert num_modify_subs > 0
      sub_file = open(LOCAL_SCRIPT_DIR + "all-subscriptions", "r")
      pub_file = open(LOCAL_SCRIPT_DIR + "all-pubs-for-each-sub", "r")
      all_mods_file = open(LOCAL_SCRIPT_DIR + "all-modifications", "w")
      all_mods_file.write("WaitScript " + str(BACKGROUND_WAIT) + "\n")
      master_test_script_file = open(LOCAL_SCRIPT_DIR + TEST_SCRIPT, "w")
      master_test_script_file.write("UpdateNetworkMap " + \
          str(NUM_SLAVE_HARNESSES) + " " + str(NUM_CLIENTS) + "\n")

      curr_slave_harness = 0
      curr_client = 0
      prev_client = 0
      num_client_subs = 0
      sub_script_file = open(LOCAL_SCRIPT_DIR + "sh-" + \
                        str(curr_slave_harness) + "-background-subscriptions", "w")
      sub_script_file.write("SubscribeScript\n")
      master_test_script_file.write("CallRemoteScript sh-" + \
          str(curr_slave_harness) + " sh-" + str(curr_slave_harness) + \
          "-background-subscriptions\n")
      num_perm_subs = num_background_subs
      if TEST_UNSUBS:
        num_background_subs = NUM_SUBSCRIPTIONS
      # Generate background subs
      for i in range(num_background_subs):
        sub_line = sub_file.readline()
        sub_items = sub_line.split(' ')
        pub_line = pub_file.readline()
        pub_items = pub_line.split(' ')
        assert pub_items[0] == sub_items[0]
        assert pub_items[1] == sub_items[1]
        while pub_items[0] == sub_items[0] and pub_items[1] == sub_items[1]:
          pub_line = pub_file.readline()
          pub_items = pub_line.split(' ')
        if int(sub_items[0]) > prev_client:
          curr_client += 1
        if curr_client >= NUM_CLIENTS_PER_HOST[curr_slave_harness]:
          curr_slave_harness += 1
          curr_client = 0
          sub_script_file.close()
          sub_script_file = open(LOCAL_SCRIPT_DIR + "sh-" + \
                            str(curr_slave_harness) + "-background-subscriptions", "w")
          sub_script_file.write("SubscribeScript\n")
          master_test_script_file.write("CallRemoteScript sh-" + \
              str(curr_slave_harness) + " sh-" + str(curr_slave_harness) + \
              "-background-subscriptions\n")
        prev_client = int(sub_items[0])
        sub_script_file.write(str(curr_client) + " " + \
                              str(num_client_subs) + " " + \
                              ' '.join(sub_items[2:]))
        num_client_subs += 1
        if TEST_UNSUBS and num_client_subs == num_perm_subs:
          first_mod_sub = num_client_subs
          first_client = curr_client
          first_slave_harness = curr_slave_harness
          first_prev_client = prev_client
      if TEST_UNSUBS:
        num_client_subs = first_mod_sub
        curr_client = first_client
        curr_slave_harness = first_slave_harness
        prev_client = first_prev_client
      sub_script_file.close()
      assert int(num_modify_subs/NUM_UPDATE_SETS) > 0
      update_set = 0
      num_subs_in_set = 0
      boundary_case = False
      if curr_client == (NUM_CLIENTS_PER_HOST[curr_slave_harness] - 1):
        curr_client = 0
        curr_slave_harness += 1
        boundary_case = True
      sub_script_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                        str(curr_slave_harness) + "-update-subscriptions", "w")
      if TEST_UNSUBS:
        sub_script_file.write("UnsubscribeScript\n")
      else:
        sub_script_file.write("SubscribeScript\n")
      pub_check_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                       str(curr_slave_harness) + "-verify-publications", "w")
      mod_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                 str(curr_slave_harness) + "-modifications", "w")
      mod_file.write("WaitScript " + str(PRE_MODIFY_WAIT) + "\n")
      mod_file.write("CallRemoteScript sh-" + str(curr_slave_harness) + \
                     " set-" + str(update_set) + "-sh-" + \
                     str(curr_slave_harness) + "-update-subscriptions\n")
      mod_file.write("WaitScript " + str(MODIFY_WAIT) + "\n")
      mod_file.close()
      VERIFY_PAYLOAD_SEED += 1
      all_mods_file.write("PublishAndModifySubscriptionsScript" + \
                          " set-" + str(update_set) + "-sh-" + \
                          str(curr_slave_harness) + "-verify-publications" + \
                          " " + PUBLICATION_DELAY + " " + \
                          str(VERIFY_PAYLOAD_SEED) + " " + \
                          VERIFY_PAYLOAD_SIZE + \
                          " set-" + str(update_set) + "-sh-" + \
                          str(curr_slave_harness) + "-modifications\n")
      if TEST_UNSUBS:
        sub_file.close()
        pub_file.close()
        sub_file = open(LOCAL_SCRIPT_DIR + "all-subscriptions", "r")
        pub_file = open(LOCAL_SCRIPT_DIR + "all-pubs-for-each-sub", "r")
        for i in range(num_perm_subs):
          sub_line = sub_file.readline()
          sub_items = sub_line.split(' ')
          pub_line = pub_file.readline()
          pub_items = pub_line.split(' ')
          assert pub_items[0] == sub_items[0]
          assert pub_items[1] == sub_items[1]
          while pub_items[0] == sub_items[0] and pub_items[1] == sub_items[1]:
            pub_line = pub_file.readline()
            pub_items = pub_line.split(' ')
      if boundary_case:
        curr_client -= 1
      while True:
        sub_line = sub_file.readline()
        if len(sub_line) == 0:
          break
        sub_items = sub_line.split(' ')
        if int(sub_items[0]) > prev_client:
          curr_client += 1
        if curr_client >= NUM_CLIENTS_PER_HOST[curr_slave_harness]:
          curr_slave_harness += 1
          if curr_slave_harness >= NUM_SLAVE_HARNESSES:
            break
          curr_client = 0
          sub_script_file.close()
          sub_script_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                            str(curr_slave_harness) + "-update-subscriptions", "w")
          pub_check_file.close()
          pub_check_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                            str(curr_slave_harness) + "-verify-publications", "w")
          if TEST_UNSUBS:
            sub_script_file.write("UnsubscribeScript\n")
          else:
            sub_script_file.write("SubscribeScript\n")
          mod_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                     str(curr_slave_harness) + "-modifications", "w")
          mod_file.write("WaitScript " + str(PRE_MODIFY_WAIT) + "\n")
          mod_file.write("CallRemoteScript sh-" + str(curr_slave_harness) + \
                         " set-" + str(update_set) + "-sh-" + \
                         str(curr_slave_harness) + "-update-subscriptions\n")
          mod_file.write("WaitScript " + str(MODIFY_WAIT) + "\n")
          mod_file.close()
          VERIFY_PAYLOAD_SEED += 1
          all_mods_file.write("PublishAndModifySubscriptionsScript" + \
                              " set-" + str(update_set) + "-sh-" + \
                              str(curr_slave_harness) + "-verify-publications" + \
                              " " + PUBLICATION_DELAY + " " + \
                              str(VERIFY_PAYLOAD_SEED) + " " + \
                              VERIFY_PAYLOAD_SIZE + \
                              " set-" + str(update_set) + "-sh-" + \
                              str(curr_slave_harness) + "-modifications\n")
        assert pub_items[0] == sub_items[0]
        assert pub_items[1] == sub_items[1]
        while True:
          if pub_items[0] != sub_items[0] or pub_items[1] != sub_items[1]:
            break
          pub_check_file.write("METADATA\n" + ' '.join(pub_items[2:]))
          pub_line = pub_file.readline()
          pub_items = pub_line.split(' ')

        prev_client = int(sub_items[0])
        if TEST_UNSUBS:
          sub_script_file.write(str(curr_client) + " " + \
                                str(num_client_subs) + "\n")
        else:
          sub_script_file.write(str(curr_client) + " " + \
                                str(num_client_subs) + " " + \
                                ' '.join(sub_items[2:]))
        num_client_subs += 1
        num_subs_in_set += 1
        if num_subs_in_set >= int(num_modify_subs/NUM_UPDATE_SETS):
          num_subs_in_set = 0
          update_set += 1
          if update_set >= NUM_UPDATE_SETS:
            break
          if curr_client < NUM_CLIENTS_PER_HOST[curr_slave_harness] - 1:
            sub_script_file.close()
            sub_script_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                              str(curr_slave_harness) + "-update-subscriptions", "w")
            pub_check_file.close()
            pub_check_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                              str(curr_slave_harness) + "-verify-publications", "w")
            if TEST_UNSUBS:
              sub_script_file.write("UnsubscribeScript\n")
            else:
              sub_script_file.write("SubscribeScript\n")
            mod_file = open(LOCAL_SCRIPT_DIR + "set-" + str(update_set) + "-sh-" + \
                       str(curr_slave_harness) + "-modifications", "w")
            mod_file.write("WaitScript " + str(PRE_MODIFY_WAIT) + "\n")
            mod_file.write("CallRemoteScript sh-" + str(curr_slave_harness) + \
                           " set-" + str(update_set) + "-sh-" + \
                           str(curr_slave_harness) + "-update-subscriptions\n")
            mod_file.write("WaitScript " + str(MODIFY_WAIT) + "\n")
            mod_file.close()
            VERIFY_PAYLOAD_SEED += 1
            all_mods_file.write("PublishAndModifySubscriptionsScript" + \
                                " set-" + str(update_set) + "-sh-" + \
                                str(curr_slave_harness) + "-verify-publications" + \
                                " " + PUBLICATION_DELAY + " " + \
                                str(VERIFY_PAYLOAD_SEED) + " " + \
                                VERIFY_PAYLOAD_SIZE + \
                                " set-" + str(update_set) + "-sh-" + \
                                str(curr_slave_harness) + "-modifications\n")
      sub_script_file.close()
      pub_check_file.close()

      # Create the master test script for the test
      all_mods_file.close()
      master_test_script_file.write("RootModeMasterScript CLEARCACHE\n")
      master_test_script_file.write("PublishAndModifySubscriptionsScript all-publications " + \
          PUBLICATION_DELAY + " " + PAYLOAD_SEED + " " + LOADED_PAYLOAD_SIZE + " all-modifications\n")
      master_test_script_file.write("WaitScript " + str(PUB_WAIT) + "\n")
      master_test_script_file.write("RootModeMasterScript SHUTDOWN\n")
      master_test_script_file.write("WaitScript " + str(END_WAIT) + "\n")
      master_test_script_file.close()
    else:
      # Create all the sh-X-Y files for the test
      sub_file = open(LOCAL_SCRIPT_DIR + "all-subscriptions", "r")
      sub_line = sub_file.readline()
      base_num_clients = 0
      num_client_subs = 0
      for i in range(NUM_SLAVE_HARNESSES):
        sub_script_file = open(LOCAL_SCRIPT_DIR + "sh-" + str(i) + "-subscriptions", "w")
        sub_script_file.write("SubscribeScript\n")
        # Maximum possible client ID for this host
        max_client_id = base_num_clients + NUM_CLIENTS_PER_HOST[i]
        while (len(sub_line) > 0):
          sub_items = sub_line.split(' ')
          if int(sub_items[0]) < max_client_id:
            sub_script_file.write(str(int(sub_items[0]) - base_num_clients) + " " + \
                                  str(num_client_subs) + " " + \
                                  ' '.join(sub_items[2:]))
            num_client_subs += 1
            sub_line = sub_file.readline()
          else:
            base_num_clients = max_client_id
            sub_script_file.close()
            break

      # Create the master test script for the test
      master_test_script_file = open(LOCAL_SCRIPT_DIR + TEST_SCRIPT, "w")
      master_test_script_file.write("UpdateNetworkMap " + \
          str(NUM_SLAVE_HARNESSES) + " " + str(NUM_CLIENTS) + "\n")
      for i in range(NUM_SLAVE_HARNESSES):
        master_test_script_file.write("CallRemoteScript sh-" + str(i) + \
            " sh-" + str(i) + "-subscriptions" + "\n")
      master_test_script_file.write("RootModeMasterScript CLEARCACHE\n")
      for PAYLOAD_SIZE in PAYLOAD_SIZES:
        master_test_script_file.write("PublishScript all-publications " + \
            PUBLICATION_DELAY + " " + PAYLOAD_SEED + " " +  PAYLOAD_SIZE + "\n")
        master_test_script_file.write("WaitScript " + str(PUB_WAIT) + "\n")
      master_test_script_file.write("RootModeMasterScript SHUTDOWN\n")
      master_test_script_file.write("WaitScript " + str(END_WAIT) + "\n")
      master_test_script_file.close()

  def get_taskset_mask(host, num_cores):
    selected_cpus = []
    cpu_allocation = HOST_INFO[host]["cpu_allocation"]
    for i in range(num_cores):
      min_alloc = min(cpu_allocation.values())
      selected_cpu = \
          [k for k in cpu_allocation if cpu_allocation[k] == min_alloc][0]
      HOST_INFO[host]["cpu_allocation"][selected_cpu] += 1
      selected_cpus.append(selected_cpu)
    taskset_bin_mask = ""
    for i in range(HOST_INFO[host]["num_cores"]):
      if i in selected_cpus:
        new_bits = "1"
      else:
        new_bits = "0"
      if HOST_INFO[host]["hyperthreaded"]:
        new_bits = new_bits*2
      taskset_bin_mask = new_bits + taskset_bin_mask
    return hex(int(taskset_bin_mask,2))

  def confirm_no_double_quotes(to_check):
    if type(to_check) is str:
      assert '"' not in to_check
    elif type(to_check) is list:
      for item in to_check:
        assert '"' not in item
    else:
      assert False, "Could not check for quotes in item"

  def confirm_no_single_quotes(to_check):
    if type(to_check) is str:
      assert "'" not in to_check
    elif type(to_check) is list:
      for item in to_check:
        assert "'" not in item
    else:
      assert False, "Could not check for quotes in item"

  def confirm_no_quotes(to_check):
    confirm_no_double_quotes(to_check)
    confirm_no_single_quotes(to_check)

  # Third party components
  for tp in third_parties:
    tp.start_index = 1
    tp.base_dir = REMOTE_BIN_DIR
    if tp.host != "localhost":
      make_sure_file_exists("empty-log-dirs/" + tp.name + ".log")
      tp.files["empty-log-dirs/" + tp.name + ".log"] = \
               REMOTE_LOG_DIR + tp.name + ".log"
    # Convert executable to taskset if core pinning
    if CORE_PIN:
      old_executable = tp.executable
      tp.executable = "/usr/bin/taskset"
      old_args = copy.deepcopy(tp.args)
      tp.args = [get_taskset_mask(tp.host, tp.num_cores),
                 old_executable]
      tp.args.extend(old_args)
    # Convert executable to script for better logging
    old_executable = tp.executable
    tp.executable = "/usr/bin/script"
    old_args = copy.deepcopy(tp.args)
    confirm_no_single_quotes(old_args)
    for i in range(len(old_args)):
      if ' ' in old_args[i]:
        old_args[i] = "'" + old_args[i] + "'" 
    # NOTE if environment variables need to be ported to the screen session,
    # this syntax seemed to work prior to old_executable:
    #   export MAVEN_OPTS=-Xmx4096m && export LD_LIBRARY_PATH=~/libdir:~/includedir && 
    tp.args = ["-c", old_executable + " " + ' '.join(old_args), REMOTE_LOG_DIR + tp.name + ".log"]
    config.add_component(tp)
    print "  ", tp.name, "running on", tp.host

  # Base harness component
  base_harness = Component()
  base_harness.start_index = 1
  base_harness.base_dir = REMOTE_BIN_DIR

  # Master harness component
  master_harness = copy.deepcopy(base_harness)
  master_harness.name = "master-harness"
  master_harness.executable = "./ta3-master-harness"
  master_harness.host = server.host
  master_harness.num_cores = server.num_cores
  sut_executable = server.executable
  sut_args = server.args
  # Convert SUT executable to taskset if core pinning
  # TODO(njhwang) how to capture the TTY output of SUT? need another script
  # command nested in here?
  if CORE_PIN:
    sut_executable = "/usr/bin/taskset"
    sut_args = [get_taskset_mask(master_harness.host, server.num_cores),
                server.executable]
    sut_args.extend(server.args)
  master_harness.args = [
    "-p", sut_executable,
    "-a", ' '.join(sut_args),
    "--test_log_dir", REMOTE_LOG_DIR + "mh-test-logs",
    "-c", REMOTE_SCRIPT_DIR + TEST_SCRIPT,
    "--timestamp_period", TIMESTAMP_PERIOD]
  if DEBUG_ENABLED:
    master_harness.args.extend(["-d", REMOTE_LOG_DIR + "mh-std-logs", "-u", "-v"])
  master_harness.files = {}
  # Copy files from server component
  if master_harness.host != "localhost":
    for item in server.files:
      if not item.startswith("/"):
        master_harness.files[item] = REMOTE_BIN_DIR + server.files[item]
      else:
        master_harness.files[item] = server.files[item]
    # Copy files for test harness executable
    master_harness.files[HARNESS_BIN_DIR + "ta3-master-harness"] = \
                         master_harness.executable
    # Copy config files
    master_harness.files[LOCAL_CONFIG_DIR + "metadata_schema.csv"] = \
                         REMOTE_CONFIG_DIR + "metadata_schema.csv"
    # Copy test script files
    master_harness.files.update( \
      util.recursive_files_dict(LOCAL_SCRIPT_DIR, 
                                REMOTE_SCRIPT_DIR))
    # Copy logging directories
    # TODO(njhwang) can remote_runner support creating empty dirs now?
    make_sure_file_exists("empty-log-dirs/mh-test-logs/dummy-log")
    master_harness.files.update( \
      util.recursive_files_dict("empty-log-dirs/mh-test-logs", 
                                REMOTE_LOG_DIR + "mh-test-logs"))
    if DEBUG_ENABLED:
      make_sure_file_exists("empty-log-dirs/mh-std-logs/sut_stdin")
      master_harness.files.update( \
        util.recursive_files_dict("empty-log-dirs/mh-std-logs", 
                                  REMOTE_LOG_DIR + "mh-std-logs"))
  else:
    os.makedirs(REMOTE_LOG_DIR + "mh-test-logs")
    if DEBUG_ENABLED:
      os.makedirs(REMOTE_LOG_DIR + "mh-std-logs")
  # Convert harness executable to taskset if core pinning
  if CORE_PIN:
    old_executable = master_harness.executable
    master_harness.executable = "/usr/bin/taskset"
    old_args = copy.deepcopy(master_harness.args)
    master_harness.args = [get_taskset_mask(master_harness.host, 1),
                           "./" + old_executable]
    master_harness.args.extend(old_args)
  # Convert harness executable to script for better log capture
  confirm_no_quotes(master_harness.executable)
  confirm_no_quotes(master_harness.args)
  old_executable = master_harness.executable
  master_harness.executable = "/usr/bin/script"
  old_args = copy.deepcopy(master_harness.args)
  confirm_no_single_quotes(old_args)
  for i in range(len(old_args)):
    if ' ' in old_args[i]:
      old_args[i] = "'" + old_args[i] + "'" 
  master_harness.args = \
    ["-c", old_executable + " " + ' '.join(old_args),
     REMOTE_LOG_DIR + master_harness.name + ".log"]
  config.add_component(master_harness)
  print "  ", master_harness.name, "running on", master_harness.host

  # Slave harness components
  # NOTE ACS likes to start from a count of 1
  #clients_processed = 0
  clients_processed = 1
  for i in range(NUM_SLAVE_HARNESSES):
    slave_harness = copy.deepcopy(base_harness)
    slave_harness.name = "slave-harness-" + str(i)
    slave_harness.host = CLIENT_HOSTS[i]
    slave_harness.executable = "./ta3-slave-harness"
    slave_harness.num_cores = client.num_cores
    slave_harness_id = "sh-" + str(i)
    slave_harness_std_log_dir = slave_harness_id + "-std-logs"
    # Make sure the test harnesses are communicating on the 'mgmt' network
    back_channel_addrs = ['127','0','0','1']
    if master_harness.host != "localhost":
      back_channel_addrs = master_harness.host.split('.')[:2]
      back_channel_addrs.append('10')
      back_channel_addrs.append(master_harness.host.split('.')[-1])
    else:
      os.makedirs(REMOTE_LOG_DIR + slave_harness_std_log_dir)
    sut_executable = client.executable
    sut_args = client.args
    if CORE_PIN:
      sut_executable = "/usr/bin/taskset"
      #sut_args = [get_taskset_mask(slave_harness.host, client.num_cores),
      sut_args = ["%c", client.executable]
      sut_args.extend(client.args)
    # Generate unique args for each SUT, if necessary
    all_args = ' '.join(sut_args)
    if "%n" in all_args:
      all_args = ""
      pad_width = len(str(NUM_CLIENTS))
      for j in range(NUM_CLIENTS_PER_HOST[i]):
        temp_args = []
        for arg in sut_args:
          new_arg = arg.replace("%n", str(clients_processed))
          # NOTE BBN likes the unique argument to just be the client ID on the
          # current harness, rather than the global client ID
          #new_arg = arg.replace("%n", str(j))
          if "%c" in new_arg:
            new_arg = new_arg.replace("%c", 
              get_taskset_mask(slave_harness.host, client.num_cores))
          temp_args.append(new_arg)
        all_args += ' '.join(temp_args) + ';'
        clients_processed += 1
      all_args = all_args.rstrip(';')
    else:
      temp_args = all_args
      all_args = "" 
      for j in range(NUM_CLIENTS_PER_HOST[i]):
        all_args += temp_args.replace("%c", 
          get_taskset_mask(slave_harness.host, client.num_cores)) + ';'
      all_args = all_args.rstrip(';')
    slave_harness.args = [
      "-i", slave_harness_id,
      "-n", str(NUM_CLIENTS_PER_HOST[i]),
      "-p", sut_executable,
      "-a", all_args,
      "--connect_addr", '.'.join(back_channel_addrs),
      "--test_log", REMOTE_LOG_DIR + slave_harness_id + "-test-log",
      "--timestamp_period", TIMESTAMP_PERIOD]
    if DEBUG_ENABLED:
      slave_harness.args.extend(["-d", REMOTE_LOG_DIR + slave_harness_std_log_dir,
                                 "-u", "-v"])
    slave_harness.files = {}
    if slave_harness.host != "localhost":
      # Copy files from client component
      # TODO(njhwang) weird bug where if I don't specify REMOTE_BIN_DIR, some *.jar's get
      # copied to the root user directory rather than in bin/third_party
      for item in client.files:
        if not item.startswith("/"):
          slave_harness.files[item] = REMOTE_BIN_DIR + client.files[item]
        else:
          slave_harness.files[item] = client.files[item]
      # Copy test harness executable
      slave_harness.files[HARNESS_BIN_DIR + "ta3-slave-harness"] = \
                          slave_harness.executable
      # Copy logging directories
      make_sure_file_exists("empty-log-dirs/dummy-log")
      slave_harness.files["empty-log-dirs/dummy-log"] = REMOTE_LOG_DIR + "dummy-log"
      if DEBUG_ENABLED:
        for j in range(NUM_CLIENTS_PER_HOST[i]):
          make_sure_file_exists("empty-log-dirs/" + slave_harness_std_log_dir + \
                                "/" + slave_harness_id + "-" + str(j) + \
                                "/sut_stdin")
        slave_harness.files.update( \
          util.recursive_files_dict("empty-log-dirs/" + slave_harness_std_log_dir, 
                                    REMOTE_LOG_DIR + slave_harness_std_log_dir))
    if CORE_PIN:
      old_executable = slave_harness.executable
      slave_harness.executable = "/usr/bin/taskset"
      old_args = copy.deepcopy(slave_harness.args)
      slave_harness.args = [get_taskset_mask(slave_harness.host, 1),
                            "./" + old_executable]
      slave_harness.args.extend(old_args)
    # Convert harness executable to script for better log capture
    confirm_no_quotes(slave_harness.executable)
    confirm_no_quotes(slave_harness.args)
    old_executable = slave_harness.executable
    slave_harness.executable = "/usr/bin/script"
    old_args = copy.deepcopy(slave_harness.args)
    confirm_no_single_quotes(old_args)
    for i in range(len(old_args)):
      if ' ' in old_args[i]:
        old_args[i] = "'" + old_args[i] + "'" 
    slave_harness.args = \
      ["-c", old_executable + " " + ' '.join(old_args),
       REMOTE_LOG_DIR + slave_harness.name + ".log"]
    config.add_component(slave_harness)
    print "  ", slave_harness.name, "running on", slave_harness.host

  print "Test artifacts located in " + REMOTE_LOG_DIR + " on each host"
