//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for EventLoop 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Jun 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE EventLoopTest

#include <boost/bind.hpp>
#include <boost/thread.hpp>
#include <chrono>
#include <sstream>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>

#include "event-loop.h"
#include "statics.h"
#include "test-init.h"
#include "util.h"

using namespace std;

// We'll use this method as our callback. We'll use boost::bind to bind a
// vector, mutex, and condition variable. All new data will be appended to the
// vector (protected by the mutex). After the new data is added the condition
// variable is fired so we can wait for the data to actually be read in the test
// thread.
void AppendReceived(vector<string>* append_to,
                    boost::mutex* append_to_tex,
                    boost::condition_variable* append_to_changed,
                    Strand* received) {
  {
    boost::lock_guard<boost::mutex> l(*append_to_tex);
    append_to->push_back(received->ToString());
    append_to_changed->notify_all();
  }
  delete received;
}

// Check that reading from a pipe via the event loop works as expected.
BOOST_AUTO_TEST_CASE(PipeReadingWorks) {
  // Create a Unix pipe. We'll use EventLoop to watch the read end of the pipe
  // and we'll write data to it via write().
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  EventLoop loop;
  vector<string> received_data;
  boost::mutex received_data_tex;
  boost::condition_variable received_data_changed;
  loop.RegisterFileDataCallback(
      read_end_fd,
      boost::bind(&AppendReceived, &received_data, &received_data_tex,
                  &received_data_changed, _1));

  BOOST_CHECK_EQUAL(received_data.size(), 0);
  loop.Start();
  
  const char* FIRST_LINE = "Line 1";
  int written = write(write_end_fd, FIRST_LINE, strlen(FIRST_LINE));
  BOOST_REQUIRE_EQUAL(written, strlen(FIRST_LINE));
  fsync(write_end_fd);

  {
    // Because things are read in a separate thread we may need to wait for the
    // callback to be called, etc. The while loop and condition variable
    // do that.
    boost::unique_lock<boost::mutex> l(received_data_tex);
    while (received_data.size() < 1) {
      received_data_changed.wait(l);
    }
    BOOST_CHECK_EQUAL(received_data.size(), 1);
    BOOST_CHECK_EQUAL(received_data[0], FIRST_LINE);
  }


  // Send some binary data through the pipe including an embedded '\0'. This
  // ensures that we're able to send/receive binary data.
  const char SECOND_LINE[] = {'a', '\0', 1, 'b', 'c'};
  const int SECOND_LINE_SIZE = 5;
  written = write(write_end_fd, SECOND_LINE, SECOND_LINE_SIZE);
  BOOST_REQUIRE_EQUAL(written, SECOND_LINE_SIZE);
  fsync(write_end_fd);

  {
    boost::unique_lock<boost::mutex> l(received_data_tex);
    while (received_data.size() < 2) {
      received_data_changed.wait(l);
    }
    BOOST_CHECK_EQUAL(received_data.size(), 2);
    for (int i = 0; i < SECOND_LINE_SIZE; ++i) {
      BOOST_CHECK_EQUAL(received_data[1][i], SECOND_LINE[i]);
    }
  }

  close(write_end_fd);
}

// Test a series of writes which shouldn't block to make sure they work.
BOOST_AUTO_TEST_CASE(NonBlockingWritesWork) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop e_loop;
  WriteQueue* wq = e_loop.GetWriteQueue(write_end_fd);
  e_loop.Start();

  bool result = wq->Write(new Knot(new string("Test Chunk 1\n")));
  BOOST_REQUIRE_EQUAL(result, true);
  string read_from_pipe;
  getline(pipe_read_stream, read_from_pipe);
  BOOST_CHECK_EQUAL(read_from_pipe, "Test Chunk 1");

  result = wq->Write(new Knot(new string("Test Chunk 2\n")));
  BOOST_REQUIRE_EQUAL(result, true);
  result = wq->Write(new Knot(new string("Test Chunk 3\n")));
  BOOST_REQUIRE_EQUAL(result, true);

  getline(pipe_read_stream, read_from_pipe);
  BOOST_CHECK_EQUAL(read_from_pipe, "Test Chunk 2");

  getline(pipe_read_stream, read_from_pipe);
  BOOST_CHECK_EQUAL(read_from_pipe, "Test Chunk 3");
}


