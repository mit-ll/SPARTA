//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        main() function for multi-threaded MySQL client.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/assign/list_of.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <memory>
#include <string>

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/extensible-ready-handler.h"
#include "baseline/common/clearcache-handler.h"
#include "baseline/common/mysql-connection.h"
#include "baseline/common/shutdown-handler.h"
#include "common/safe-file-stream.h"
#include "common/line-raw-parser.h"
#include "common/object_threads.h"
#include "common/event-loop.h"
#include "common/logging.h"
#include "common/statics.h"
#include "query-handler.h"

using boost::assign::list_of;
using namespace std;

namespace po = boost::program_options;

MySQLConnection* ConnectionFactory(const string& host, 
                                   const string& user,
                                   const string& password,
                                   const string& database) {
  MySQLConnection* connection = new MySQLConnection(host, 
                                                    user, 
                                                    password, 
                                                    database);
  connection->Connect();
  return connection;
}

QueryHandler* ConstructQueryHandler(
    ObjectThreads<MySQLConnection>* connection_pool,
    std::ostream* query_log, 
    int max_retries,
    bool enable_events) {
  return new QueryHandler(connection_pool, 
                          query_log, 
                          max_retries, 
                          enable_events);
}

// Standard POSIX file descriptors for stdout and stdin
const int kStdOutFD = 1;
const int kStdInFD = 0;

int main(int argc, char** argv) {
  Initialize();
  string host, user, pwd, db;
  bool enable_events = false;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("host", po::value<string>(&host)->default_value("localhost"),
       "MariaDB host")
      ("database,D", po::value<string>(&db)->default_value("1krows_100kBpr"), 
       "MariaDB database to use")
      ("user,u", po::value<string>(&user)->default_value("root"),
       "MariaDB user name")
      ("password,p", po::value<string>(&pwd), 
       "MariaDB password for given user")
      ("start-threads", po::value<int>()->default_value(10),
       "Number of threads to spawn initially")
      ("max-threads", po::value<int>()->default_value(10),
       "Maximum number of threads to spawn")
      ("max-retries", po::value<int>()->default_value(100),
       "Number of times a query will be resent if the server "
       "disconnects for any reason. If set to -1, queries will "
       "be repeatedly sent until a valid response is received.")
      ("query-log", po::value<string>(),
       "Log all queries sent and the time they took to complete in this "
       "file. This does syncrhonous logging and logs each query twice so "
       "it will have a significant performance impact.")
      ("enable-events,e", "If set, will output information stdout when "
       "particular events occur.")
      ("verbose,v", "If set, will output all messages at DEBUG level and "
       "above. Otherwise, will output all messages at INFO level and above.");
  po::variables_map vm;

  try {
    po::store(po::parse_command_line(argc, argv, desc), vm);
  }
  catch (const boost::bad_any_cast &ex) {
    LOG(FATAL) << ex.what();
  }
  catch (const boost::program_options::invalid_option_value& ex) {
    LOG(FATAL) << ex.what();
  }


  po::notify(vm);    

  // Display help on options
  if (vm.count("help")) {
    cout << desc << endl;
    exit(0);
  }

  // Set logging level
  if (vm.count("verbose") > 0) {
    Log::SetApplicationLogLevel(DEBUG);
  } else {
    Log::SetApplicationLogLevel(INFO);
  }

  // Set enable_events
  if (vm.count("enable-events") > 0) {
    enable_events = true;
  }

  // Validate command line options
  vector<string> req_args = list_of(string("password"));
  for (auto arg : req_args) {
    if (vm.count(arg) == 0) {
      LOG(FATAL) << "You must specify --" << arg;
    }
  }

  // Initialize the connection pool
  ObjectThreads<MySQLConnection> mysql_pool(
      boost::bind(&ConnectionFactory, host, user, pwd, db));
  mysql_pool.set_max_threads(vm["start-threads"].as<int>());
  mysql_pool.Spawn(vm["start-threads"].as<int>());

  // Setup the command and parsing stack.
  EventLoop event_loop;
  ExtensibleReadyHandler* ready_handler =
      new ExtensibleReadyHandler(event_loop.GetWriteQueue(kStdOutFD));
  LineRawParser lr_parser(ready_handler);
  
  NumberedCommandReceiver* numbered_commands =
      new NumberedCommandReceiver(event_loop.GetWriteQueue(kStdOutFD));
  ready_handler->AddHandler("COMMAND", numbered_commands);

  ClearCacheHandler* cch = new ClearCacheHandler(
      event_loop.GetWriteQueue(kStdOutFD));
  ready_handler->AddHandler("CLEARCACHE", cch);
  ready_handler->AddHandler(
      "SHUTDOWN", new ShutdownHandler(numbered_commands, &event_loop));

  auto_ptr<ostream> query_log_stream(NULL);
  if (vm.count("query-log") > 0) {
    query_log_stream.reset(
        new SafeOFStream(vm["query-log"].as<string>().c_str()));
  }
  numbered_commands->AddHandler(
      "SELECT", boost::bind(&ConstructQueryHandler, &mysql_pool,
                            query_log_stream.get(), 
                            vm["max-retries"].as<int>(),
                            enable_events));

  event_loop.RegisterFileDataCallback(
      kStdInFD,
      boost::bind(&LineRawParser::DataReceived, &lr_parser, _1));

  // Start the event loop and wait for exit
  event_loop.Start();
  event_loop.WaitForExit();

  return 0;
}
