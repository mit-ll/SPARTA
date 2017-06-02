//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Main application for the TA1 server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 11 May 2012   omd            Original Version
//*****************************************************************

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/assign/list_inserter.hpp>
#include <boost/assign/list_of.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <string>

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/extensible-ready-handler.h"
#include "baseline/common/clearcache-handler.h"
#include "baseline/common/mysql-connection.h"
#include "baseline/common/shutdown-handler.h"
#include "common/safe-file-stream.h"
#include "common/object_threads.h"
#include "common/output-handler.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/schema.h"
#include "delete-handler.h"
#include "insert-handler.h"
#include "update-handler.h"
#include "verify-handler.h"
#include "util.h"

namespace po = boost::program_options;

using boost::assign::list_of;
using std::string;

MySQLConnection* ConnectionFactory(const string& host, const string& user,
                                   const string& password,
                                   const string& database) {
  MySQLConnection* connection = 
    new MySQLConnection(host, user, password, database);
  connection->Connect();
  return connection;
}

DataInserter* InserterFactory(
    const string& host, const string& user, const string& password,
    const string& database, const Schema* schema,
    const std::set<std::string>& stop_words) {
  std::auto_ptr<MySQLConnection> connection(
      ConnectionFactory(host, user, password, database));
  return new DataInserter(connection, schema, stop_words);

}

InsertHandler* ConstructInsertHandler(ObjectThreads<DataInserter>* insert_pool,
                                      bool enable_events) {
  return new InsertHandler(insert_pool, enable_events);
}

// Standard POSIX file descriptors for stdout and stdin
const int kStdOutFD = 1;
const int kStdInFD = 0;

int main(int argc, char** argv) {
  Initialize();
  Log::SetOutputStream(&std::cerr);

  string host, user, pwd, db, stopwords_path;
  int num_init_threads, num_max_threads;
  bool enable_events = false;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print this help message")
      ("host", po::value<string>(&host)->default_value("localhost"),
       "MySQL host")
      ("database,D", po::value<string>(&db)->default_value("1krows_100kBpr"),
       "Database to use")
      ("user,u", po::value<string>(&user)->default_value("root"),
       "User name for MySQL connection")
      ("password,p", po::value<string>(&pwd), "Password for MySQL connection")
      ("schema-file,f", po::value<string>(),
       "Path to a file holding the schema info")
      ("stop-words,s", po::value<string>(&stopwords_path),
       "Path to the file containing the list of stopwords to use "
       "for parsing notes fields")
      ("init-threads",
       po::value<int>(&num_init_threads)->default_value(10),
       "Number of MySQL threads to spawn right away")
      ("max-threads",
       po::value<int>(&num_max_threads)->default_value(20),
       "Maximum number of MySQL threads so spawn. Note that "
       "there are actually two thread pools each of which can "
       "have this many threads so in rare cases there "
       "may be double this many threads active.")
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
  vector<string> req_args = 
    list_of(string("password"))("schema-file")("stop-words");
  for (auto arg : req_args) {
    if (vm.count(arg) == 0) {
      LOG(FATAL) << "You must specify --" << arg;
    }
  }

  ObjectThreads<MySQLConnection> mysql_pool(
      boost::bind(&ConnectionFactory, host, user, pwd, db));
  mysql_pool.Spawn(num_init_threads);
  mysql_pool.set_max_threads(num_max_threads);

  // Setup the command and parsing stack.
  EventLoop event_loop;
  ExtensibleReadyHandler* ready_handler =
      new ExtensibleReadyHandler(event_loop.GetWriteQueue(kStdOutFD));
  LineRawParser lr_parser(ready_handler);
  
  NumberedCommandReceiver* numbered_commands =
      new NumberedCommandReceiver(event_loop.GetWriteQueue(kStdOutFD));
  ready_handler->AddHandler("COMMAND", numbered_commands);

  SafeIFStream schema_file(vm["schema-file"].as<string>().c_str());
  Schema schema(&schema_file);

  std::set<std::string> stopwords;
  GetStopWords(stopwords_path, &stopwords);

  ObjectThreads<DataInserter> insert_pool(
      std::bind(&InserterFactory, host, user, pwd, db,
                &schema, stopwords));
  ObjectThreads<MySQLConnection> connection_pool(
      std::bind(&ConnectionFactory, host, user, pwd, db));

  insert_pool.set_max_threads(num_max_threads);
  connection_pool.set_max_threads(num_max_threads);

  numbered_commands->AddHandler(
      "INSERT", boost::bind(&ConstructInsertHandler, &insert_pool,
                                                     enable_events));
  numbered_commands->AddHandler(
      "UPDATE", [&connection_pool, &schema, &stopwords, enable_events] () {
        return new UpdateHandler(&connection_pool, &schema, stopwords,
                                 enable_events); });
  numbered_commands->AddHandler(
      "DELETE", [&connection_pool, &schema, enable_events] () {
        return new DeleteHandler(&connection_pool, &schema, enable_events); });
  numbered_commands->AddHandler(
      "VERIFY", [&connection_pool, enable_events] () {
        return new VerifyHandler(&connection_pool, enable_events); });
  ready_handler->AddHandler(
      "CLEARCACHE", new ClearCacheHandler(event_loop.GetWriteQueue(kStdOutFD)));
  ready_handler->AddHandler(
      "SHUTDOWN", new ShutdownHandler(numbered_commands, &event_loop));

  event_loop.RegisterFileDataCallback(
      kStdInFD,
      boost::bind(&LineRawParser::DataReceived, &lr_parser, _1));

  event_loop.Start();
  event_loop.WaitForExit();
  numbered_commands->WaitForAllCommands();

  return 0;
}
