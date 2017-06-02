//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A protocol extension for handling numbered commands. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_NUMBERED_COMMAND_RECEIVER_H_
#define CPP_COMMON_NUMBERED_COMMAND_RECEIVER_H_

#include "extensible-ready-handler.h"

#include <functional>
#include <string>
#include <map>

#include "common/line-raw-data.h"
#include "common/check.h"

/// This file contains two classes NumberedCommandReceiver and
/// NumberedCommandHandler. NumberedCommandReceiver is a protocol extension that
/// handles all numbered commands. It takes care of tracking the command number
/// and sending the appropriate RESULTS response but uses NumberedCommandHandler
/// objects to handle specific commands. For example, The TA1 server must be able
/// to insert data but this can be done asynchronously so INSERT commands are
/// sent inside "COMMAND n" "ENDCOMMAND" pairs. The NumberedCommandReceiver
/// handles the "COMMAND n" and "ENDCOMMAND" parts and makes sure the results of
/// the insert are communicated inside an "RESULTS n"/"ENDRESULTS" pair. The
/// INSERT itself is handled by a NumberedCommandHandler subclass that handles
/// inserts.
///
/// The NumberedCommandReceiver buffers all data between COMMAND n and ENDCOMMAND
/// into a LineRawData object. It then looks at the first token on the 1st line
/// following "COMMAND n" to determine which NumberedCommandHandler subclass
/// handles the command. It constructs an instance of that class and calls
/// Execute on it. Execute should return quickly but it need not actually
/// complete the command. Instead Execute can simply schedule the command to be
/// handled on another thread or something. When the command is complete the
/// NumberedCommandHandler should write the results by calling WriteResults.  No
/// need to worry about the command number and such - WriteResults will ensure
/// that "RESULTS n\n" is written to the stream before returning the object.
/// After all the results have been written the user should call Done(), which
/// lets NumberedCommandReceiver know that the command is no longer outstanding
/// and it frees the object. Since the object is freed in Done() that should be
/// the last method called.
///
/// Subclasses of this handle specific commands.
class NumberedCommandHandler {
 public:
  virtual ~NumberedCommandHandler() {}

  /// The following overloaded methods will write the given data to the results
  /// stream after wrapping it in a RESULTS n/ENDRESULTS pair with the
  /// appropriate value for n.
  void WriteResults(const LineRawData<Knot>& data);
  /// For simple string literal constants. This does *not* take ownership of the
  /// char*. The lifetime of the char* must be long enough to guarantee that the
  /// data gets written out before the char* goes out of scope. For string
  /// literals that's fine, but in general we need to be careful!
  ///
  /// data is assumed to end in a '\n' if it conforms to LineRawData protocol.
  void WriteResults(const char* data);
 
  /// Instead of WriteResults, users may request a StreamingWriter so results can
  /// be streamed as they arrive. In this case the "RESULTS n\n" part will have
  /// been written to the returned writer when it is returned and the caller must
  /// call StreamingWriterDone() to have ENDRESULTS written, etc.
  StreamingWriter* GetStreamingWriter();
  void StreamingWriterDone(StreamingWriter* writer);

  /// Writes an EVENTMSG to the current write queue. Optionally takes a string of
  /// additional information about the event. Takes ownership of info, if
  /// specified.
  void WriteEvent(int event_id, std::string* info = nullptr);
  /// Writes an EVENTMSG in line raw format to the provided StreamingWriter.
  /// Takes ownership of info, if specified.
  void WriteStreamingEvent(StreamingWriter* writer, 
                           int event_id, 
                           std::string* info = nullptr);

  /// This should be the *last* thing a NumberedCommandHandler does. The
  /// NumberedCommandHandler will delete the object after this is called.
  void Done() {
    command_done_callback_();
    delete this;
  }

  /// This is called by NumberedCommandHandler. Once this is called the subclass
  /// should make sure the command gets executed and that WriteResults and Done
  /// get called when the command is complete.
  ///
  /// This object should take ownership of command_data and free it when done.
  virtual void Execute(LineRawData<Knot>* command_data) = 0;
 private:
  /// These 3 methods are called immeddiately after object construction by
  /// NumberedCommandReceiver to set up the class. We could pass these via the
  /// constructor but each subclass has a different constructor (e.g. the
  /// QueryHandler takes a pointer to the ObjectThreads pool it will use to
  /// execute queries) so each subclass would have to write boilerplate to accept
  /// these parameters and pass them to the base class. This way each subclass is
  /// simple and the subclass is guaranteed that Execute won't be called on it
  /// until the class is all set.
  void SetCommandDoneCallback(std::function<void ()> command_done_callback) {
    command_done_callback_ = command_done_callback;
  }
  void SetWriteQueue(WriteQueue* queue) {
    write_queue_ = queue;
  }
  void SetCommandNumber(int command_number) {
    command_number_ = command_number;
  }
  friend class NumberedCommandReceiver;

  /// Called by all variants of WriteResults to actually send the data.
  void SendResults(Knot* data);

  WriteQueue* write_queue_;
  boost::function<void ()> command_done_callback_;
  int command_number_;
};

/// NumberedCommandReceiver::AddHandler takes a token NCHConstructor pair. When
/// the token is seen a NumberedCommandHandler is constructed by calling one of
/// these.
typedef boost::function<NumberedCommandHandler* ()> NCHConstructor;

/// The extension for handling numbered commands.
class NumberedCommandReceiver : public ProtocolExtension {
 public:
  /// Results are written to output_queue. This class does not take ownership
  /// of output_queue.
  NumberedCommandReceiver(WriteQueue* output_queue);
  virtual ~NumberedCommandReceiver();
  /// This indicates that when the 1st token on the 1st line following "COMMAND
  /// n" is trigger_token the handler should call handler_constructor to get an
  /// instance of a NumberedCommandHandler and call Execute on it to handle the
  /// actual command.
  void AddHandler(const std::string& trigger_token,
                  NCHConstructor handler_constructor);
  /// Returns the number of pending commands.
  int NumPendingCommands();

  /// Blocks until all pending numbered commands have produced results.
  void WaitForAllCommands();
  /// Overrides from ProtocolExtension.
  virtual void LineReceived(Knot data);
  virtual void RawReceived(Knot data);
  virtual void OnProtocolStart(Knot line);
 private:
  LineRawToOutputHandler* LROutputCallback(int command_number);
  void CommandDoneCallback();
  /// Figure out which NumberedCommandHandler subclass should handle the current
  /// data, construct one and call Execute() on it.
  void DispatchCommand();

  WriteQueue* output_queue_;
  std::map<const std::string, NCHConstructor> handler_map_;
  int pending_commands_;
  /// Guards pending_commands_.
  boost::mutex pending_commands_tex_;
  /// Condition fires when all pending commands have completed.
  boost::condition_variable all_commands_done_cond_;
  /// cur_data_ is the data we have received so far between the "COMMAND n" and
  /// "ENDCOMMAND" pairs. 
  std::auto_ptr<LineRawData<Knot> > cur_data_;
  /// cur_command_number_ is the number (i.e. the n in "COMMAND n") of the
  /// command we're working on currently.
  int cur_command_number_;
};

#endif
