//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Tests SpawnSUT function.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   njh            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE SpawnSUTTest
#include <boost/assign/list_of.hpp>

#include "root-mode-command-sender.h"
#include "numbered-command-sender.h"
#include "generic-numbered-command.h"
#include "sut-protocol-stack.h"
#include "spawn-sut.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using boost::assign::list_of;
using namespace std;

// The SET command uses a single integer parameter to specify how many times a
// GO response should be sent in the numbered results. For example:
//  - Command sender sends:
//      COMMAND 0
//      SET 3
//      ENDCOMMAND
//  - Command receiver responds:
//      RESULTS 0
//      GO
//      GO
//      GO
//      ENDRESULTS
class SetCommand : public GenericNumberedCommand {
 public:
  SetCommand(NumberedCommandSender* nc)
      : GenericNumberedCommand("SET", nc) {}

 private:
  // This simply appends data, which should contain the number of GO lines to
  // request, to the command name and returns the full command in output. Upon
  // returning, output should contain something like "SET n".
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output) {
    DCHECK(data.Size() == 1);
    DCHECK(!data.IsRaw(0));
    // TODO(njhwang) check that data is an integer
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

      // Set up numbered command senders.
      DCHECK(GetNumberedCommandSender() != nullptr);
      set_command_.reset(new SetCommand(GetNumberedCommandSender()));

      // Set up root command sender.
      root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
      GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);
    }

  private:
    std::unique_ptr<SetCommand> set_command_;
    // These are owned by this SUTProtocolStack ProtocolExtensionManager, so no
    // need to manually free them.
    RootModeCommandSender* root_mode_command_sender_;
    NumberedCommandSender* nc_sender_;
};

BOOST_AUTO_TEST_CASE(SpawnSUTWorks) {
  // Number of times "GO" will be sent by SUT.
  const int num_reps = 3; 
  EventLoop event_loop;
  SampleSUTProtocolStack protocol_stack;
  int sut_stdin_read_fd;
  int sut_stdout_write_fd;
  int command_num = 0;

  // Set up the function that will set up the notional SUT's pipes.
  auto pipe_fun = [&](int* sut_stdin_write_fd, int* sut_stdout_read_fd) {
    SetupPipes(sut_stdout_read_fd, &sut_stdout_write_fd,
               &sut_stdin_read_fd, sut_stdin_write_fd);
    // SpawnSUT needs this to return an integer representing the PID of what
    // would be the child process. We return 0 here, but it won't be used for
    // anything since we won't ask the protocol stack to wait for the fake child
    // process to terminate.
    return 0;
  };

  // Spawn the notional SUT and build its protocol stack.
  SpawnSUT(pipe_fun, "", false, &event_loop, nullptr, nullptr, 
      &protocol_stack, nullptr);

  event_loop.Start();

  // Set up access to the notional SUT's stdin/out.
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  // Perform command sequence. SUT output is simulated by writing to
  // sut_output_stream while test harness output is simulated by using
  // protocol_stack's API. SUT input is verified via VerifyIStreamContents. Note
  // that test harness input is not currently verified by this test.
  LOG(DEBUG) << "SUT sending READY...";
  sut_output_stream << "READY" << endl;
  protocol_stack.WaitUntilReady();

  LOG(DEBUG) << "TH sending COMMAND...";
  LineRawData<Knot> command_data;
  command_data.AddLine(Knot(new string(itoa(num_reps))));
  protocol_stack.GetSetCommand()->Schedule(command_data);
  VerifyIStreamContents(list_of("COMMAND " + itoa(command_num))
                               ("SET " + itoa(num_reps))("ENDCOMMAND"),
                        &sut_input_stream);

  LOG(DEBUG) << "SUT sending RESULTS...";
  sut_output_stream << "RESULTS " << command_num << endl;
  for (int i = 0; i < num_reps; i++) {
    sut_output_stream << "GO" << endl;
  }
  sut_output_stream << "ENDRESULTS" << endl;
  sut_output_stream << "READY" << endl;
  protocol_stack.WaitUntilReady();

  LOG(DEBUG) << "TH sending SHUTDOWN...";
  protocol_stack.GetRootModeCommandSender()->SendCommand("SHUTDOWN");
  VerifyIStreamContents(list_of(string("SHUTDOWN")), &sut_input_stream);
  sut_output_stream << "DONE" << endl;
  // This final READY/wait sequence is done to ensure protocol_stack receives
  // all of the notional SUT's output before event_loop terminates.
  sut_output_stream << "READY" << endl;
  sut_output_stream.close();
  protocol_stack.WaitUntilReady();
  event_loop.ExitLoopAndWait();
}