// Write to a pipe but don't read from it. Keep writing until we see the queue
// start to fill up. Then start reading before Write() returns false and make
// sure everything we wrote shows up in the same order it was originally
// written.
BOOST_AUTO_TEST_CASE(FullPipeWritesWork) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop e_loop;
  WriteQueue* wq = e_loop.GetWriteQueue(write_end_fd);
  e_loop.Start();

  int item_write_count = 0;
  // Write items until there's 5 queued up. There should be plenty of room in
  // the buffer to hold 5 small writes.
  const int kNumItemsInBuffer = 5;
  while (wq->ItemsPending() < kNumItemsInBuffer) {
    ostringstream to_write;
    to_write << "Item Number " << item_write_count << "\n";
    ++item_write_count;
    int result = wq->Write(new Knot(new string(to_write.str())));
    BOOST_REQUIRE_EQUAL(result, true);
  }
  
  BOOST_CHECK_EQUAL(wq->ItemsPending(), kNumItemsInBuffer);

  // Note that the pipe itself has a buffer so there should be way more than
  // kNumItemsInBuffer items that were written. Let's check that and then read
  // 1/2 of them. Here I check that's there's at least 5 more but the 5 is
  // pretty arbitrary.
  BOOST_CHECK_GT(item_write_count, kNumItemsInBuffer + 5);
  int number_to_read = item_write_count / 2;

  int item_read_count = 0;
  string line;
  for (int i = 0; i < number_to_read; ++i) {
    getline(pipe_read_stream, line);
    ostringstream expected;
    expected << "Item Number " << item_read_count;
    ++item_read_count;
    BOOST_CHECK_EQUAL(line, expected.str());
  }

  // Now write some more stuff until we again have kNumItemsInBuffer in the
  // buffer.
  while (wq->ItemsPending() < kNumItemsInBuffer) {
    ostringstream to_write;
    to_write << "Item Number " << item_write_count << "\n";
    ++item_write_count;
    int result = wq->Write(new Knot(new string(to_write.str())));
    BOOST_REQUIRE_EQUAL(result, true);
  }
  
  BOOST_CHECK_EQUAL(wq->ItemsPending(), kNumItemsInBuffer);

  // Finally, read everything. They should all be there and they should be in
  // order.
  while (item_read_count < item_write_count) {
    getline(pipe_read_stream, line);
    ostringstream expected;
    expected << "Item Number " << item_read_count;
    ++item_read_count;
    BOOST_CHECK_EQUAL(line, expected.str());
  }
}

// Used in the next unit test...
void WriteFromThread(int num_to_write, const string& write_prefix,
                     WriteQueue* wq) {
  for (int i = 0; i < num_to_write; ++i) {
    ostringstream output;
    output << write_prefix << i << "\n";

    // If the buffer is full the write might fail. So here we busy loop until
    // we're able to write.
    bool write_queued = false;
    do {
      write_queued = wq->Write(new Knot(new string(output.str())));
    } while (!write_queued);
  }
}

// First fill up the buffer. Then spawn two threads and have them writing as
// fast as possible. That way we've got writes from two thread contending to get
// data queued which should test that things are really thread safe. Once the
// threads are running start reading and make sure all messages are received in
// the correct order.
BOOST_AUTO_TEST_CASE(WritesFromThreadsWork) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop e_loop;
  WriteQueue* wq = e_loop.GetWriteQueue(write_end_fd);
  e_loop.Start();

  int initial_write_count = 0;
  // Write until the pipe is full and at least one item gets buffered.
  while (wq->ItemsPending() == 0) {
    ostringstream to_write;
    to_write << "Initial Write " << initial_write_count << "\n";
    ++initial_write_count;
    int result = wq->Write(new Knot(new string(to_write.str())));
    BOOST_REQUIRE_EQUAL(result, true);
  }
  
  const int kT1Writes = 500;
  const int kT2Writes = 500;
  boost::thread t1(
      boost::bind(&WriteFromThread, kT1Writes, "Thread 1: ", wq));
  boost::thread t2(
      boost::bind(&WriteFromThread, kT2Writes, "Thread 2: ", wq));

  for (int initial_read_count = 0; initial_read_count < initial_write_count;
       ++initial_read_count) {
    string line;
    getline(pipe_read_stream, line);
    ostringstream expected;
    expected << "Initial Write " << initial_read_count;
    BOOST_CHECK_EQUAL(line, expected.str());
  }

  // Now everything we read should have come from one of the two threads. Make
  // sure we get what we expect.
  int num_t1_read = 0;
  int num_t2_read = 0;
  for (int j = 0; j < kT1Writes + kT2Writes; ++j) {
    string line;
    getline(pipe_read_stream, line);
    ostringstream expected;
    if (line.find("Thread 1:") == 0) {
     expected << "Thread 1: " << num_t1_read;
     ++num_t1_read;
     BOOST_CHECK_EQUAL(line, expected.str());
    } else {
     expected << "Thread 2: " << num_t2_read;
     ++num_t2_read;
     BOOST_CHECK_EQUAL(line, expected.str());
    }
  }

  t1.join();
  t2.join();
}

