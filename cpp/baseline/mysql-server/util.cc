//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Oct 2012   omd            Original Version
//*****************************************************************

#include "util.h"

#include "common/check.h"
#include "common/safe-file-stream.h"

using namespace std;

void GetStopWords(const std::string& file_path,
                  std::set<std::string>* stopwords) {
  SafeIFStream stopwords_file(file_path.c_str());
  while (stopwords_file.good()) {
    string s_word;
    getline(stopwords_file, s_word);
    stopwords->insert(s_word);
  }
  CHECK(stopwords_file.eof()) << "Error reading stop words file.";
}
