//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An event loop for handling non-blocking writes to files. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_WRITE_EVENT_LOOP_H_
#define CPP_COMMON_WRITE_EVENT_LOOP_H_

#include "event-loop-base.h"

#include <map>

#include "conditions.h"
#include "future.h"
#include "host-port.h"
#include "knot.h"

////////////////////////////////////////////////////////////////////////////////
// WriteEventLoop
////////////////////////////////////////////////////////////////////////////////

class WriteQueue;
class NetworkConnection;
class NetworkClient;
struct ConnectionStatus;

class EventLoop;

/// As noted in event-loop.h we want to have a separate thread for reads and
/// writes. This is the event loop that manages all writes. The bulk of the heavy
/// lifting is done by the WriteQueue class defined below.
class WriteEventLoop : public EventLoopBase {
 public:
  WriteEventLoop() {}
  virtual ~WriteEventLoop();

  /// Returns a WriteQueue for the given file handle. In order to ensure that
  /// multiple writes from different threads don't get interleaved all writes
  /// should be made through this object. Multiple calls to this method with the
  /// same file descriptor will return the same WriteQueue. Caching the
  /// WriteQueue is recommended as this function requires us to look up the queue
  /// for a given file handle which can be expensive. The WriteEventLoop
  /// maintains ownership of all WriteQueue's and will free them in it's
  /// destructor.
  WriteQueue* GetWriteQueue(int file_descriptor);

 private:
  friend class WriteQueue;
  /// A pending network connection is complete when the socket becomes writable
  /// so these functions use the WriteEventLoop.
  friend class NetworkClient;

  /// Map from file handle to WriteQueue for the file handle.
  std::map<int, WriteQueue*> write_queue_map_;
};

////////////////////////////////////////////////////////////////////////////////
// WriteQueue
////////////////////////////////////////////////////////////////////////////////

class StreamingWriter;

/// The WriteQueue class. See comments in event-loop.h for usage.
class WriteQueue {
 public:
  virtual ~WriteQueue();
  /// Returns true on success. Returns false if the output queue is full (e.g.
  /// the total number of pending bytes exceeds the maximum allowed number of
  /// pending bytes). If blocking is preferable use WriteWithBlock. Note that
  /// this will not attempt to write the output if it can't be 100% sure that it
  /// will eventually succeed (otherwise the performer might receive partial
  /// output and a corrupt protocol) thus this may return false when a
  /// WriteWithBlock would succeed without blocking.  Takes ownership of to_write
  /// and frees it *unless* this returns false in which case the caller must
  /// manage the memory.
  bool Write(Knot* to_write);

  /// Similar to Write() except instead of returning false if the queue is full
  /// it blocks until there is room on the queue. Takes ownership of to_write.
  void WriteWithBlock(Knot* to_write);

  /// Returns the number of bytes that are in the output queue.
  int BytesPending() const;

  /// Returns the number of "items" in the output queue. An item is the data
  /// passed to a Write() call. Note that an item that has been partially, but
  /// not completely, written to the stream counts as an item.
  int ItemsPending() const;

  /// Blocks until ItemsPending() == 0.
  void WaitForPendingItems() const;

  /// How many threads are currently blocked trying to write?
  int NumBlockedThreads() const;

  /// Asks the write queue to log every byte written out to the given ostream.
  /// This obviously affects performance, but it helps with debugging too.
  void SetDebugLoggingStream(std::ostream* log_stream) {
    logging_stream_ = log_stream;
  }

  /// This call blocks until all data/streaming writers before it in the output
  /// queue have been fulfilled. When they've been fulfilled this returns a
  /// StreamingWriter. The user can then use that to output multiple data items.
  /// Note that on return the user holds a lock on the WriteQueue which is not
  /// released until the writer is freed. Thus, users should write as fast as
  /// possible and then free the StreamingWriter.
  StreamingWriter* GetStreamingWriter();

  /// Change the maximum buffer size.
  void SetMaximumPendingBytes(int new_max) {
    max_pending_bytes_ = new_max;
  }

 private:
  /// An entry in the queue of items to write. Indicates we need to write
  /// substr(output_item, output_offset). If output_item == nullptr that means
  /// this is actually a placeholder for a StreamingWriter and it will be removed
  /// from the queue later via a call to StreamingWriterDone.
  struct OutputQueueEntry {
    OutputQueueEntry(Knot* oi, Knot::iterator start_it,
                     SimpleCondition<bool>* notify_cond)
        : output_item(oi), output_start_it(start_it), done_cond(notify_cond),
          is_streaming_writer(false) {}
    OutputQueueEntry(Knot* oi, Knot::iterator start_it,
                     SimpleCondition<bool>* notify_cond,
                     bool streaming_writer)
        : output_item(oi), output_start_it(start_it), done_cond(notify_cond),
          is_streaming_writer(streaming_writer) {}
    /// Can't use an auto_ptr here as those aren't allowed in STL containers.
    const Knot* output_item;
    Knot::iterator output_start_it;
    /// If a thread is waiting for the write to complete this will be non-null.
    /// It will be signaled when the write is done.
    SimpleCondition<bool>* done_cond;
    /// If true, this item is for a streaming writer. That behaves differently.
    /// Most importantly, this isn't removed from the queue until the
    /// StreamingWriter indicates it is OK to do so. See StreamingWriter for
    /// details.
    bool is_streaming_writer;
  };

  /// Private constructor. Only WriteEventLoop can construct one of these.
  WriteQueue(WriteEventLoop *parent, int file_descriptor);
  friend class WriteEventLoop;

  /// Called by a StreamingWriter's destructor to indicate that all writes are
  /// done and other items in the queue can proceed.
  void StreamingWriterDone();
  friend class StreamingWriter;

