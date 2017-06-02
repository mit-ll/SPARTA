//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of QueryHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 May 2012   omd            Original Version
//*****************************************************************

#include "query-handler.h"

#include <algorithm>
#include <boost/bind.hpp>
#include <cstring>
#include <string>

#include "baseline/common/common-mysql-defs.h"
#include "baseline/common/stemmer.h"
#include "common/check.h"
#include "common/statics.h"
#include "common/string-algo.h"
#include "common/timer.h"

using std::string;

QueryHandler::QueryHandler(ObjectThreads<MySQLConnection>* connection_pool,
                           std::ostream* query_log, 
                           int max_retries,
                           bool events_enabled) 
    : connection_pool_(connection_pool), 
      query_log_(query_log),
      max_retries_(max_retries),
      events_enabled_(events_enabled) {
}

void QueryHandler::Execute(LineRawData<Knot>* command_data) {
  // Event ID 0: Query received
  if (events_enabled_) {
    WriteEvent(0);
  }
  LOG(DEBUG) << "Adding a new task. # running threads: "
             << connection_pool_->NumRunningThreads() << "/"
             << connection_pool_->NumThreads(); 
  connection_pool_->AddWork(
      boost::bind(&QueryHandler::RunQuery, this, _1, command_data));
  LOG(DEBUG) << "Added a new task. # running threads: "
             << connection_pool_->NumRunningThreads() << "/"
             << connection_pool_->NumThreads(); 
}

void QueryHandler::RunQuery(MySQLConnection* connection,
                            LineRawData<Knot>* command_data) {
  CHECK(command_data->Size() == 1);
  DCHECK(command_data->Get(0).StartsWith("SELECT ", 7));

  string query_string;
  command_data->Get(0).ToString(&query_string);
  if (NeedsExpansion(query_string)) {
    LOG(DEBUG) << "Expanding query " << query_string
        << " to handle stemming, keyword, proximity searches";
    ExpandQuery(&query_string);
  }
  // Event ID 1: Query parsed
  if (events_enabled_) {
    WriteEvent(1);
  }

  std::auto_ptr<Timer> timer;
  if (query_log_ != nullptr) {
    timer.reset(new Timer);
    timer->Start();
    (*query_log_) << "[QUERY] " << query_string << endl;
  }

  bool query_submitted = false;
  bool query_repeated = false;
  int num_tries = 1;
  while (!query_submitted) {
    // Event ID 2: Query submission attempted (with attempt count included)
    if (events_enabled_) {
      WriteEvent(2, new string(itoa(num_tries)));
    }
    if (mysql_real_query(connection->GetConnection(),
                         query_string.c_str(), query_string.size()) != 0) {

      if (query_log_ != nullptr) {
        (*query_log_) << "[ERROR " << timer->Elapsed()
            << "] Attempt #" << num_tries << ", query: " 
            << query_string << endl;
      }

      unsigned int err_code = mysql_errno(connection->GetConnection());
      // err_code == 2006 -> "MySQL Server has gone away"
      if (err_code == 2006) {
        num_tries++;
        if (num_tries < max_retries_ || max_retries_ == -1) {
          if (!query_repeated) {
            query_repeated = true;
            LOG(WARNING) << "Query " << query_string << " being repeated...";
          }
          connection->Reconnect();
          continue;
        }
      }
      LineRawData<Knot> results;
      results.AddLine(Knot(new string("FAILED")));
      Knot err_str;
      Knot state_str(new string("SQL State: "));
      const char* err = mysql_error(connection->GetConnection());
      const char* err_state = mysql_sqlstate(connection->GetConnection());
      results.AddLine(Knot(new string("Error Code: " + itoa(err_code))));
      state_str.AppendOwned(err_state, strlen(err_state));
      results.AddLine(state_str);
      err_str.AppendOwned(err, strlen(err));
      results.AddLine(err_str);
      if (num_tries > 1) {
        results.AddLine(Knot(new string("# query tries: " + itoa(num_tries))));
      }
      results.AddLine(Knot(new string("ENDFAILED")));
      WriteResults(results);
    } else {
      // Event ID 3: Query submitted
      if (events_enabled_) {
        WriteEvent(3);
      }
      if (query_log_ != nullptr) {
        (*query_log_) << "[RECEIVED " << timer->Elapsed() << "] "
            << query_string << endl;
      }
      ProcessResults(connection);
      if (query_log_ != nullptr) {
        (*query_log_) << "[COMPLETE " << timer->Elapsed() << "] "
            << query_string << endl;
      }
      if (num_tries > 1) {
        LOG(WARNING) << "Query " << query_string << " required "
                     << num_tries << " attempts before succeeding";
      }
    }
    query_submitted = true;
  }
  delete command_data;
  Done();
}

