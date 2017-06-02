//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Causes the server to run the VERIFY command. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_VERIFY_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_VERIFY_SCRIPT_H_

#include <memory>

#include "common/knot.h"
#include "common/line-raw-data.h"
#include "test-harness/common/test-script.h"

class VerifyCommand;
class GeneralLogger;

/// A very simple script that does nothing but send the VERIFY command for a
/// single row id.
class VerifyScript : public TestScript {
 public:
  /// Constructs a verify script that will send a verify command for row_id to
  /// the SUT. row_id is assumed to consist of just a single line (perhaps
  /// after the LineRawData has has Set*Offset called on it) with the row id.
  /// This is an odd way to pass the row id, but given the way this is
  /// constructed it's actually the most convenient. This takes ownership of
  /// row_id.
  VerifyScript(LineRawData<Knot>* row_id,
               LineRawData<Knot>* mod_id,
               VerifyCommand* verify_command,
               GeneralLogger* logger);
  virtual ~VerifyScript() {}

  virtual void Run();

 private:
  std::unique_ptr<LineRawData<Knot> > row_id_;
  std::unique_ptr<LineRawData<Knot> > mod_id_;
  VerifyCommand* verify_command_;
  GeneralLogger* logger_;
};

/// Functor to construct a verify script if one is recieved over the network
/// via a RUNSCRIPT command.
class VerifyScriptFactory {
 public:
  VerifyScriptFactory(VerifyCommand* verify_command,
                      GeneralLogger* logger)
      : verify_command_(verify_command),
        logger_(logger) {}

  TestScript* operator()(const LineRawData<Knot>& command_data);

 private:
  VerifyCommand* verify_command_;
  GeneralLogger* logger_;
};

#endif
