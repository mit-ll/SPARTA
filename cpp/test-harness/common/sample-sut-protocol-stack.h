//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Protocol stack representing a sample SUT test harness
//                     protocol stack
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   njh            Original Version
//*****************************************************************

#include "root-mode-command-sender.h"
#include "numbered-command-sender.h"
#include "generic-numbered-command.h"
#include "sut-protocol-stack.h"

/// The SET command uses a single integer parameter to specify how many times a
/// GO response should be sent in the numbered results. For example:
///  - Command sender sends:
///      COMMAND 0
///      SET 3
///      ENDCOMMAND
///  - Command receiver responds:
///      RESULTS 0
///      GO
///      GO
///      GO
///      ENDRESULTS
class SetCommand : public GenericNumberedCommand {
 public:
  SetCommand(NumberedCommandSender* nc)
      : GenericNumberedCommand("SET", nc) {}

 private:
  /// This simply appends data, which should contain the number of GO lines to
  /// request, to the command name and returns the full command in output. Upon
  /// returning, output should contain something like "SET n".
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output) {
    DCHECK(data.Size() == 1);
    DCHECK(!data.IsRaw(0));
    /// TODO(njhwang) check that data is an integer
    output->Append(new std::string(GetCommandName() + " "));
    data.AppendLineRawOutput(output);
  }
};

class SampleSUTProtocolStack : public SUTProtocolStack {
  public:
    SampleSUTProtocolStack() {}

    virtual ~SampleSUTProtocolStack() {}

    SetCommand* GetSetCommand() {
      return set_command_.get();
    }

    RootModeCommandSender* GetRootModeCommandSender() {
      return root_mode_command_sender_;
    }

    NumberedCommandSender* GetNumberedCommandSender() {
      return nc_sender_;
    }

  protected:
    virtual void SetupCommands() {
      DCHECK(GetReadyMonitor() != nullptr);
      nc_sender_ = new NumberedCommandSender(GetReadyMonitor());
      GetProtocolManager()->AddHandler("RESULTS", nc_sender_);

      /// Set up numbered command senders.
      DCHECK(GetNumberedCommandSender() != nullptr);
      set_command_.reset(new SetCommand(GetNumberedCommandSender()));

      /// Set up root command sender.
      root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
      GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);
    }

  private:
    std::unique_ptr<SetCommand> set_command_;
    /// This is automatically freed, so no need to manually free it.
    RootModeCommandSender* root_mode_command_sender_;
    NumberedCommandSender* nc_sender_;
};