// Issue several writes that shouldn't block. That should work.
BOOST_AUTO_TEST_CASE(NonBlockingWriteWithBlockWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop e_loop;
  WriteQueue* wq = e_loop.GetWriteQueue(write_end_fd);
  e_loop.Start();
 
  string line;  

  wq->WriteWithBlock(new Knot(new string("Line 1\n")));
  getline(pipe_read_stream, line);
  BOOST_CHECK_EQUAL(line, "Line 1");

  wq->WriteWithBlock(new Knot(new string("Line 2\n")));
  getline(pipe_read_stream, line);
  BOOST_CHECK_EQUAL(line, "Line 2");
}

// The following function is run in separate threads in the next unit test.
void WriteWithBlockFromThread(int thread_id, int num_to_write,
                              WriteQueue* wq) {
  for (int i = 0; i < num_to_write; ++i) {
    ostringstream output;
    output << "Thread: " << thread_id << "\nMessage number: " << i << "\n";
    wq->WriteWithBlock(new Knot(new string(output.str())));
  }
}

// Also used by the following test. This writes the same thing over and over
// until it's told to stop. It sets the final int* argument to be the number of
// times it wrote it's message.
void WriteUntilStop(WriteQueue* wq, boost::mutex* stop_tex, bool* stop,
                    int* num_written) {
  int write_count = 0;
  while (true) {
    {
      boost::lock_guard<boost::mutex> l(*stop_tex);
      if (*stop) {
        break;
      }
    }
    wq->WriteWithBlock(new Knot(new string("Buffer Message\n")));
    ++write_count;
  }
  *num_written = write_count;
}

BOOST_AUTO_TEST_CASE(BlockingWritesWork) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop e_loop;
  WriteQueue* wq = e_loop.GetWriteQueue(write_end_fd);
  // Make the buffer smaller to make this run faster.
  wq->SetMaximumPendingBytes(2048);
  e_loop.Start();

  // First start a thread that will write until it blocks. Then we know the
  // queue is full. At that point we'll start the other threads.
  boost::mutex stop_buffer_thread_tex;
  bool stop_buffer_thread = false;
  int num_buffer_writes;
  // The number of buffer messages we've read from the pipe
  int num_buffer_reads = 0;
  boost::thread buffer_thread(boost::bind(&WriteUntilStop, wq,
                                          &stop_buffer_thread_tex,
                                          &stop_buffer_thread,
                                          &num_buffer_writes));
  while (wq->NumBlockedThreads() == 0) {
    boost::this_thread::sleep(boost::posix_time::milliseconds(50));
  }
  // Tell the buffer thread it can stop. We still haven't read anything from the
  // pipe so that thread is blocked on the WriteWithBlock call but as soon as
  // we start reading it should unblock and exit.
  stop_buffer_thread_tex.lock();
  stop_buffer_thread = true;
  stop_buffer_thread_tex.unlock();

  const int kNumThreads = 10;
  const int kNumWritesPerThread = 1000;
  vector<boost::thread*> write_threads;
  vector<int> num_read_by_thread(kNumThreads, 0);
  for (int i = 0; i < kNumThreads; ++i) {
    boost::thread* t = new boost::thread(
        boost::bind(&WriteWithBlockFromThread, i,
                    kNumWritesPerThread, wq));
    write_threads.push_back(t);
  }
  
  while (count(num_read_by_thread.begin(),
               num_read_by_thread.end(),
               kNumWritesPerThread) < kNumThreads) {
    string line;
    getline(pipe_read_stream, line);
    if (line.find("Buffer Message") != string::npos) {
      ++num_buffer_reads;
    } else {
      BOOST_REQUIRE_EQUAL(line.find("Thread: "), 0);
      const int kThreadPrefixLen = 8; // length of "Thread: "
      int thread_id = atoi(line.substr(kThreadPrefixLen).c_str());
      string message_num_line;
      getline(pipe_read_stream, message_num_line);
      BOOST_REQUIRE_EQUAL(message_num_line.find("Message number: "), 0);
      const int kMessageNumberPrefixLen = 16;
      int message_number = atoi(
          message_num_line.substr(kMessageNumberPrefixLen).c_str());
      BOOST_CHECK_EQUAL(message_number, num_read_by_thread[thread_id]);
      num_read_by_thread[thread_id] += 1;
    }
  }

  buffer_thread.join();
  vector<boost::thread*>::iterator thread_it;
  for (thread_it = write_threads.begin(); thread_it != write_threads.end();
       ++thread_it) {
    (*thread_it)->join();
    delete *thread_it;
  }

  BOOST_CHECK_EQUAL(num_buffer_reads, num_buffer_writes);
}

