//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Various utility functions for MySQL server components. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_UTIL_H_
#define CPP_BASELINE_MYSQL_SERVER_UTIL_H_

#include <set>
#include <string>

/// Reads the stop words list from file_path and inserts the stopwords in
/// stopwords.
void GetStopWords(const std::string& file_path,
                  std::set<std::string>* stopwords);

#endif
