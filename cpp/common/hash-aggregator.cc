//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of RowHashAggregator. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#include "hash-aggregator.h"

#include <openssl/md5.h>
#include <string>

using std::string;

HashAggregator::HashAggregator() {
  EVP_DigestInit(&md_ctx_, EVP_md5());
}

void HashAggregator::AddPartialResult(const Knot& data) {
  // TODO(odain) This ends up copying the data (though at least it gets copied
  // into small chunks whose size is known in advance). It would be more
  // efficient if we could iterate through the strands and add each strand to
  // the hash directly. That would require adding a strand iterator or something
  // to Knot.
  string data_str;
  data.ToString(&data_str);
  EVP_DigestUpdate(&md_ctx_, data_str.data(), data_str.size());
}

Knot HashAggregator::Finalize() {
  unsigned char hash_value[EVP_MAX_MD_SIZE];
  unsigned int hash_size;
  EVP_DigestFinal(&md_ctx_, hash_value, &hash_size);
  DCHECK(hash_size < EVP_MAX_MD_SIZE);

  // 2 * hash_size as each byte becomes 2 hex digits.
  // TODO(njhwang) some weirdness here...result_len had to account for null
  // character or something? do something cleaner here that will still make
  // valgrind happy
  size_t result_len = 2 * hash_size + 1;
  char* hex_result = new char[result_len];
  for (unsigned int i = 0; i < hash_size; ++i) {
    snprintf(hex_result + 2 * i, result_len, "%02x", hash_value[i]);
  }
  string* result_str = new string(hex_result, result_len - 1);
  delete[] hex_result;
  return Knot(result_str);
}
