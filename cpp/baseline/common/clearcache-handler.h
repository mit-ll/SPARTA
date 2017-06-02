//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A handler for the CLEARCACHE command. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_MYSQL_CLIENT_CLEARCACHE_HANDLER_H_
#define CPP_BASELINE_MYSQL_CLIENT_CLEARCACHE_HANDLER_H_

#include "common/protocol-extension-manager.h"

class WriteQueue;

/// The baseline doesn't need to do anything in response to a CLEARCACHE command
/// except send back DONE. This does that. Note that this is a root mode command
/// so this inherits from ProtocolExtension rather than NumberedCommandHandler.
class ClearCacheHandler : public ProtocolExtension {
 public:
  ClearCacheHandler(WriteQueue* write_queue) : write_queue_(write_queue) {}

  virtual ~ClearCacheHandler() {}
  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot data);
  virtual void RawReceived(Knot data);

 private:
  WriteQueue* write_queue_;
};

#endif
