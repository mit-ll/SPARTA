//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for hashing row values. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_ROW_HASH_AGGREGATOR_H_
#define CPP_TEST_HARNESS_TA1_ROW_HASH_AGGREGATOR_H_

#include "common/aggregating-future.h"

#include <openssl/evp.h>

#include "common/knot.h"

/// This class expects to receive a series of results from a query in the
/// following format:
///
/// ROW
/// id
/// v1
/// v2
/// ...
/// ENDROW
///
/// where id is the id of the row and v1, v2, ... are the values in the other
/// columns of the table. This will also handle cases where all we get back is
/// the id of the row. If we get just the id of the row the value the Future
/// fires with is simple an '\n' delimited list of row id's. However, if the
/// other column values are present as well the future fires with "id <hash>"
/// pairs delimited by '\n' where the hash is some hash function of the values in
/// all the columns *except* the id column.
///
/// The current implementation use the md5 checksum from openssl because it's
/// very fast and plenty robust for our testing purposes. However, users
/// shouldn't assume any particular hash function.
class RowHashAggregator : public FutureAggregator<Knot, Knot> {
 public:
  RowHashAggregator(const char* startdelimiter="ROW",
		  const char* enddelimiter="ENDROW") : startdelimiter_(startdelimiter),
		  enddelimiter_(enddelimiter), state_(WAITING_FOR_ROW),
		  hash_started_(false) {}
  virtual ~RowHashAggregator() {}

  virtual void AddPartialResult(const Knot& data);

 protected:
  Knot Finalize() {
    return results_;
  }

 private:

  /// If hash_started_ is true then we append the current hash to results_ and
  /// set hash_started_ to false. If hash_started_ is false then we must have
  /// received just row id's and there's nothing to append. In that case we
  /// simply append a newline.
  void FinalizeHash();

  /// Add data to the hash. If hash_started_ is false we first initialize the
  /// hash and set hash_started_ to true.
  void AddToHash(const Knot& data);


  /// The marker for the start of a row, typically "ROW" or "INSERT"
  const char* startdelimiter_;
  /// The marker for the end of a row, typically "ENDROW" or "ENDINSERT"
  const char* enddelimiter_;

  Knot results_;

  enum State {
    WAITING_FOR_ROW, WAITING_FOR_ID, COMPUTING_HASH, HANDLING_FAILURE
  };
  State state_;

  /// If true then we've already added some text to the hash. If false and we've
  /// got some data to be hashed we need to re-initialize the hash data
  /// structures first as we haven't yet initialized anything. This gets set to
  /// false in FinalizeHash.
  bool hash_started_;

  /// This is the openssl data structure used for calculating hashes.
  EVP_MD_CTX md_ctx_;
};


#endif