  /// Tries to write all the data in to_write from start_it to to_write.end().
  /// Returns an iterator pointing to the 1st character *not* written or
  /// to_write.end() if all the data was written.
  Knot::iterator WriteItem(const Knot* to_write, Knot::iterator start_it);
  /// Similar to WriteItem except this also checks the queue and will not try to
  /// write the item if there is anything in the queue (lest the ordering
  /// guarantee be violated).
  Knot::iterator TryWriteImmediate(Knot* to_write);
  /// Add an entry to the queue so that the data between start_it and
  /// to_write.end() will be written to the file as soon as possible. If
  /// notify_cond is not null it will be notified when the write is complete.
  /// This does not take ownership of notify_cond.
  ///
  /// Note: this must take a *pointer* to a Knot or the iterator would no longer
  /// be valid. That is why WriteItem and TryWriteItem also take a pointer to a
  /// Knot.
  void QueueWrite(Knot* to_write, Knot::iterator start_it,
                  SimpleCondition<bool>* notify_cond);
  void QueueWrite(const OutputQueueEntry& entry);
  /// This gets called by libevent when the file handle is writable. Since
  /// libevent is C this must be static and we have no flexibility in the
  /// function signature. The void* parameter will be a pointer to the WriteQueue
  /// that needs to handle the event.
  static void FileHandleWriteableCallback(int file_descriptor, short event_type,
                                         void* write_queue_ptr);
  /// Called by FileHandleWriteableCallback.
  void HandleCallback();
  /// Processes the output queue writing as many items as it can.
  void ProcessOutputQueue();

  /// Write() returns false if adding the new data to the output queue would
  /// cause there to be more than this many bytes in the queue.
  static const int kDefaultMaxPendingBytes = 10 << 20; /// 20 MB
  WriteEventLoop* parent_;
  int file_descriptor_;
  /// The libevent struct event* that will cause this to be notified when the
  /// file handle become writable. We allocate this once and keep re-using it.
  event* writeable_event_;

  /// data_tex_ guards all variables below this point.
  mutable boost::mutex data_tex_;
  /// If true, we've already registered with WriteEventLoop to be notified when
  /// the file is writable so no need to do it again.
  bool writeable_event_registered_;
  /// The output queue. We try to maintain fewer than kMaxPendingBytes bytes of
  /// data here. However, if a thread calls WriteWithBlock and the queue is full
  /// we still queue up that data. However, since that thread then blocks it
  /// can't continue to add items. Thus, the size of the queue is bound by
  /// kMaxPendingBytes plus up to one entry per writing thread.
  std::deque<OutputQueueEntry> output_queue_;
  /// The sum of the bytes still to be sent for all items in the queue
  int pending_bytes_;
  /// The number of thread blocked waiting to write.
  int num_blocked_threads_;
  /// A condition variable indicating that there are no items pending.
  mutable boost::condition_variable no_items_pending_cond_;
  /// If not-null all output will be logged to the given stream.
  std::ostream* logging_stream_;
  int max_pending_bytes_;

  /// When we're trying to write to a file, the "regular way" or via
  /// StreamingWriter, we may alternate between having an EV_WRITE event
  /// registered and not having such an event (for example, when libevent fires
  /// indicating that the file handle is writable we now don't have any event
  /// registered though we might again register an event if we can't write the
  /// remainder of the data). In order to keep libevent from exiting the loop too
  /// early we Add() this fake event when output_queue_size() > 0 and Fire() it
  /// when the output_queue_.size() becomes 0.
  std::unique_ptr<FakeEvent> pending_writes_event_;
};

////////////////////////////////////////////////////////////////////////////////
// StreamingWriter
////////////////////////////////////////////////////////////////////////////////

/// This behaves like a *blocking* output stream. This outputs to the same
/// location (or locations if there's a debug log) as the WriteQueue that
/// constructed it. It holds a lock on the WriteQueue so that no other writes may
/// proceed for the lifetime of this object. It is generally used to write very
/// large result sets from the baseline to the test harness without having to
/// buffer them first.  The correct use pattern is to retrieve an object via
/// WriteQueue::GetStreamingWriter, use it as soon as possible and as quickly as
/// possible, and then free it immeditately so that other writes may proceed.
///
/// Design description: only need to read this if you're trying to figure out how
/// this works with the WriteQueue's output_queue_ and such:
///
/// GetStreamingWriter puts an OutputQueueEntry on the output_queue_ that has
/// is_streaming_writer set to true. The ProcessOutputQueue doesn't ever remove
/// these from the queue thus ensuring that all other writes and attempts to get
/// a streaming writer are queued behind this. To get a writer such an entry is
/// put on the queue with output_item == nullptr but a non-null done_cond. When
/// ProcessOutputQueue encounters this item it fires done_cond thus waking the
/// waiting thread and returning a StreamingWriter to it. When the
/// StreamingWriter wants to write it just modifies the OutputQueueEntry at the
/// head of the output_queue_ (it must be at the head or there wouldn't be a
/// StreamingWriter instance) by setting output_item to point to the data it
/// wants to write. We then use the normal processing methods to write the data
/// except that the OutputQueueEntry isn't removed from the output_queue_ (since
/// is has is_streaming_writer == true). When the StreamingWriter gets destroyed
/// it removes it's OutputQueueEntry from the output_queue_ and processing then
/// proceeds like normal.
class StreamingWriter {
 public:
  virtual ~StreamingWriter();

  /// BLOCKS until to_write has been written to the underlying file descriptor.
  void Write(const Knot& to_write);

 private:
  StreamingWriter(WriteQueue* parent, std::ostream* logging_stream);
  friend class WriteQueue;


  WriteQueue* parent_;
  int fd_;
  std::ostream* logging_stream_;
};

#endif
