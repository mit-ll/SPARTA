//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of WriteEventLoop
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************

#include "write-event-loop.h"

#include <fcntl.h>

using std::map;

////////////////////////////////////////////////////////////////////////////////
// WriteEventLoop
////////////////////////////////////////////////////////////////////////////////

WriteEventLoop::~WriteEventLoop() {
  map<int, WriteQueue*>::iterator j;
  for (j = write_queue_map_.begin(); j != write_queue_map_.end(); ++j) {
    delete j->second;
  }
}

WriteQueue* WriteEventLoop::GetWriteQueue(int file_descriptor) {
  map<int, WriteQueue*>::iterator wqi = write_queue_map_.find(file_descriptor);
  if (wqi == write_queue_map_.end()) {
    WriteQueue* wq = new WriteQueue(this, file_descriptor);
    write_queue_map_.insert(std::make_pair(file_descriptor, wq));
    return wq;
  } else {
    return wqi->second;
  }
}

////////////////////////////////////////////////////////////////////////////////
// WriteQueue Implementation
////////////////////////////////////////////////////////////////////////////////

WriteQueue::WriteQueue(WriteEventLoop* parent, int file_descriptor)
    : parent_(parent), file_descriptor_(file_descriptor),
      writeable_event_registered_(false), pending_bytes_(0),
      num_blocked_threads_(0), logging_stream_(NULL), 
      max_pending_bytes_(kDefaultMaxPendingBytes),
      pending_writes_event_(new FakeEvent(parent_->GetEventBase())) {
  // ensure the file handle is in O_NONBLOCK mode. Calling write() with a
  // regular handle is a blocking operation. With a handle in O_NONBLOCK it
  // will write as much as possible before blocking and then return. That
  // allows us to free up the event loop to handle other events. The 1st call
  // here gets the current flags, the 2nd ensures O_NONBLOCK is set.
  int cur_flags = fcntl(file_descriptor_, F_GETFL);
  if ((cur_flags & O_NONBLOCK) == 0) {
    fcntl(file_descriptor_, F_SETFL, cur_flags | O_NONBLOCK);
  }

  // Set up the event we'll want to register. Note that the event is not
  // persistent as a file handle may well be writable even if we have
  // nothing to write to it. Thus we only register this event when we want to
  // know if the file handle has become writable when it wasn't before and we
  // have data to write.
  writeable_event_ =
      event_new(parent_->GetEventBase(), file_descriptor_, EV_WRITE,
                &WriteQueue::FileHandleWriteableCallback, this);
}

WriteQueue::~WriteQueue() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  CHECK(output_queue_.size() == 0) << "WriteQueue destroyed but there "
      << "were still " << output_queue_.size() << " unwritten items";
  // We have to free the FakeEvent before the event_base gets freed so we do it
  // here explicitly.
  pending_writes_event_.reset();
  event_free(writeable_event_);
}

// Note that this does *NOT* aquire the data_tex_ mutex. Whatever methods call
// it *must* be holding the mutex. (Unfortunately boost::mutex doesn't seem to
// provide a way to check that a mutex is held so we can't put a CHECK here).
Knot::iterator WriteQueue::WriteItem(
    const Knot* to_write, Knot::iterator start_it) {
  if (logging_stream_ == NULL) {
    return to_write->WriteToFileDescriptor(file_descriptor_, start_it);
  } else {
    Knot::iterator stop_it =
        to_write->WriteToFileDescriptor(file_descriptor_, start_it);
    (*logging_stream_) << to_write->SubKnot(start_it, stop_it);
    return stop_it;
  }
}

// This does not aquire the data_tex_ mutex. Any calling function must already
// hold this mutex.
Knot::iterator WriteQueue::TryWriteImmediate(Knot* to_write) {
  if (output_queue_.size() == 0) {
    pending_writes_event_->Add();
    DCHECK(pending_bytes_ == 0);
    Knot::iterator stop_it = WriteItem(to_write, to_write->begin());
    if (stop_it == to_write->end()) {
      pending_writes_event_->Remove();
    }
    return stop_it;
  } else {
    return to_write->begin();
  }
}

