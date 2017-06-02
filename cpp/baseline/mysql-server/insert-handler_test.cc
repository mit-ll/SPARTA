//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for InsertHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 11 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE InsertHandlerTest

#include "insert-handler.h"

#include <mysql/mysql.h>

#include "baseline/common/mysql-connection.h"
#include "test-init.h"

MySQLConnection* ConnectionFactory() {
  MySQLConnection* connection = new MySQLConnection;
  connection->Connect("", "", "", "db1");
  return connection;
}

BOOST_AUTO_TEST_CASE(TestInsertsWork) {
  MySQLConnection connection;
  
  MYSQL* mysql = mysql_init(NULL);
  mysql_options(mysql, MYSQL_OPT_USE_EMBEDDED_CONNECTION, NULL);

  ObjectThreads<MySQLConnection> mysql_pool(ConnectionFactory);

}