void QueryHandler::ProcessResults(MySQLConnection* connection) {
  MYSQL_RES* result_set = mysql_use_result(connection->GetConnection());

  CHECK(result_set != nullptr) << "Error processing query:\n"
      << mysql_error(connection->GetConnection());

  MYSQL_FIELD* fields = mysql_fetch_fields(result_set);
  unsigned int num_columns = mysql_field_count(connection->GetConnection());

  MYSQL_ROW row;

  static const char kRowStart[] = "ROW";
  static const int kRowStartLen = strlen(kRowStart);

  static const char kRowEnd[] = "ENDROW";
  static const int kRowEndLen = strlen(kRowEnd);

  Knot row_header;
  row_header.AppendOwned(kRowStart, kRowStartLen);

  Knot row_footer;
  row_footer.AppendOwned(kRowEnd, kRowEndLen);

  StreamingWriter* writer = GetStreamingWriter();
  bool results_started = false;
  bool results_written = false;
  bool dummy_reported = false;
  for (row = mysql_fetch_row(result_set); row != nullptr;
       row = mysql_fetch_row(result_set)) {
    if (!results_started) {
      // Event ID 4: First byte of query result received
      if (events_enabled_) {
        WriteStreamingEvent(writer, 4);
      }
      results_started = true;
    }
    if (!dummy_reported && results_written) {
      // Event ID 5: Dummy event that gets report during results streaming
      if (events_enabled_) {
        WriteStreamingEvent(writer, 5);
      }
      dummy_reported = true;
    }
    LineRawData<Knot> result_row;
    result_row.AddLine(row_header);
    unsigned long *lengths;
    lengths = mysql_fetch_lengths(result_set);
    for (unsigned int i = 0; i < num_columns; ++i) {
      Knot col_data;
      col_data.AppendOwned(row[i], lengths[i]);
      // I think this is the right thing to check for binary data though the
      // docs aren't 100% clear. The other option is fields[i].type ==
      // MYSQL_TYPE_BLOB.
      if (fields[i].flags & BINARY_FLAG) {
        result_row.AddRaw(col_data);
      } else {
        result_row.AddLine(col_data);
      }
    }  
    result_row.AddLine(row_footer);
    Knot final_row;
    result_row.AppendLineRawOutput(&final_row);
    writer->Write(final_row);
    if (!results_written) {
      results_written = true;
    }
  }

  StreamingWriterDone(writer);

  mysql_free_result(result_set);
}

bool QueryHandler::NeedsExpansion(const string& query) const {
  return boost::regex_search(query, *expand_funs_regex_);
}