bool WriteQueue::Write(Knot* to_write) {
  DCHECK(to_write->Size() > 0);
  boost::lock_guard<boost::mutex> l(data_tex_);
  Knot::iterator next_write_start = to_write->begin();
  // We should only try the write if we can guarantee we'll be able to complete
  // the write. Otherwise we'd end up with a broken protocol. We can't know how
  // much data the next write() call will accept but as long as there's room on
  // the queue for the new data we know we'll be able to queue it if necessary.
  if ((to_write->Size() + pending_bytes_) >=
      static_cast<size_t>(max_pending_bytes_)) {
    return false;
  } else {
    next_write_start = TryWriteImmediate(to_write);
    if (next_write_start == to_write->end()) {
      delete to_write;
      return true;
    } else {
      // If we're here either we tried to write it and failed or we noticed that
      // the queue isn't empty so we didn't even try to write it. In either case
      // we need to queue it up to be written later.
      QueueWrite(to_write, next_write_start, NULL);
      return true;
    }
  }
}

StreamingWriter* WriteQueue::GetStreamingWriter() {
  data_tex_.lock();
  if (output_queue_.size() == 0) {
    pending_writes_event_->Add();
    output_queue_.push_back(
        OutputQueueEntry(nullptr, Knot::iterator(), nullptr, true));
    data_tex_.unlock();
  } else {
    SimpleCondition<bool> writer_ready(false);

    ++num_blocked_threads_;
    QueueWrite(
        OutputQueueEntry(nullptr, Knot::iterator(), &writer_ready, true));
    // Have to unlock the mutex before we wait for the condition to become true
    // or we'll deadlock.
    data_tex_.unlock();
    writer_ready.Wait(true);
  }
  return new StreamingWriter(this, logging_stream_);
}

void WriteQueue::WriteWithBlock(Knot* to_write) {
  CHECK(boost::this_thread::get_id() !=
        parent_->GetEventLoopThreadId())
      << "Calling WriteWithBlock from the WriteEventLoop thread "
      << "will cause a deadlock.";
  DCHECK(to_write->Size() > 0);
  data_tex_.lock();

  Knot::iterator next_write_start = TryWriteImmediate(to_write);
  if (next_write_start == to_write->end()) {
    data_tex_.unlock();
    delete to_write;
    return;
  } else {
    SimpleCondition<bool> write_done(false);
    QueueWrite(to_write, next_write_start, &write_done);
    ++num_blocked_threads_;
    // Wait until the write completes.
    data_tex_.unlock();
    write_done.Wait(true);
  }
}

void WriteQueue::QueueWrite(Knot* to_write, Knot::iterator start_it,
                            SimpleCondition<bool>* notify_cond) {
  QueueWrite(OutputQueueEntry(to_write, start_it, notify_cond));
}

// Note that this does *NOT* aquire the data_tex_ mutex. Whatever methods call
// it *must* be holding the mutex. (Unfortunately boost::mutex doesn't seem to
// provide a way to check that a mutex is held so we can't put a CHECK here).
void WriteQueue::QueueWrite(const OutputQueueEntry& entry) {
  output_queue_.push_back(entry);
  if (!writeable_event_registered_) {
    if (output_queue_.size() == 1) {
      DCHECK(entry.output_item != nullptr);
      parent_->RegisterEvent(writeable_event_);
      writeable_event_registered_ = true;
    } else {
      // This happens if there is an allocated StreamingWriter instance but it
      // currently doesn't have anything to write. In that case the file may be
      // writeable but we have nothing to write and we're just queueing up a new
      // write behind the StreamingWriter.
      DCHECK(output_queue_.front().is_streaming_writer);
    }
  }
  if (entry.output_item != nullptr) {
    pending_bytes_ += entry.output_item->end() - entry.output_start_it;
    DCHECK(pending_bytes_ > 0);
  } else {
    DCHECK(entry.is_streaming_writer == true);
  }
}

void WriteQueue::StreamingWriterDone() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  DCHECK(output_queue_.front().is_streaming_writer == true);
  DCHECK(output_queue_.front().output_item == nullptr);
  output_queue_.pop_front();
  ProcessOutputQueue();
}

void WriteQueue::HandleCallback() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  writeable_event_registered_ = false;
  ProcessOutputQueue();
}

