//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Oct 2012   omd            Original Version
//*****************************************************************

#include "index-table-insert-builder.h"

#include "common/check.h"
#include "baseline/common/stemmer.h"

#include <cstring>

using std::set;
using std::string;
using std::vector;

IndexTableInsertBuilder::IndexTableInsertBuilder(
    const string& keyword_index_name, const string& stem_index_name,
    const set<string>& stop_words)
    : keyword_index_name_(keyword_index_name),
      stem_index_name_(stem_index_name), parser_(stop_words) {
}

void IndexTableInsertBuilder::GetInsertStatements(
    const string& row_id, const string& field_name, const Knot& data,
    string* keyword_statement, string* stem_statement) const {
  set<string> words;
  parser_.Parse(data, &words);

  if (words.size() == 0) {
    return;
  }
  *keyword_statement = GetSingleStatement(
          keyword_index_name_, row_id, field_name, words);

  set<string> stems;
  Stem(words, &stems);
  DCHECK(stems.size() > 0);

  *stem_statement = GetSingleStatement(
          stem_index_name_, row_id, field_name, stems);
}

string IndexTableInsertBuilder::GetSingleStatement(
    const std::string& index_table, const string& row_id,
    const std::string& column, const std::set<std::string>& items) const {
  const char kInsertStatementBegin[] = "INSERT into ";
  // Note, this hard codes the format of our index tables. I think, in this
  // situation, that's OK.
  const char kInsertStatementFieldPart[] = " (id, col, word) VALUES ";

  DCHECK(items.size() > 0);
  // First figure out the length of the insert statment so we can reserve space
  // for it.
  int statement_length = strlen(kInsertStatementBegin) +
      strlen(kInsertStatementFieldPart);
  statement_length += index_table.size();

  // for each item we'll have the string "(row_id, col_name, word), ". The
  // lengths of all parts except the word is fixed so we compute how many we'll
  // have and what all that overhead will be here.

  // All statements but 1 include the ", " after them. We'll assume they all
  // have it as allocating 2 extra chars is no big deal but getting this wrong
  // and allocating too little memory is really expensive and fairly invisible.
  statement_length += items.size() * 2;
  // 4 characters for quote characters around col_name and word, 4 characters
  // for the ", " following row_id and col_name, and 2 characters for the "()".
  statement_length += items.size() * (4 + 4 + 2);
  // The column name and id string get repeated for each row.
  statement_length += items.size() * (column.size() + row_id.size());
  // Finally, add up the lengths of all the individual items.
  set<string>::const_iterator item_it;
  for (item_it = items.begin(); item_it != items.end(); ++item_it) {
    statement_length += item_it->size();
  }

  string result;
  result.reserve(statement_length);

  // Build the statement
  result = kInsertStatementBegin + index_table + kInsertStatementFieldPart;

  // This gets repeated a bunch, so save and re-use it.
  string values_begin = "(" + row_id + ", '" + column + "', ";

  item_it = items.begin();
  // Here we enclose the string with double quotes. ANSI SQL says that string
  // literals are surrounded by single quotes, but then we'd have to escape the
  // strings which is time consuming and makes the query string longer thus
  // eliminating the benfit of the resize() call above. Since MySQL accepts
  // double quotes and our notes fields should contain no other characters that
  // require quoting we'll take the easy road.
  result += values_begin + "\"" + *item_it + "\")";
  ++item_it;
  for (; item_it != items.end(); ++item_it) {
    result += ", " + values_begin + "\"" + *item_it + "\")";
  }
  return result;
}
