//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for UpdateHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Oct 2012   omd            Original Version
//*****************************************************************

// TODO(odain): None of these tests are as robust as I'd like. They all check
// that we get a set of expected queries but we're also checking for things that
// could safely change like the spaces in the queries and the order of the
// queries (the order is partially, but not completely required). I don't
// anticipate changing these things, making the tests more robust would be a ton
// of work, and time is short...

#define BOOST_TEST_MODULE UpdateHandlerTest
#include "common/test-init.h"

#include "update-handler.h"

#include <boost/assign/list_inserter.hpp>
#include <set>
#include <string>
#include <vector>

#include "common/check.h"
#include "common/line-raw-data.h"
#include "common/schema.h"

using namespace std;

class TestableUpdateHandler : public UpdateHandler {
 public:
  TestableUpdateHandler(
      Schema* schema, const std::set<std::string>& stop_words)
      : UpdateHandler(nullptr, schema, stop_words) {
  }

  vector<string> GetSQLStatements(
       const std::string& row_id, LineRawData<Knot>* command_data) const {
    return UpdateHandler::GetSQLStatements(row_id, command_data, nullptr);
  }

 protected:
   virtual std::string GetSQLString(
       MySQLConnection* connection, Knot data, const FieldInfo& f_info) const {
     CHECK(connection == nullptr);
     if (schema_->RequiresQuotes(f_info)) {
       return string("'") + data.ToString() + "'";
     } else {
       return data.ToString();
     }
   }
};

// Check that updates to a single table where we're not updating any keywords or
// stemming indexed fields works as expected.
BOOST_AUTO_TEST_CASE(SingleNonIndexUpdateWorks) {
  LineRawData<Knot> update_data;
  update_data.AddLine(Knot(new string("fname")));
  update_data.AddLine(Knot(new string("harry")));

  istringstream schema_file(
      "name,type,table,length,index\n"
      "id,BIGINT,base:notes:fingerprint,0,false\n"
      "fname,CHAR,base,11,false\n"
      "lname,CHAR,base,15,false\n"
      "notes1,TEXT,notes,100,true\n"
      "fingerprint,BLOB,fingerprint,109234,false\n");
  Schema schema(&schema_file);
  set<string> stopwords;
  stopwords.insert("a");
  stopwords.insert("the");

  TestableUpdateHandler uh(&schema, stopwords);
  vector<string> update_statements = uh.GetSQLStatements("185", &update_data);

  // We expect the lock statements even though they're not necessary when only a
  // single table is updated.
  BOOST_REQUIRE_EQUAL(update_statements.size(), 3);
  BOOST_CHECK_EQUAL(update_statements[0],
                    "LOCK TABLES keywords WRITE, stems WRITE, base WRITE, "
                   "fingerprint WRITE, notes WRITE");
  BOOST_CHECK_EQUAL(
      update_statements[1], "UPDATE base SET fname = 'harry' where id = 185");
  BOOST_CHECK_EQUAL(update_statements[2], "UNLOCK TABLES");
}

// Check that we get the right update statements if we update more than a single
// table but we don't update any fields that are indexed.
BOOST_AUTO_TEST_CASE(MultiTableNoIndexWorks) {
  LineRawData<Knot> update_data;
  update_data.AddLine(Knot(new string("fname")));
  update_data.AddLine(Knot(new string("harry")));
  update_data.AddLine(Knot(new string("lname")));
  update_data.AddLine(Knot(new string("Dain")));

  istringstream schema_file(
      "name,type,table,length,index\n"
      "id,BIGINT,base:notes:fingerprint,0,false\n"
      "fname,CHAR,base,11,false\n"
      "lname,CHAR,notes,15,false\n"
      "notes1,TEXT,notes,100,true\n"
      "fingerprint,BLOB,fingerprint,109234,false\n");
  Schema schema(&schema_file);
  set<string> stopwords;
  stopwords.insert("a");
  stopwords.insert("the");

  TestableUpdateHandler uh(&schema, stopwords);
  vector<string> update_statements = uh.GetSQLStatements("222", &update_data);

  // We expect the lock statements even though they're not necessary when only a
  // single table is updated.
  BOOST_REQUIRE_EQUAL(update_statements.size(), 4);
  BOOST_CHECK_EQUAL(update_statements[0],
                    "LOCK TABLES keywords WRITE, stems WRITE, base WRITE, "
                   "fingerprint WRITE, notes WRITE");
  BOOST_CHECK_EQUAL(
      update_statements[1], "UPDATE base SET fname = 'harry' where id = 222");
  BOOST_CHECK_EQUAL(
      update_statements[2], "UPDATE notes SET lname = 'Dain' where id = 222");
  BOOST_CHECK_EQUAL(update_statements[3], "UNLOCK TABLES");
}

