//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Maintains a connection to a MySQL server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_MYSQL_CONNECTION_H_
#define CPP_COMMON_MYSQL_CONNECTION_H_

#include <boost/thread.hpp>
#include <memory>
#include <mysql/mysql.h>
#include <string>

/// The main use of this class is with ObjectThreads. Since the MySQL libs don't
/// enable easy multi-threading we work around that by having one connection to
/// the server per thread. ObjectThreads lets us spawn a thread that opens a
/// connection and we can then ensure that each thread is using only its own
/// connection and there's no need for locks, etc.
///
/// Note that we're using the C API here instead of the C++ connector or another
/// C++ library. There are several reasons for this:
///
/// 1) The C++ connector APIs aren't as rich as the C API. In particular there's
/// no way to send large BLOB's without making multiple copies of the data.
/// Similarly, there is not stand-alone function to escape strings so you have to
/// use prepared statements.
///
/// 2) The C++ connector is not well documented. There official online docs have
/// "TODO: add content" messages all over and the examples are incomplete.
///
/// 3) The only other C++ libraries I could find are not well maintained and are
/// the project of just one or two people.
class MySQLConnection {
 public:
  //MySQLConnection();
  MySQLConnection(const std::string& host,
                    const std::string& username,
                    const std::string& password,
                    const std::string& database);
  virtual ~MySQLConnection();
  /*void Connect(const std::string& host,
               const std::string& username,
               const std::string& password,
               const std::string& database);*/
  void Connect();
  void Reconnect();

  MYSQL* GetConnection() {
    return connection_;
  }
 private:
  void Disconnect();
  /// Constructors call this to ensure that the MySQL library is initialized
  /// exactly once and it's initialized before any other MySQL library calls are
  /// made.
  static void InitializeMySQLOnce();
  /// This is called to ensure that the libarary is safely shut down exactly once
  /// and only after all MySQLConnection objects have been freed.
  ///
  /// Note: This assumes that all MySQL connections are via MySQLConnection
  /// objects and that once the 1st connection is made the connection count drops
  /// to 0 exactly once at which point no further connections will be made.
  static void ShutdownMySQLOnce();
  const std::string host_;
  const std::string username_;
  const std::string password_;
  const std::string database_;
  /// These variables track the number of active connections in a thread safe way
  /// so we can be sure to initialize and shut down exactly once.
  static int active_connections_count_;
  static boost::mutex active_connections_count_tex_;

  /// Note that the call to mysql_close in the destructor frees this memory.
  MYSQL* connection_;

};

#endif
