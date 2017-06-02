//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of the Stem method 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************

#include "stemmer.h"

#include <boost/scoped_array.hpp>
#include <cstring>

#include "third-party/stemmer.h"

using namespace std;

void Stem(const std::set<std::string>& inputs, std::set<std::string>* outputs) {
  // The porter algorithm modifies the word to be stemmed *in place* and
  // requires a char*. Thus, this first copies each word into a new char*, stems
  // that, and then copies the result into a string. All the copying is
  // unfortunate, but likely unavoidable.
  set<string>::const_iterator i;
  for (i = inputs.begin(); i != inputs.end(); ++i) {
     outputs->insert(Stem(*i));
  }
}

std::string Stem(const std::string& input) {
  boost::scoped_array<char> to_stem(new char[input.size()]);
  memcpy(to_stem.get(), input.data(), input.size());

  stemmer stem_struct;
  int stemmed_end = stem(&stem_struct, to_stem.get(), input.size() - 1);
  return string(to_stem.get(), stemmed_end + 1);
}
