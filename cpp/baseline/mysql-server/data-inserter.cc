//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of DataInserter
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Oct 2012   omd            Original Version
//*****************************************************************

#include "data-inserter.h"

#include "baseline/common/common-mysql-defs.h"
#include "common/check.h"
#include "common/schema.h"
#include "common/string-algo.h"

using namespace std;

DataInserter::DataInserter(
    auto_ptr<MySQLConnection> connection, const Schema* schema,
    const set<string>& stop_words)
    : connection_(connection), schema_(schema),
      // TODO(odain): These probably shouldn't be hard coded...
      index_insert_builder_(kKeywordIndexTableName, kStemsIndexTableName,
                            stop_words),
	  // TODO(mjr): allow for custom alarm words
      alarm_words_()
      {
  PrepareStatements();
}

DataInserter::~DataInserter() {
  map<string, MYSQL_STMT*>::iterator stmt_it;
  for (stmt_it = prep_stmt_map_.begin(); stmt_it != prep_stmt_map_.end();
       ++stmt_it) {
    mysql_stmt_close(stmt_it->second);
  }

  for (map<string, MYSQL_BIND*>::iterator i = bind_map_.begin();
       i != bind_map_.end(); ++i) {
    delete[] i->second;
  }

  map<pair<string, string>, BindManager*>::iterator i;
  for (i = bind_manager_map_.begin(); i != bind_manager_map_.end(); ++i) {
    delete i->second;
  }
}

void DataInserter::PerformInserts(LineRawData<Knot>* data, 
                                  LineRawData<Knot>* hash,
                                  DoneCallback cb,
                                  EventCallback eb) {
  // Event ID 4: Insert command processing began
  if (eb != nullptr) {
    eb(4, nullptr);
  }
  // This method's paramter should be a unique_ptr, but the rest of the API
  // doesn't suppor that. At least this way we can be sure we don't have a
  // memory leak.
  //
  // TODO(odain) Fix the API!
  unique_ptr<LineRawData<Knot> > data_ptr(data);
  unique_ptr<LineRawData<Knot> > hash_ptr(hash);
  // Note: the order of inserts here is important. In order to satisfy the
  // atomicity constraints we have to be sure that the *view* won't return
  // inconsitent results. Since the view is an inner-join we can insert into
  // base and fpnotes in any order as neither will be retrieved until both have
  // completed. However, we have to be sure to update the full-text indices
  // before we do the base and fpnotes tables or else we could have a rows that
  // are retrived by some, but not all, queries.

  // TODO(njhwang) Inserting the hash relies on there being a hash field defined as the *last*
  // field in the schema. This isn't an ideal requirement, but was the easiest
  // way to get hash information properly inserted into a MariaDB database in
  // Phase 2. Ideally, whatever is generating the line raw data for insertion
  // would include the proper hash value at whatever index the schema specifies;
  // however, the row hashing is currently a process that is disjoint from the
  // line raw data generator (i.e., the Python data generator), and is done by
  // directory-importer.cc. Therefore, we pass in the hash information here,
  // make sure there is only a single unit of line raw data provided, and append
  // it to the rest of the row data.
  if (hash != nullptr) {
    // data should have all fields *except* the 'hash' column
    CHECK(data->Size() == schema_->NumFields() - 1);
    // 'hash' column info should be the last set of FieldIds
    const vector<FieldId>* last_fids = schema_->GetFieldIds(schema_->NumFields() - 1);
    // 'hash' column should only be in one table
    CHECK(last_fids->size() == 1);
    // Make sure things are named appropriately
    CHECK(last_fids->at(0).table() == string(kRowHashesTableName));
    CHECK(last_fids->at(0).field() == string(kRowHashesHashFieldName));
    // Should only be one item of LineRawData
    CHECK(hash->Size() == 1);
    data->AddLine(hash->Get(0));
  } else {
    CHECK(data->Size() == schema_->NumFields());
  }

  LOG(DEBUG) << "Processing insert for row " << data->Get(0);

  // First bind all the data. If the field is one that should be indexed, get
  // the insert statement for the insert and execute it.
  for (size_t i = 0; i < schema_->NumFields(); ++i) {
    const vector<FieldId>* fids = schema_->GetFieldIds(i);
    CHECK(fids->size() > 0);
    for (size_t j = 0; j < fids->size(); ++j) {
      FieldId fid = fids->at(j);
      DCHECK(bind_manager_map_.find(fid) != bind_manager_map_.end());
      bind_manager_map_[fid]->Bind(data->Get(i));

      if (schema_->GetFieldInfo(fid).index) {
        string keyword_insert, stem_insert;
        index_insert_builder_.GetInsertStatements(
            data->Get(0).ToString(),  fids->at(0).field(), data->Get(i),
            &keyword_insert, &stem_insert);

        string alarms_insert;
        alarm_words_.GetInsertStatement(kAlarmsIndexTableName,
    			data->Get(0).ToString(), fids->at(0).field(),
    			data->Get(i).ToString(), &alarms_insert);

        if (!keyword_insert.empty()) {
          // Event ID 5: Insert keyword index command submitted
          if (eb != nullptr) {
            eb(5, nullptr);
          }
          int insert_result = mysql_real_query(
              connection_->GetConnection(), keyword_insert.data(),
              keyword_insert.size());

          CHECK(insert_result == 0)
              << "Error updating keyword index for row "
              << data->Get(0) << ":\n"
              << mysql_error(connection_->GetConnection())
              << "\nQuery was:\n" << keyword_insert;
        }

        if (!stem_insert.empty()) {
          // Event ID 6: Insert stem index command submitted
          if (eb != nullptr) {
            eb(6, nullptr);
          }
          int insert_result = mysql_real_query(
              connection_->GetConnection(), stem_insert.data(),
              stem_insert.size());

          CHECK(insert_result == 0)
              << "Error updating stem index for row "
              << data->Get(0) << ":\n"
              << mysql_error(connection_->GetConnection())
              << "\nQuery was:\n" << stem_insert;
        }

        if (!alarms_insert.empty()) {
          int insert_result = mysql_real_query(
              connection_->GetConnection(), alarms_insert.data(),
              alarms_insert.size());
	  

          CHECK(insert_result == 0)
              << "Error updating alarm index for row "
              << data->Get(0) << ":\n"
              << mysql_error(connection_->GetConnection())
              << "\nQuery was:\n" << alarms_insert;
	  

        }
      }
    }
  }

  // Then issue all the prepared statements to actually do the inserting.
  map<string, MYSQL_STMT*>::iterator stmt_it;
  for (stmt_it = prep_stmt_map_.begin(); stmt_it != prep_stmt_map_.end();
       ++stmt_it) {
    DCHECK(bind_map_.find(stmt_it->first) != bind_map_.end());
    mysql_stmt_bind_param(stmt_it->second, bind_map_[stmt_it->first]);
    // Event ID 7: Insert command submitted
    if (eb != nullptr) {
      eb(7, nullptr);
    }
    int insert_result = mysql_stmt_execute(stmt_it->second);
    CHECK(insert_result == 0) << "Error executing insert for "
        << stmt_it->first << ". Error:\n"
        << mysql_stmt_error(stmt_it->second);
  }
  if (cb != nullptr) {
    cb();
  }
}