// The algorihm here is as follows: for each CONTAINED_IN or CONTAINS_STEM call
// we encounter we'll add a join against the relevant index table and we'll
// replace the function call with a "(table.id = main.id and table.col = C and
// table.word = W)". A straight replacement including the parentheses ensures
// that this works correctly with boolean queries or any other kind of nesting.
// Note that we may need to join against the same index table more than once in
// order to support things like "WHERE CONTAINED_IN(A, B) OR CONTAINED_IN(C,
// D)". Thus, each time we replace a function call we add another join and
// another able alias. In some cases we might add more table aliases than
// necessary, but that is safe, even if it's not optimal.
void QueryHandler::ExpandQuery(string* query) const {
  // First break the query into parts. Part 1 contains everything up to the
  // WHERE clause. We'll add more table aliases to this as necessary. Part 2 is
  // the WHERE clause; we'll search and replace function calls here.
  boost::smatch full_stmt_match_result;
  bool matched = boost::regex_match(*query, full_stmt_match_result,
                                    *select_stmt_regex_);
  CHECK(matched) << "SQL select statement regular expression didn't match: "
      << *query;

  // 4: 1 for the whole expression, and 1 for each ()-captured regex part.
  CHECK(full_stmt_match_result.size() == 4);

  int replaced_functions = 0;
  std::ostringstream new_joins;
  std::ostringstream where_clause;
  string::const_iterator cur_where_start = full_stmt_match_result[3].first;
  // Now iterate over all the CONTAINED_IN, CONTAINS_STEM, and WORD_PROXIMITY calls and replace
  // them.
  boost::sregex_iterator mi(full_stmt_match_result[3].first,
                            full_stmt_match_result[3].second,
                            *expand_funs_regex_);
  for (; mi != boost::sregex_iterator(); ++mi) {
    // Copy everything in the where clause from the last replacement up to the
    // one we're about to replace.
    where_clause << string(cur_where_start, (*mi)[0].first);
    boost::smatch fun_match;
    ++replaced_functions;
    string new_table_name("t");
    new_table_name += itoa(replaced_functions);
    // The word (for CONTAINED_IN) or stem (for CONTAINS_STEM) that we should
    // lookup, or the word1, word2 pair for WORD_PROXIMITY.
    // After the following if statements word_or_stem should be enclosed
    // in quotes.
    string word_or_stem;
    string word1;
    string word2;
    string comparison;
    string column;
    string xpath;
    string value;
    bool proximity_ranking = false;
    // CONTAINED IN
    if (regex_match((*mi)[0].first, (*mi)[0].second,
                    fun_match, *contained_in_regex_)) {
      // 0 == the full match, 1 == the column name, and 2 == the quoted string
      // we're looking for.
      CHECK(fun_match.size() == 3);
      new_joins << ", " << kKeywordIndexTableName << " " << new_table_name;
      word_or_stem = string(fun_match[2].first, fun_match[2].second);
      // In the above we don't convert things to lowercase, we assume the SQL
      // command had already done that. Double check!
      DCHECK(std::all_of(word_or_stem.begin(), word_or_stem.end(),
                     [](char x){ return !isalpha(x) || islower(x); }));

    }
    // CONTAINS_STEM
    else if (regex_match((*mi)[0].first, (*mi)[0].second,
    				fun_match, *contains_stem_regex_)) {
      // 0 == the full match, 1 == the column name, and 2 == the quoted string
      // we're looking for.
      CHECK(fun_match.size() == 3);
      new_joins << ", " << kStemsIndexTableName << " " << new_table_name;
      word_or_stem = string(fun_match[2].first, fun_match[2].second);
      word_or_stem = string("'") + Stem(word_or_stem) + "'";
      // In the above we don't convert things to lowercase, we assume the SQL
      // command had already done that. Double check!
      DCHECK(std::all_of(word_or_stem.begin(), word_or_stem.end(),
                     [](char x){ return !isalpha(x) || islower(x); }));

    }
    // WORD_PROXIMITY
    else if(regex_match((*mi)[0].first, (*mi)[0].second,
				fun_match, *word_prox_regex_)) {
        // 0 == the full match, 1 == the column name, 2 == word1,
    	// 3 == word2, 4 == comparison ('< 50')
        CHECK(fun_match.size() == 5);
    	new_joins << ", " << kAlarmsIndexTableName;
    	word1 = string(fun_match[2].first, fun_match[2].second);
    	word2 = string(fun_match[3].first, fun_match[3].second);
    	comparison = string(fun_match[4].first, fun_match[4].second);
    }
    // WORD_PROXIMITY RANKING
    else if(regex_match((*mi)[0].first, (*mi)[0].second,
				fun_match, *prox_ranking_regex_)) {
        // 0 == the full match
        CHECK(fun_match.size() == 1);
        proximity_ranking = true;
    }
    // xml_value
    else if(regex_match((*mi)[0].first, (*mi)[0].second,
				fun_match, *xml_value_regex_)) {
        // 0 == the full match, 1 == the column name (xml),
    	// 2 == path ('//name'), 3 = target value ('Bob')
        CHECK(fun_match.size() == 4);
    	new_joins << ", " << kXmlValueTableName;
    	column = string(fun_match[1].first, fun_match[1].second);
    	xpath = string(fun_match[2].first, fun_match[2].second);
    	value = string(fun_match[3].first, fun_match[3].second);
    }
    else // ERROR
    {
    	CHECK(0) << "Failed to expand query that needed expansion: "
    			<< query;
    }

    // CONTAINED_IN or CONTAINS_STEM
    if (!word_or_stem.empty()) {
    	where_clause << "(" << kMainViewName << ".id = "
    			<< new_table_name << ".id and "
    			<< new_table_name << ".col = '"
    			<< string(fun_match[1].first, fun_match[1].second) << "' and "
    			<< new_table_name << ".word = "
    			<< word_or_stem << ")";
    }
    // WORD_PROXIMITY
    else if (!word1.empty()) {
    	where_clause << "(" << kMainViewName << ".id = "
    			<< kAlarmsIndexTableName << ".id and "
    			<< kAlarmsIndexTableName << ".field = '"
    			<< string(fun_match[1].first, fun_match[1].second) << "' and (("
    			<< kAlarmsIndexTableName << ".word1 = '" << word1 << "' and "
    			<< kAlarmsIndexTableName << ".word2 = '" << word2 << "') or ("
    			<< kAlarmsIndexTableName << ".word1 = '" << word2 << "' and "
    			<< kAlarmsIndexTableName << ".word2 = '" << word1 << "')) and "
    			<< kAlarmsIndexTableName << ".distance " << comparison << ")";
    }
    // xml_value
    else if (!xpath.empty()) {
    	where_clause << "(" << kMainViewName << ".id = "
    			<< kXmlValueTableName << ".id and "
    			<< kXmlValueTableName << ".field = '"
    			<< column << "' and ";
    	// Check for relative or absolute xpath
    	// absolute is /a/b/c/d
    	// relative is //d
    	// thus, if char.at(1) == '/', it's relative
    	if (xpath.at(1) == '/') {
    		// Relative path: ensure path ends with xpath
    		// via LIKE '%xpath'
    		where_clause << kXmlValueTableName << ".path LIKE '%"
    				<< xpath.substr(1) << "'";
    	}
    	else {
    		where_clause << kXmlValueTableName << ".path = '"
    				<< xpath << "'";
    	}
    	where_clause << " and " << kXmlValueTableName << ".value = '"
    			<< value << "')";
    }
    // PROXIMITY RANKING
    else if (proximity_ranking) {
    	where_clause << "ORDER BY " << kAlarmsIndexTableName << ".distance";
    }
    else // ERROR
    {
    	CHECK(0) << "Failed to expand query that needed expansion: "
    			<< query;
    }


    cur_where_start = fun_match[0].second;
  }

  where_clause << string(cur_where_start, full_stmt_match_result[0].second);

  std::ostringstream final_statement;
  string select_clause = string(full_stmt_match_result[1].first,
                                full_stmt_match_result[1].second);
  // We have to replace "select id" with "select main.id" as id is ambiguous
  // after the join. We have to replace "select *" with "select main.*" as we
  // only want the stuff in main to be returned.
  CHECK(select_clause == "id" || select_clause == "*");
  final_statement << "SELECT main." << select_clause
      << " " << string(full_stmt_match_result[2].first,
                       full_stmt_match_result[2].second)
      << new_joins.str() << " " << where_clause.str();

  *query = final_statement.str();
  // Now, if necessary, replace any "id" column references with "main.id" as id
  // by itself is ambiguous given the join.
  boost::smatch id_col_match;
  while (regex_match(*query, id_col_match, *id_replace_regex_)) {
    final_statement.str("");
    final_statement << string(id_col_match[1].first, id_col_match[1].second)
        << "main.id"
        << string(id_col_match[2].first, id_col_match[2].second);
    *query = final_statement.str();
  }
}

