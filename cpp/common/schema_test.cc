//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for Schema 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 12 Sep 2012   omd            Original Version
//*****************************************************************

#include "schema.h"

#define BOOST_TEST_MODULE SchemaTest
#include "test-init.h"

#include <sstream>

using namespace std;

BOOST_AUTO_TEST_CASE(ParsingWorks) {
  istringstream data_file(
      // header line
      "name,type,table,length,index\n"
      "hours_worked_per_week,CHAR,fpnotes,20,false\n"
      "first_name,ENUM,base,0,false\n"
      "last_name,INT,fpnotes,0,false\n"
      "notes,BLOB,base,1000,true\n"
      "weeks_worked_last_year,TINYINT UNSIGNED,base,0,false\n");

  Schema s(&data_file);

  BOOST_REQUIRE_EQUAL(s.Size(), 5);
  const vector<FieldId>& fields_in_base =
      s.GetFieldsInTable("base");
  BOOST_REQUIRE_EQUAL(fields_in_base.size(), 3);
  BOOST_CHECK_EQUAL(fields_in_base[0].field(), "first_name");
  BOOST_CHECK_EQUAL(fields_in_base[0].table(), "base");
  BOOST_CHECK_EQUAL(fields_in_base[1].field(), "notes");
  BOOST_CHECK_EQUAL(fields_in_base[1].table(), "base");
  BOOST_CHECK_EQUAL(fields_in_base[2].field(), "weeks_worked_last_year");
  BOOST_CHECK_EQUAL(fields_in_base[2].table(), "base");

  const vector<FieldId>& fields_in_fpnotes =
      s.GetFieldsInTable("fpnotes");
  BOOST_REQUIRE_EQUAL(fields_in_fpnotes.size(), 2);
  BOOST_CHECK_EQUAL(fields_in_fpnotes[0].field(), "hours_worked_per_week");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[0].table(), "fpnotes");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[1].field(), "last_name");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[1].table(), "fpnotes");

  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("fpnotes", "last_name")),
                    MYSQL_TYPE_LONG);
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("base", "weeks_worked_last_year")),
                    MYSQL_TYPE_TINY);
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("base", "notes")),
                    MYSQL_TYPE_BLOB);

  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("fpnotes", "hours_worked_per_week")).max_length, 20);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "notes")).max_length, 1000);

  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "weeks_worked_last_year")).unsigned_flag, true);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("fpnotes", "last_name")).unsigned_flag, false);

  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "notes")).index, true);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "first_name")).index, false);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("fpnotes", "last_name")).index, false);


  BOOST_CHECK_EQUAL(s.GetAllTables().size(), 2);
  BOOST_CHECK(s.GetAllTables().find("base") != s.GetAllTables().end());
  BOOST_CHECK(s.GetAllTables().find("fpnotes") != s.GetAllTables().end());
}

// Same exact test as above but make sure it works even if the file doesn't end
// in a "\n" character.
BOOST_AUTO_TEST_CASE(ParsingWorksNoFinalNewline) {
  istringstream data_file(
      // header line
      "name,type,table,length,index\n"
      "hours_worked_per_week,CHAR,fpnotes,20,false\n"
      "first_name,ENUM,base,0,false\n"
      "last_name,INT,fpnotes,0,false\n"
      "notes,BLOB,base,1000,true");

  Schema s(&data_file);

  BOOST_REQUIRE_EQUAL(s.Size(), 4);
  const vector<FieldId>& fields_in_base =
      s.GetFieldsInTable("base");
  BOOST_REQUIRE_EQUAL(fields_in_base.size(), 2);
  BOOST_CHECK_EQUAL(fields_in_base[0].field(), "first_name");
  BOOST_CHECK_EQUAL(fields_in_base[0].table(), "base");
  BOOST_CHECK_EQUAL(fields_in_base[1].field(), "notes");
  BOOST_CHECK_EQUAL(fields_in_base[1].table(), "base");

  const vector<FieldId>& fields_in_fpnotes =
      s.GetFieldsInTable("fpnotes");
  BOOST_REQUIRE_EQUAL(fields_in_fpnotes.size(), 2);
  BOOST_CHECK_EQUAL(fields_in_fpnotes[0].field(), "hours_worked_per_week");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[0].table(), "fpnotes");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[1].field(), "last_name");
  BOOST_CHECK_EQUAL(fields_in_fpnotes[1].table(), "fpnotes");

  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("fpnotes", "last_name")),
                    MYSQL_TYPE_LONG);
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("base", "notes")),
                    MYSQL_TYPE_BLOB);

  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("fpnotes", "hours_worked_per_week")).max_length, 20);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "notes")).max_length, 1000);

  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "notes")).index, true);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("base", "first_name")).index, false);
  BOOST_CHECK_EQUAL(s.GetFieldInfo(
          FieldId("fpnotes", "last_name")).index, false);

  BOOST_CHECK_EQUAL(s.GetAllTables().size(), 2);
  BOOST_CHECK(s.GetAllTables().find("base") != s.GetAllTables().end());
  BOOST_CHECK(s.GetAllTables().find("fpnotes") != s.GetAllTables().end());
}

// Check that things work if a field is in more than one table.
BOOST_AUTO_TEST_CASE(MultipleTablesWorks) {
  istringstream data_file(
      "name,type,table,length,index\n"
      "id,BIGINT,base:fpnotes,0,false\n"
      "fname,CHAR,base,20,false\n"
      "notes,TEXT,fpnotes,1000,false\n");

  Schema s(&data_file);

  BOOST_REQUIRE_EQUAL(s.Size(), 4);
  BOOST_REQUIRE_EQUAL(s.GetFieldIds(0)->size(), 2);
  BOOST_CHECK_EQUAL(s.GetFieldIds(0)->at(0).table(), "base");
  BOOST_CHECK_EQUAL(s.GetFieldIds(0)->at(0).field(), "id");
  BOOST_CHECK_EQUAL(s.GetFieldIds(0)->at(1).table(), "fpnotes");
  BOOST_CHECK_EQUAL(s.GetFieldIds(0)->at(1).field(), "id");
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("base", "id")), MYSQL_TYPE_LONGLONG);
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("fpnotes", "id")),
                    MYSQL_TYPE_LONGLONG);

  BOOST_REQUIRE_EQUAL(s.GetFieldIds(1)->size(), 1);
  BOOST_CHECK_EQUAL(s.GetFieldIds(1)->at(0).table(), "base");
  BOOST_CHECK_EQUAL(s.GetFieldIds(1)->at(0).field(), "fname");
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("base", "fname")),
                    MYSQL_TYPE_STRING);

  BOOST_REQUIRE_EQUAL(s.GetFieldIds(2)->size(), 1);
  BOOST_CHECK_EQUAL(s.GetFieldIds(2)->at(0).table(), "fpnotes");
  BOOST_CHECK_EQUAL(s.GetFieldIds(2)->at(0).field(), "notes");
  BOOST_CHECK_EQUAL(s.GetFieldType(FieldId("fpnotes", "notes")),
                    MYSQL_TYPE_BLOB);
}