// Check that we get the right update statements if we update more than a single
// field in a single table and none of the fields that are indexed.
BOOST_AUTO_TEST_CASE(MultiFieldSingleTableNoIndexWorks) {
  LineRawData<Knot> update_data;
  update_data.AddLine(Knot(new string("fname")));
  update_data.AddLine(Knot(new string("harry")));
  update_data.AddLine(Knot(new string("lname")));
  update_data.AddLine(Knot(new string("Dain")));

  istringstream schema_file(
      "name,type,table,length,index\n"
      "id,BIGINT,base:notes:fingerprint,0,false\n"
      "fname,CHAR,base,11,false\n"
      "lname,CHAR,base,15,false\n"
      "notes1,TEXT,notes,100,true\n"
      "fingerprint,BLOB,fingerprint,109234,false\n");
  Schema schema(&schema_file);
  set<string> stopwords;
  stopwords.insert("a");
  stopwords.insert("the");

  TestableUpdateHandler uh(&schema, stopwords);
  vector<string> update_statements = uh.GetSQLStatements("222", &update_data);

  // We expect the lock statements even though they're not necessary when only a
  // single table is updated.
  BOOST_REQUIRE_EQUAL(update_statements.size(), 3);
  BOOST_CHECK_EQUAL(update_statements[0],
                    "LOCK TABLES keywords WRITE, stems WRITE, base WRITE, "
                   "fingerprint WRITE, notes WRITE");
  BOOST_CHECK_EQUAL(
      update_statements[1],
      "UPDATE base SET fname = 'harry', lname = 'Dain' where id = 222");
  BOOST_CHECK_EQUAL(update_statements[2], "UNLOCK TABLES");
}

// Test that updating a field that needs to be indexed creates the right
// statements.
BOOST_AUTO_TEST_CASE(IndexUpdatesWork) {
  LineRawData<Knot> update_data;
  update_data.AddLine(Knot(new string("fname")));
  update_data.AddLine(Knot(new string("harry")));
  update_data.AddLine(Knot(new string("notes1")));
  update_data.AddLine(Knot(new string("This is a the words")));

  istringstream schema_file(
      "name,type,table,length,index\n"
      "id,BIGINT,base:notes:fingerprint,0,false\n"
      "fname,CHAR,base,11,false\n"
      "lname,CHAR,base,15,false\n"
      "notes1,TEXT,notes,100,true\n"
      "fingerprint,BLOB,fingerprint,109234,false\n");
  Schema schema(&schema_file);
  set<string> stopwords;
  stopwords.insert("a");
  stopwords.insert("the");

  TestableUpdateHandler uh(&schema, stopwords);
  vector<string> update_statements = uh.GetSQLStatements("101", &update_data);

  // We expect the lock statements even though they're not necessary when only a
  // single table is updated.
  BOOST_REQUIRE_EQUAL(update_statements.size(), 8);
  BOOST_CHECK_EQUAL(update_statements[0],
                    "LOCK TABLES keywords WRITE, stems WRITE, base WRITE, "
                   "fingerprint WRITE, notes WRITE");
  BOOST_CHECK_EQUAL(
      update_statements[1],
      "DELETE FROM keywords WHERE id = 101 and col = 'notes1'");
  BOOST_CHECK_EQUAL(
      update_statements[2],
      "DELETE FROM stems WHERE id = 101 and col = 'notes1'");
  BOOST_CHECK_EQUAL(
      update_statements[3],
      "INSERT into keywords (id, col, word) VALUES "
      "(101, 'notes1', \"is\"), (101, 'notes1', \"this\"), "
      "(101, 'notes1', \"words\")");
  BOOST_CHECK_EQUAL(
      update_statements[4],
      "INSERT into stems (id, col, word) VALUES "
      "(101, 'notes1', \"is\"), (101, 'notes1', \"thi\"), "
      "(101, 'notes1', \"word\")");
  BOOST_CHECK_EQUAL(
      update_statements[5],
      "UPDATE base SET fname = 'harry' where id = 101");
  BOOST_CHECK_EQUAL(
      update_statements[6],
      "UPDATE notes SET notes1 = 'This is a the words' where id = 101");
  BOOST_CHECK_EQUAL(update_statements[7], "UNLOCK TABLES");
}