// Just a simple test to make sure it works at all.
BOOST_AUTO_TEST_CASE(StreamingWriterWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];
  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop loop;
  loop.Start();
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);

  unique_ptr<StreamingWriter> writer(wq->GetStreamingWriter());

  writer->Write(Knot(new string("This is my test data\n")));
  writer.reset();

  string results;
  getline(pipe_read_stream, results);
  BOOST_CHECK_EQUAL(results, "This is my test data");
};

// Helper function for the following tests.
void WriteMessageToStreamingWriter(WriteQueue* queue, const string* message) {
  unique_ptr<StreamingWriter> writer(queue->GetStreamingWriter());
  writer->Write(Knot(message));
}

// Make sure ordering is correct so that writes queued traditionally end up
// ordered correctly with respect to writes queued via StreamingWriter.
BOOST_AUTO_TEST_CASE(StreamingWriterOrderingWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];
  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop loop;
  loop.Start();
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);
  // Make things faster by making the buffer smaller
  wq->SetMaximumPendingBytes(1024);

  // First queue up lots of writes without reading from the pipe. Do this until
  // the queue is full (e.g. Write() returns false). Then call
  // WriteMessageToStreamingWriter in a separate thread. That thread shouldn't
  // write anything until all the already added messages have been sent.
  bool keep_going = true;
  while (keep_going) {
    Knot* to_write = new Knot(new string("BEFORE MESSAGE\n"));
    keep_going = wq->Write(to_write);
    if (!keep_going) {
      delete to_write;
    }
  }

  boost::thread spt(std::bind(
          &WriteMessageToStreamingWriter, wq, new string("FROM STREAMING\n")));

  while (true) {
    string from_pipe;
    getline(pipe_read_stream, from_pipe);
    if (from_pipe == "FROM STREAMING") {
      break;
    } else {
      BOOST_CHECK_EQUAL(from_pipe, "BEFORE MESSAGE");
    }
  }
  
  // Now write some more stuff the traditional way and make sure we get only the
  // new stuff, no more BEFORE_MESSAGE messages should arrive.
  for (int i = 0; i < 10; ++i) {
    wq->Write(new Knot(new string("AFTER MESSAGE\n")));  
  }

  for (int i = 0; i < 10; ++i) {
    string from_pipe;
    getline(pipe_read_stream, from_pipe);
    BOOST_CHECK_EQUAL(from_pipe, "AFTER MESSAGE");
  }
}