// Assumes the data_tex_ mutex is already held!
void WriteQueue::ProcessOutputQueue() {
  while (output_queue_.size() > 0) {
    DCHECK(pending_bytes_ >= 0);
    OutputQueueEntry& to_write = output_queue_.front();
    if (to_write.output_item == nullptr) {
      // This should only happen if the item represents a blocked call to
      // GetStreamingWriter(). In that case there isn't yet anything to write.
      // Instead, we just signal that it is now safe to return the
      // StreamingWriter object.
      DCHECK(to_write.is_streaming_writer == true);
      DCHECK(to_write.done_cond != nullptr);
      --num_blocked_threads_;
      DCHECK(num_blocked_threads_ >= 0);
      to_write.done_cond->Set(true);
      break;
    } else {
      // Assume we'll be able to write the everything in to_write. If not well
      // adjust below.
      pending_bytes_ -= to_write.output_item->end() - to_write.output_start_it;
      DCHECK(pending_bytes_ >= 0);
      Knot::iterator next_write_start = WriteItem(
          to_write.output_item, to_write.output_start_it);
      if (next_write_start == to_write.output_item->end()) {
        // All written so remove it from the queue and free the Knot. Unless it
        // was a StreamingWriter request in wich case we keep the item on the
        // queue and exit the loop, waiting for future write requests.
        if (to_write.is_streaming_writer) {
          // Since this is a streaming writer, we don't remove it from the
          // queue, but we do set the output_item to nullptr since it has been
          // successfully written.
          to_write.output_item = nullptr;
          DCHECK(to_write.done_cond != nullptr);
          to_write.done_cond->Set(true);
          to_write.done_cond = nullptr;
          --num_blocked_threads_;
          DCHECK(num_blocked_threads_ >= 0);
          break;
        } else {
          delete to_write.output_item;
          if (to_write.done_cond != NULL) {
            --num_blocked_threads_;
            DCHECK(num_blocked_threads_ >= 0);
            to_write.done_cond->Set(true);
          }
          output_queue_.pop_front();
        }
      } else {
        // It wasn't all written so update the offset but don't pop it off the
        // queue.
        pending_bytes_ += to_write.output_item->end() - next_write_start;
        to_write.output_start_it = next_write_start;
        // There's still data left so we asked to get notified when we can again
        // write to the file.
        parent_->RegisterEvent(writeable_event_);
        writeable_event_registered_ = true;
        break;
      }
    }
  }
  if (output_queue_.size() == 0) {
    no_items_pending_cond_.notify_all();
    pending_writes_event_->Remove();
  }
}

void WriteQueue::FileHandleWriteableCallback(
    int file_descriptor_, short event_type, void* write_queue_ptr) {
  CHECK(event_type == EV_WRITE);
  WriteQueue* write_queue = reinterpret_cast<WriteQueue*>(write_queue_ptr);
  write_queue->HandleCallback();
}

int WriteQueue::BytesPending() const {
  boost::lock_guard<boost::mutex> l(data_tex_);
  return pending_bytes_;
}

int WriteQueue::ItemsPending() const {
  boost::lock_guard<boost::mutex> l(data_tex_);
  return output_queue_.size();
}

void WriteQueue::WaitForPendingItems() const {
  boost::unique_lock<boost::mutex> l(data_tex_);
  while (output_queue_.size() > 0) {
    no_items_pending_cond_.wait(l);
  }
}

int WriteQueue::NumBlockedThreads() const {
  boost::lock_guard<boost::mutex> l(data_tex_);
  return num_blocked_threads_;
}

////////////////////////////////////////////////////////////////////////////////
// StreamingWriter
////////////////////////////////////////////////////////////////////////////////

StreamingWriter::StreamingWriter(WriteQueue* parent,
                                 std::ostream* logging_stream)
    : parent_(parent), logging_stream_(logging_stream) {
}

StreamingWriter::~StreamingWriter() {
  parent_->StreamingWriterDone();
}

void StreamingWriter::Write(const Knot& to_write) {
  SimpleCondition<bool> write_done(false);
  {
    boost::lock_guard<boost::mutex> l(parent_->data_tex_);
    WriteQueue::OutputQueueEntry& entry = parent_->output_queue_.front();
    DCHECK(entry.is_streaming_writer == true);

    entry.output_item = &to_write;
    parent_->pending_bytes_ += to_write.Size();
    entry.output_start_it = to_write.begin();
    entry.done_cond = &write_done;

    ++(parent_->num_blocked_threads_);
    parent_->ProcessOutputQueue();
  }

  write_done.Wait(true);
}
