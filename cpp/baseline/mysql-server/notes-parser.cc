//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NotesParser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************

#include "notes-parser.h"

#include <boost/assign/list_of.hpp>

#include "common/knot.h"
#include "common/string-algo.h"

using namespace std;

NotesParser::NotesParser(const set<string>& stop_words) 
    : stop_words_(stop_words) {
  // The test plan says that everything counts as a regular character excpet the
  // items in the word_delims list below.
  memset(&is_word_char_, true, sizeof(is_word_char_));

  // Note that we're guaranteed that the notes generator won't include any "
  // characters, but other code relies on that fact (we don't try to escape this
  // character when inserting into MySQL) so we add it to word_delims just to be
  // extra-safe.
  vector<unsigned char> word_delims = boost::assign::list_of(' ')('.')(',')
      ('!')('?')('-')(';')('"');

  for (vector<unsigned char>::const_iterator i = word_delims.begin();
       i != word_delims.end(); ++i) {
    is_word_char_[*i] = false;
  }
}

void NotesParser::Parse(const Knot& data, set<string>* results) const {
  string notes;
  data.ToString(&notes);

  int word_start = 0;
  int word_end = 0;
  while (static_cast<size_t>(word_end) < notes.size()) {
    word_start = SkipWordDelims(notes, word_end);
    if (word_start == -1) {
      // Reached the end of the string
      return;
    }

    word_end = word_start + 1;
    while (static_cast<size_t>(word_end) < notes.size()) {
      unsigned char idx = notes[word_end];
      DCHECK(idx < kNumValidChars);
      if (is_word_char_[idx] == false) {
        break;
      }
      ++word_end;
    }
   
    string word =  notes.substr(word_start, word_end - word_start);
    ToLower(&word);
    if (stop_words_.find(word) == stop_words_.end()) {
      results->insert(word);
    }
  }
}

int NotesParser::SkipWordDelims(const string& data, int start) const {
  for (size_t i = start; i < data.size(); ++i) {
    unsigned char idx = data[i];
    DCHECK(idx < kNumValidChars);
    if (is_word_char_[idx]) {
      return i;
    }
  }
  return -1;
}
