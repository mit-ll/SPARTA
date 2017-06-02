//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class  that parses the individual words out of the
//                     notes field. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_NOTES_PARSER_H_
#define CPP_BASELINE_MYSQL_SERVER_NOTES_PARSER_H_

#include <set>
#include <string>

class Knot;

/// This class is used to parse the notes fields into the words they contain. As
/// per the test plan, all characters except the space character and '.' ',' '!'
/// '?' '-' and ';' count as words (so, for example, "it's" is a single word). To
/// use this class, construct and instance and then call Parse on it as often as
/// desired. Note that constructing this class is somewhat expensive so you
/// should re-use the NotesParser if possible.
class NotesParser {
 public:
  /// Note that this sets up an array of valid and invalid characters and is thus
  /// moderately expensive. It is thus best to construct one of these once and
  /// then re-use it.
  NotesParser(const std::set<std::string>& stop_words);

  void Parse(const Knot& data, std::set<std::string>* results) const;

 private:
  /// Starting from start, skip any non-word characters and return the position
  /// of the 1st word character. Returns -1 if the end of the string is reached
  /// before a word character is seen.
  int SkipWordDelims(const std::string& data, int start) const;

  std::set<std::string> stop_words_;
  /// For standard ASCII we only expect character codes 0 through 127. True, we
  /// don't really expect 0 (or 1 for that matter) but in order to make this fast
  /// we want a 1-1 correspondence between the integer value of the character and
  /// it's position in the is_word_char_ array below.
  static const int kNumValidChars = 128;
  /// vector<bool> is "bad" so I'm using an array of bool's here. This array is
  /// such that is_word_char_[c] == true if c is a valid character in a word.
  /// is_word_char_[c] is false for characters like spaces, !, ?, etc. that
  /// delimit word boundaries.
  bool is_word_char_[kNumValidChars];
};


#endif
