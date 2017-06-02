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

#include "row-hash-aggregator.h"

#include <openssl/md5.h>
#include <string>

using std::string;

// start/end delimiter is what bounds a row entry.
// For results, this is ROW/ENDROW
// For inserts, this is INSERT/ENDINSERT
void RowHashAggregator::AddPartialResult(const Knot& data) {
  switch (state_) {
    case WAITING_FOR_ROW:
      if (data == startdelimiter_) {
        state_ = WAITING_FOR_ID;
      } else {
        CHECK(data == "FAILED");
        results_.Append(data);
        results_.AppendOwned("\n", 1);
        state_ = HANDLING_FAILURE;
      }
      break;
    case WAITING_FOR_ID:
      results_.Append(data);
      state_= COMPUTING_HASH;
      break;
    case COMPUTING_HASH:
      if (data == enddelimiter_) {
        FinalizeHash();
        state_ = WAITING_FOR_ROW;
      } else {
        AddToHash(data);
      }
      break;
    case HANDLING_FAILURE:
      results_.Append(data);
      results_.AppendOwned("\n", 1);
      if (data == "ENDFAILED") {
        LOG(WARNING) << "FAILED message received from SUT:\n" << results_;
        state_ = WAITING_FOR_ROW;
      }
      break;
    default:
      LOG(FATAL) << "This shouldn't ever happen!";
  }
}

void RowHashAggregator::AddToHash(const Knot& data) {
  if (!hash_started_) {
    EVP_DigestInit(&md_ctx_, EVP_md5());
    hash_started_ = true;
  }

  // TODO(odain) This ends up copying the data (though at least it gets copied
  // into small chunks whose size is known in advance). It would be more
  // efficient if we could iterate through the strands and add each strand to
  // the hash directly. That would require adding a strand iterator or something
  // to Knot.
  string data_str;
  data.ToString(&data_str);
  EVP_DigestUpdate(&md_ctx_, data_str.data(), data_str.size());
}

void RowHashAggregator::FinalizeHash() {
  if (hash_started_) {
    hash_started_ = false;
    unsigned char hash_value[EVP_MAX_MD_SIZE];
    unsigned int hash_size;
    EVP_DigestFinal(&md_ctx_, hash_value, &hash_size);
    DCHECK(hash_size < EVP_MAX_MD_SIZE);

    // 2 * hash_size as each byte becomes 2 hex digits. Add one for the initial
    // space and one for the terminating \n
    size_t result_len = 2 * hash_size + 2;
    char* hex_result = new char[result_len];
    hex_result[0] = ' ';
    for (unsigned int i = 0; i < hash_size; ++i) {
      sprintf(hex_result + 2 * i + 1, "%02x", hash_value[i]);
    }
    hex_result[result_len - 1] = '\n';
    results_.Append(hex_result, result_len);
  } else {
    results_.AppendOwned("\n", 1);
  }
}
