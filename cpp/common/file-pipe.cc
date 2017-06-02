//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of FilePipe 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 04 May 2012   omd            Original Version
//*****************************************************************

#include "file-pipe.h"

#include <unistd.h>

#include "check.h"

using std::istream;
using std::ostream;

FilePipe::FilePipe() {
  // Create a pipe. file_descriptors_ will hold the input and output file
  // descriptors.
  int file_descriptors[2];
  int ret = pipe(file_descriptors);
  CHECK(ret == 0);

  out_stream_.reset(new FileHandleOStream(file_descriptors[OUTPUT_STREAM_IDX]));
  in_stream_.reset(new FileHandleIStream(file_descriptors[INPUT_STREAM_IDX]));
}

void FilePipe::CloseWriteStream() {
  out_stream_->close();
}

void FilePipe::CloseReadStream() {
  in_stream_->close();
}