// Writes a header followed by multiple instances of a body and then a footer
// using a StreamingWriter. See tests below for details.
void MultipleWritesViaStreamingWriter(WriteQueue* queue,
                                      int message_body_count,
                                      const string& message_id) {
  CHECK(message_id[message_id.size() - 1] == '\n');
  unique_ptr<StreamingWriter> writer(queue->GetStreamingWriter());

  string* msg_header = new string("STREAMINGHEADER: ");
  *msg_header += message_id;
  writer->Write(Knot(msg_header));
  std::this_thread::sleep_for(std::chrono::milliseconds(10));

  for (int i = 0; i < message_body_count; ++i) {
    string* msg_body = new string("STREAMINGBODY: ");
    *msg_body += message_id;
    writer->Write(Knot(msg_body));
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }

  string* msg_footer = new string("STREAMINGFOOTER: ");
  *msg_footer += message_id;
  writer->Write(msg_footer);
}

// Write message_repeat_count copies of the same multiline message with pauses
// in between. See the unit tests below.
void MultipleNormalWrites(WriteQueue* queue, int message_body_count,
                          int message_repeat_count, const string& message_id) {
  CHECK(message_id[message_id.size() - 1]  == '\n');

  for (int j = 0; j < message_repeat_count; ++j) {
    Knot* message = new Knot;
    string* msg_header = new string("NORMALHEADER: ");
    *msg_header += message_id;
    message->Append(msg_header);

    for (int i = 0; i < message_body_count; ++i) {
      string* msg_body = new string("NORMALBODY: ");
      *msg_body += message_id;
      message->Append(msg_body);
    }

    string* msg_footer = new string("NORMALFOOTER: ");
    *msg_footer += message_id;
    message->Append(msg_footer);

    if (!queue->Write(message)) {
      queue->WriteWithBlock(message);
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
}

// Queue up multiple threads. Some write via StreamingWriter, some write in the
// "normal" way. All write multiple messages and wait various amounts of time
// between writes. We ensure that everything gets written and then all writes,
// including those that come from multiple writes to StreamingWriter, are
// atomic.
BOOST_AUTO_TEST_CASE(StreamingWriterInManyThreadsWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];
  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop loop;
  loop.Start();
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);

  const int kNormalBodyCount = 5;
  const int kNormalRepeats = 2;
  const int kStreamingBodyCount = 5;

  boost::thread tn1(std::bind(&MultipleNormalWrites, wq, kNormalBodyCount,
                             kNormalRepeats, "Normal1\n"));
  boost::thread ts1(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming1\n"));
  boost::thread tn2(std::bind(&MultipleNormalWrites, wq, kNormalBodyCount,
                             kNormalRepeats, "Normal2\n"));
  boost::thread ts2(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming2\n"));
  boost::thread ts3(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming3\n"));


  int complete_messages_found = 0;
  // The number of complete messages (HEADER, BODY, then FOOTER) we expect from
  // the 5 threads above.
  const int kExpectedMessageCount = 2 * kNormalRepeats + 3;
  while(complete_messages_found < kExpectedMessageCount) {
    string line;
    getline(pipe_read_stream, line);
    if (line.find("NORMAL") == 0) {
      // We expect a NORMALHEADER followed by kNormalBodyCount NORMALBODY
      // messages, followed by a NORMALFOOTER message, all with the same message
      // id.
      BOOST_CHECK_EQUAL(line.find("NORMALHEADER: "), 0);
      string cur_message_id = line.substr(strlen("NORMALHEADER: "));

      string expected_body("NORMALBODY: ");
      expected_body += cur_message_id;
      for (int i = 0; i < kNormalBodyCount; ++i) {
        getline(pipe_read_stream, line);
        BOOST_CHECK_EQUAL(line, expected_body);
      }
      
      string expected_footer("NORMALFOOTER: ");
      expected_footer += cur_message_id;
      getline(pipe_read_stream, line);
      BOOST_CHECK_EQUAL(line, expected_footer);
      ++complete_messages_found;
    } else {
      BOOST_CHECK_EQUAL(line.find("STREAMINGHEADER: "), 0);
      string cur_message_id = line.substr(strlen("STREAMINGHEADER: "));

      string expected_body("STREAMINGBODY: ");
      expected_body += cur_message_id;
      
      for (int i = 0; i < kStreamingBodyCount; ++i) {
        getline(pipe_read_stream, line);
        BOOST_CHECK_EQUAL(line, expected_body);
      }

      string expected_footer("STREAMINGFOOTER: ");
      expected_footer += cur_message_id;
      getline(pipe_read_stream, line);
      BOOST_CHECK_EQUAL(line, expected_footer);
      ++complete_messages_found;
    }
  }
}

// Pretty much much the same as above, but we 1st fill up the queue
BOOST_AUTO_TEST_CASE(StreamingWriterInManyThreadsWithFullQueueWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];
  FileHandleIStream pipe_read_stream(read_end_fd);

  EventLoop loop;
  loop.Start();
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);
  // Make things a bit faster by making the buffer smaller
  wq->SetMaximumPendingBytes(1024);


  // Fill up the queue with "IGNORE\n" messages.
  int num_ignore_messages = 0;
  bool keep_going = true;
  while (keep_going) {
    Knot* to_write = new Knot(new string("IGNORE\n"));
    keep_going = wq->Write(to_write);
    if (keep_going) {
      ++num_ignore_messages;
    } else {
      delete to_write;
    }
  }

  const int kNormalBodyCount = 5;
  const int kNormalRepeats = 2;
  const int kStreamingBodyCount = 5;

  boost::thread tn1(std::bind(&MultipleNormalWrites, wq, kNormalBodyCount,
                             kNormalRepeats, "Normal1\n"));
  boost::thread ts1(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming1\n"));
  boost::thread tn2(std::bind(&MultipleNormalWrites, wq, kNormalBodyCount,
                             kNormalRepeats, "Normal2\n"));
  boost::thread ts2(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming2\n"));
  boost::thread ts3(std::bind(&MultipleWritesViaStreamingWriter, wq,
                              kStreamingBodyCount, "Streaming3\n"));

  // We should get all the IGNORE messages before we get anything else.
  for (int i = 0; i < num_ignore_messages; ++i) {
    string line;
    getline(pipe_read_stream, line);
    CHECK(line == "IGNORE");
    BOOST_CHECK_EQUAL(line, "IGNORE");
  }

  int complete_messages_found = 0;
  // The number of complete messages (HEADER, BODY, then FOOTER) we expect from
  // the 5 threads above.
  const int kExpectedMessageCount = 2 * kNormalRepeats + 3;
  while(complete_messages_found < kExpectedMessageCount) {
    string line;
    getline(pipe_read_stream, line);
    if (line.find("NORMAL") == 0) {
      // We expect a NORMALHEADER followed by kNormalBodyCount NORMALBODY
      // messages, followed by a NORMALFOOTER message, all with the same message
      // id.
      BOOST_CHECK_EQUAL(line.find("NORMALHEADER: "), 0);
      string cur_message_id = line.substr(strlen("NORMALHEADER: "));

      string expected_body("NORMALBODY: ");
      expected_body += cur_message_id;
      for (int i = 0; i < kNormalBodyCount; ++i) {
        getline(pipe_read_stream, line);
        BOOST_CHECK_EQUAL(line, expected_body);
      }
      
      string expected_footer("NORMALFOOTER: ");
      expected_footer += cur_message_id;
      getline(pipe_read_stream, line);
      BOOST_CHECK_EQUAL(line, expected_footer);
      ++complete_messages_found;
    } else {
      BOOST_CHECK_EQUAL(line.find("STREAMINGHEADER: "), 0);
      string cur_message_id = line.substr(strlen("STREAMINGHEADER: "));

      string expected_body("STREAMINGBODY: ");
      expected_body += cur_message_id;
      
      for (int i = 0; i < kStreamingBodyCount; ++i) {
        getline(pipe_read_stream, line);
        BOOST_CHECK_EQUAL(line, expected_body);
      }

      string expected_footer("STREAMINGFOOTER: ");
      expected_footer += cur_message_id;
      getline(pipe_read_stream, line);
      BOOST_CHECK_EQUAL(line, expected_footer);
      ++complete_messages_found;
    }
  }
}

void ReadThreadFunction(istream* input_stream, string* data_read) {
  while (input_stream->good()) {
    string line;
    getline(*input_stream, line);
    if (!line.empty()) {
      *data_read += line + "\n";
    }
  }

  BOOST_CHECK_EQUAL(input_stream->eof(), true);
}

// We had a bug where you could call ExitLoopAndWait and the event loop would
// exit while there were still some writes outstanding. This test reproduces the
// old issue. We keep it so we can be sure we don't re-introduce the same issue.
//
// Note: this tests a race condition. It should never fail. If it fails at all,
// even very rarely, there's a real bug that needs to be fixed.
//
// The test works as follows:
// 1) We construct a very big buffer of stuff to be written out.
// 2) We write queue up the write in the main thread
// 3) We read the output of the write from another thread
// 4) We call ExitLoopAndWait from the main thread. That should wait for all the
//    writes in the writing thread to complete.
// 5) We make sure everything was received in the receiving thread.
BOOST_AUTO_TEST_CASE(AllWritesCompleteBeforeThreadExits) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream read_stream(read_end_fd);
  string data_read;
  boost::thread read_thread(std::bind(
          &ReadThreadFunction, &read_stream, &data_read));

  EventLoop loop;
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);

  loop.Start();

  Knot* output_data = new Knot;
  const char kOutputLine[] = "This is one line in the buffer\n";
  const int kOutputLineLength = strlen(kOutputLine);
  // Write about 30MB of data (kOutputLine is 29 characters long)
  const int kNumLines = 1 << 20;
  int bytes_to_write = kOutputLineLength * kNumLines;

  // Make sure this many bytes can be queued. 100 is totally arbitrary...
  wq->SetMaximumPendingBytes(bytes_to_write + 100);

  for (int i = 0; i < kNumLines; ++i) {
    output_data->AppendOwned(kOutputLine, kOutputLineLength);
  }
  BOOST_CHECK_EQUAL(output_data->Size(), bytes_to_write);

  BOOST_REQUIRE_EQUAL(wq->Write(output_data), true);

  loop.ExitLoopAndWait();
  // We close the stream now - all the data we're going to write has been
  // written. This will also cause the reading thread to terminate as the pipe
  // will be at EOF.
  close(write_end_fd);

  read_thread.join();

  BOOST_CHECK_EQUAL(data_read.size(), bytes_to_write);
}

void WritingThread(WriteQueue* write_queue,
                   SimpleCondition<bool>* streaming_writer_allocated,
                   const Knot& line_to_write,
                   int num_lines) {
  std::unique_ptr<StreamingWriter> writer(
      write_queue->GetStreamingWriter());
  streaming_writer_allocated->Set(true);
  for (int i = 0; i < num_lines; ++i) {
    writer->Write(line_to_write);
  }
}

// The same test as AllWritesCompleteBeforeThreadExits but using a
// StreamingWriter. This is a bit different as streaming writer uses EventLoop
// differently so it's conceivable that the previous test would pass and this
// would fail or vice-versa.
//
// In order to use a StreamingWriter we need to introduce an additional thread
// to do the writing. We don't need to wait for that thread to finish (the
// ExitLoopAndWait call should ensure that the StreamingWriter has been
// destroyed before exiting) but we do need to ensure that it has started so we
// wait on a SimpleCondition<bool> that tells us the StreamingWriter has been
// allocated.
BOOST_AUTO_TEST_CASE(AllWritesCompleteBeforeExitWithStreamingWriter) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  FileHandleIStream read_stream(read_end_fd);
  string data_read;
  boost::thread read_thread(std::bind(
          &ReadThreadFunction, &read_stream, &data_read));

  EventLoop loop;
  WriteQueue* wq = loop.GetWriteQueue(write_end_fd);

  loop.Start();

  const char kOutputLine[] = "This is one line in the buffer\n";
  const int kOutputLineLength = strlen(kOutputLine);
  Knot line_to_write;
  line_to_write.AppendOwned(kOutputLine, kOutputLineLength);
  // Write about 30MB of data (kOutputLine is 29 characters long)
  const int kNumLines = 1 << 20;
  int bytes_to_write = kOutputLineLength * kNumLines;

  SimpleCondition<bool> streaming_writer_allocated(false);
  boost::thread write_thread(
      boost::bind(&WritingThread, wq, &streaming_writer_allocated,
                  line_to_write, kNumLines));

  streaming_writer_allocated.Wait(true);

  loop.ExitLoopAndWait();
  // We close the stream now - all the data we're going to write has been
  // written. This will also cause the reading thread to terminate as the pipe
  // will be at EOF.
  close(write_end_fd);

  read_thread.join();

  BOOST_CHECK_EQUAL(data_read.size(), bytes_to_write);
}