boost::regex* QueryHandler::expand_funs_regex_;
boost::regex* QueryHandler::select_stmt_regex_;
boost::regex* QueryHandler::contained_in_regex_;
boost::regex* QueryHandler::contains_stem_regex_;
boost::regex* QueryHandler::id_replace_regex_;
boost::regex* QueryHandler::word_prox_regex_;
boost::regex* QueryHandler::prox_ranking_regex_;
boost::regex* QueryHandler::xml_value_regex_;

// Note that this will *not* match CONTAINED_IN or CONTAINS_STEM like-calls
// enclosed in quotes because ANSI SQL, which is all the test harness will send,
// uses single quotes to sorround strings. Thus, if a CONTAINED_IN or
// CONTAINS_STEM string was enclosed in quotes the quotes in the string literal
// inside the call would have to be escaped for the string to be valid and then
// it woudln't match. For example, 'CONTAINED_IN(A, B)' won't match because B
// isn't in quotes and 'CONTAINED_IN(A, \'B\')' won't match because the quotes
// around B are (correctly) escaped.
//
// This confusing regex gets repeated in all of the following regular
// expressions and is probably worth an explanation:
//
// "'(?:[^']|\\\\')*''"
//
// What we're looking for is a quote character (the ') followed by zero or more
// non-quote characters. That would be:  '[^']*'. However, SQL allows for
// escaped quote characters like \' so we need to accept those as well. Thus we
// use (?:...) which is a non-capturing parantheses to say we'll accept [^']
// not a quote character) or \'. However we have to double the \ character to
// make it count with C escapes and then double it again so it coun't with regex
// escapes.
static const char kExpandFunsRegex[] =
    "CONTAINED_IN\\([^,]+, *'(?:[^']|\\\\')*'\\)|"
    "CONTAINS_STEM\\([^,]+, *'(?:[^']|\\\\')*'\\)|"
	"WORD_PROXIMITY\\(([^,]+), *'((?:[^']|\\\\')*)', *'((?:[^']|\\\\')*)'\\) *((?:=|>|<|>=|<|<=|<>) *\\d+)|"
	"ORDER *BY *WORD_PROXIMITY\\((?:[^,]+), *'(?:(?:[^']|\\\\')*)', *'(?:(?:[^']|\\\\')*)'\\)|"
	"xml_value\\(([^,]+), '([^']+)', '([^']+)'\\)";
