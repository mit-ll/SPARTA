//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of MySQLConnection 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 May 2012   omd            Original Version
//*****************************************************************

#include "mysql-connection.h"

#include "common/logging.h"
#include "common/check.h"

using std::string;

MySQLConnection::MySQLConnection(const string& host, const string& username, 
                                 const string& password, 
                                 const string& database) :
    host_(host), username_(username), password_(password), database_(database), connection_(NULL) {
  // Make sure mysql_library_init has been called exactly once.
  InitializeMySQLOnce();
}

/*void MySQLConnection::Connect(
    const string& host, const string& username, const string& password,
    const string& database) {*/
void MySQLConnection::Connect() {
  // Make sure connect isn't called on an existing connection
  CHECK(connection_ == NULL);
  CHECK(mysql_thread_safe() == 1);
  connection_ = mysql_init(NULL);
  CHECK(connection_ != NULL);
  // TODO(odain) Set up SSL. Need to figure out certificates and such...
  // mysql_ssl_set();
  MYSQL* connect_result = mysql_real_connect(connection_, host_.c_str(),
                                             username_.c_str(),
                                             password_.c_str(), 
                                             database_.c_str(),
                                             0, NULL, 0);
  // If the connection succeeded the pointer to the MYSQL struct is returned.
  if (connect_result != connection_) {
    LOG(ERROR) << "Error connecting to the database:\n"
               << mysql_error(connection_);
    exit(1);
  }
}

void MySQLConnection::Reconnect() {
  Disconnect();
  Connect();
}

void MySQLConnection::Disconnect() {
  // Note: I *am* calling mysql_thread_end here in the destructor. I have even
  // added logging to ensure that it's called. Yet, in some applications I'm
  // getting "Error in my_thread_global_end(): X threads didn't exit" where X is
  // the number of threads that had a MySQL connection. This indicates that
  // mysql_thread_end wasn't called. I have no idea why this behavior, but it
  // seems not to be a serious issue.
  mysql_thread_end();
  mysql_close(connection_);
  connection_ = NULL;
}

MySQLConnection::~MySQLConnection() {
  Disconnect();
  // Make sure mysql_library_end gets called after all the active connections
  // are closed.
  ShutdownMySQLOnce();
}

int MySQLConnection::active_connections_count_ = 0;
boost::mutex MySQLConnection::active_connections_count_tex_;

void MySQLConnection::InitializeMySQLOnce() {
  boost::lock_guard<boost::mutex> l(active_connections_count_tex_);
  if (active_connections_count_ == 0) {
    mysql_library_init(0, NULL, NULL);
  }
  ++active_connections_count_;
}

void MySQLConnection::ShutdownMySQLOnce() {
  boost::lock_guard<boost::mutex> l(active_connections_count_tex_);
  --active_connections_count_;
  if (active_connections_count_ == 0) {
    mysql_library_end();
  }
}
