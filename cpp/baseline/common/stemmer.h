//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Takes a set of words and returns a set of stemmed words. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_STEMMER_H_
#define CPP_BASELINE_MYSQL_SERVER_STEMMER_H_

#include <set>
#include <string>

/// Stems all of the words in inputs and returns the set of stemmed words. Note
/// that this assumes that all the words in inputs have already been converted to
/// lower case!
void Stem(const std::set<std::string>& inputs, std::set<std::string>* outputs);

/// Stems a single word.
std::string Stem(const std::string& input);

#endif