void DataInserter::PrepareStatements() {
  set<string>::const_iterator table_it;
  for (table_it = schema_->GetAllTables().begin();
       table_it != schema_->GetAllTables().end(); 
       ++table_it) {

    const vector<FieldId>& fields_in_table =
        schema_->GetFieldsInTable(*table_it);

    vector<string> field_names;
    field_names.reserve(fields_in_table.size());
    for (size_t j = 0; j < fields_in_table.size(); ++j) {
      field_names.push_back(fields_in_table[j].field());
    }
    PrepareStatement(*table_it, field_names);
  }
}

void DataInserter::PrepareStatement(const string& table_name,
                                    const vector<string>& field_names) {
  ostringstream insert_template;
  insert_template << "INSERT INTO " << table_name << "("
      << Join(field_names, ", ") << ") VALUES (";

  vector<string> place_holders(field_names.size(), "?");
  insert_template << Join(place_holders, ", ") << ")";

  string insert_template_str = insert_template.str();
  LOG(DEBUG) << "Preparing statement: " << insert_template_str;

  MYSQL_STMT* stmt = mysql_stmt_init(connection_->GetConnection());
  DCHECK(stmt != NULL);
  int prep_result = mysql_stmt_prepare(stmt, insert_template_str.data(),
                                       insert_template_str.size());
  CHECK(prep_result == 0)
      << "Error preparing statement:\n" << insert_template_str
      << "\nError:\n" << mysql_stmt_error(stmt);

  prep_stmt_map_.insert(make_pair(table_name, stmt));
  PrepareStatementBinds(table_name);
}

void DataInserter::PrepareStatementBinds(const string& table_name) {
  const vector<FieldId>& fields = schema_->GetFieldsInTable(table_name);
  MYSQL_BIND* bind_array = new MYSQL_BIND[fields.size()];
  bind_map_.insert(make_pair(table_name, bind_array));

  for (size_t i = 0; i < fields.size(); ++i) {
    FieldInfo f_info = schema_->GetFieldInfo(fields[i]);
    LOG(DEBUG) << "Binding field: " << fields[i].field();
    BindManager* manager = BindManager::GetBindManager(
        f_info.type, f_info.unsigned_flag, f_info.max_length, bind_array + i);
    bind_manager_map_.insert(make_pair(fields[i], manager));
  }
}