// We use this to break apart a SELECT statement and find the places we need to
// be modfiying things. Note that this handles only a limited subset of SQL but,
// as per the test plan, it's all we need to handle.
static const char kSelectStmtRegex[] = "SELECT +(.*) +(FROM .*) +(WHERE .*)";
// These break apart the CONTAINED_IN and CONTAINS_STEM calls. Note that the
// CONTAINED_IN regex captures the string literal including the ' characters
// that surround it while the CONTAINS_STEM captures the literal without the '
// characters. This is so we can pass the literal to the Stem function.
static const char kContainedInRegex[] =
    "CONTAINED_IN\\(([^,]+), *('(?:[^']|\\\\')*')\\)";
static const char kContainsStemRegex[] =
    "CONTAINS_STEM\\(([^,]+), *'((?:[^']|\\\\')*)'\\)";
static const char kWordProxRegex[] =
    "WORD_PROXIMITY\\(([^,]+), *'((?:[^']|\\\\')*)', *'((?:[^']|\\\\')*)'\\) *((?:=|>|<|>=|<|<=|<>) *\\d+)";
static const char kWordProxRankingRegex[] =
	"ORDER BY WORD_PROXIMITY\\((?:[^,]+), *'(?:(?:[^']|\\\\')*)', *'(?:(?:[^']|\\\\')*)'\\)";
static const char kXmlValueRegex[] =
	"xml_value\\(([^,]+), '([^']+)', '([^']+)'\\)";
// Finally, we have to replace any appearance of "id" with "main.id" as id is an
// ambiguous column name after the join. We take care of the case in the SELECT
// clause directly, but id might appear elsewhere in the WHERE clause. This is a
// bit tricky sine id might appear in quotes, in which case it's fine, and it
// might appear in the middle of a word, in which case it's fine. Thus we need
// to find "id" that comes at a column boundry (after "(", ",", or " ") where it
// is preceeded by no quotes or an even number of quotes.
static const char kIdReplaceRegex[] =
    "((?:[^']|'(?:[^']|\\\\')*')+[ (,=])id([, )].*)";

void InitializeQueryHandlerRegex() {
  QueryHandler::expand_funs_regex_ = new boost::regex(
      string(kExpandFunsRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::select_stmt_regex_ = new boost::regex(
      string(kSelectStmtRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::contained_in_regex_ = new boost::regex(
      string(kContainedInRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::contains_stem_regex_ = new boost::regex(
      string(kContainsStemRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::id_replace_regex_ = new boost::regex(
      string(kIdReplaceRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::word_prox_regex_ = new boost::regex(
      string(kWordProxRegex),
      boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::prox_ranking_regex_ = new boost::regex(
	  string(kWordProxRankingRegex),
	  boost::regex::optimize | boost::regex::ECMAScript);

  QueryHandler::xml_value_regex_ = new boost::regex(
	  string(kXmlValueRegex),
	  boost::regex::optimize | boost::regex::ECMAScript);
}

void FreeQueryHandlerRegex() {
  delete QueryHandler::expand_funs_regex_;
  delete QueryHandler::select_stmt_regex_;
  delete QueryHandler::contained_in_regex_;
  delete QueryHandler::contains_stem_regex_;
  delete QueryHandler::id_replace_regex_;
  delete QueryHandler::word_prox_regex_;
  delete QueryHandler::prox_ranking_regex_;
  delete QueryHandler::xml_value_regex_;
}

ADD_INITIALIZER("QueryHandlerRegexInit", &InitializeQueryHandlerRegex);
ADD_FINALIZER("FinalizeQueryHandlerRegex", &FreeQueryHandlerRegex);
