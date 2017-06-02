//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A class for hashing aggregate values.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   ni24039            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_HASH_AGGREGATOR_H_
#define CPP_TEST_HARNESS_COMMON_HASH_AGGREGATOR_H_

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
class HashAggregator : public FutureAggregator<Knot, Knot> {
 public:
  HashAggregator();

  virtual void AddPartialResult(const Knot& data);

 protected:
  Knot Finalize();

 private:
  /// This is the openssl data structure used for calculating hashes.
  EVP_MD_CTX md_ctx_;
};


#endif
