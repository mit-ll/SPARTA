//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of util methods. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   omd            Original Version
//*****************************************************************

#include "util.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <signal.h>
#include <sys/prctl.h>
#include <unistd.h>
#include <time.h>

#include "check.h"
#include "logging.h"
#include "string-algo.h"
#include "general-logger.h"

FileHandleOStream::FileHandleOStream(int fd)
    : buf_(fd, std::ios_base::out), fd_(fd) {
  std::streambuf* old_buffer = rdbuf(&buf_);
  delete old_buffer;
}

void FileHandleOStream::close() {
  flush();
  ::close(fd_);
}

FileHandleIStream::FileHandleIStream(int fd)
    : buf_(fd, std::ios_base::in), fd_(fd) {
  std::streambuf* old_buffer = rdbuf(&buf_);
  delete old_buffer;
}

void FileHandleIStream::close() {
  ::close(fd_);
}

void SetupPipe(int* read_fd, int* write_fd) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  CHECK(ret == 0);

  // The constants 0 and 1 here are as per the pipe() call.
  *read_fd = pipe_descriptors[0];
  *write_fd = pipe_descriptors[1];
}

void SetupPipes(int* proc_stdout_read_fd, int* proc_stdout_write_fd,
                int* proc_stdin_read_fd, int* proc_stdin_write_fd) {
  // Set up file descriptors for the process' stdout
  SetupPipe(proc_stdout_read_fd, proc_stdout_write_fd);

  // Set up file descriptors for the process' stdin
  SetupPipe(proc_stdin_read_fd, proc_stdin_write_fd);
}

// This is pretty much the standard unix fork/exec thing plus we set up file
// handles for the subprocess' stdin/stdout.
int SpawnAndConnectPipes(
    const std::string& executable, const std::vector<std::string>& args,
    int* process_stdin_handle, int* process_stdout_handle) {
  // File descriptors for the pipe that the parent writes to to send data tot he
  // child and the pipe the child writes to to send data to the parent.
  int parent_to_child[2];
  int child_to_parent[2];

  // Calling pipe returns two file descriptors. These constants indicate which
  // file descriptor is for reading and which is for writing.
  const int READ_END = 0;
  const int WRITE_END = 1;

  // We're going to connect the pipes to the child's stdin and stdout. These are
  // the file descriptors for those streams.
  const int STDIN_FD = 0;
  const int STDOUT_FD = 1;

  if (pipe(parent_to_child) < 0) {
    LOG(ERROR) << "Error creating pipe!";
    exit(1);
  }
  if (pipe(child_to_parent) < 0) {
    LOG(ERROR) << "Error creating pipe!";
    exit(1);
  }

  int pid = fork();
  if (pid < 0) {
    LOG(ERROR) << "Fork failed!";
    exit(1);
  }

  if (pid == 0) {
    // child process

    // There does not appear to be an OS-independent (or even POSIX) way to make
    // sure the child gets a signal when the parent dies. This is a Linux
    // specific way and it should keep us from having lots of orphan processes
    // if the test harness crashes, gets a Ctrl-C, etc.
    if (prctl(PR_SET_PDEATHSIG, SIGHUP) != 0) {
      int e = errno;
      LOG(FATAL) << "Error calling prctl to have child notified "
         "if parent dies:\n" << ErrorMessageFromErrno(e);
    }

    // Close the ends of the pipe we won't use.
    close(parent_to_child[WRITE_END]);
    close(child_to_parent[READ_END]);

    // Redirect the pipe to stdin/stdout and then close the pipe file handles.
    dup2(parent_to_child[READ_END], STDIN_FD);
    close(parent_to_child[READ_END]);
    dup2(child_to_parent[WRITE_END], STDOUT_FD);
    close(child_to_parent[WRITE_END]);

    // execv requires a 0-terminated array of char*. The 1st argument must be
    // the name of the executable. Here we build that array.
    char** exec_args = new char*[args.size() + 2];
    exec_args[0] = new char[executable.size() + 1];
    strcpy(exec_args[0], executable.c_str());
    for (unsigned int i = 0; i < args.size(); ++i) {
      exec_args[i + 1] = new char[args[i].size() + 1];
      strcpy(exec_args[i+1], args[i].c_str());
    }
    exec_args[args.size() + 1] = 0;
    int res = execv(executable.c_str(), exec_args);
    if (res == -1) {
      int err = errno;
      LOG(FATAL) << "Error spawning " << executable << " Error:\n"
          << ErrorMessageFromErrno(err);
    }
    // Note that exec_args memory is never freed, but after the call to execv
    // this process is reaped so there's no real leak and no way to clean it up
    // even if there was a leak.
  } else {
    // parent process

    // Close the ends of the pipe we won't use.
    close(parent_to_child[READ_END]);
    close(child_to_parent[WRITE_END]);

    *process_stdout_handle = child_to_parent[READ_END];
    *process_stdin_handle = parent_to_child[WRITE_END];
  }
  return pid;
}

int SpawnAndConnectPipes(
    const std::string& executable, const std::vector<std::string>& args,
    std::auto_ptr<FileHandleOStream>* process_stdin,
    std::auto_ptr<FileHandleIStream>* process_stdout) {
  int stdin_h, stdout_h;
  int pid = SpawnAndConnectPipes(executable, args, &stdin_h, &stdout_h);
  // Wrap the ends that are connected to stdin/stdout with a iostream.
  process_stdout->reset(new FileHandleIStream(stdout_h));
  process_stdin->reset(new FileHandleOStream(stdin_h));
  return pid;
}

int SpawnAndConnectPipes(
    const std::string & executable, const std::string& args,
    std::auto_ptr<FileHandleOStream>* process_stdin,
    std::auto_ptr<FileHandleIStream>* process_stdout) {
  std::vector<std::string> args_vec;
  Split(args, ' ', &args_vec);
  return SpawnAndConnectPipes(executable, args_vec, 
                              process_stdin, process_stdout);
}

int SpawnAndConnectPipes(
    const std::string& executable, const std::string& args,
    int* process_stdin_handle, int* process_stdout_handle) {
  std::vector<std::string> args_vec;
  Split(args, ' ', &args_vec);
  return SpawnAndConnectPipes(executable, args_vec, process_stdin_handle,
                              process_stdout_handle);
}

std::string ErrorMessageFromErrno(int errnum) {
  const int kBufferSize = 1024;
  char buffer[kBufferSize]; 
  // TODO(njhwang) still don't fully understand under what circumstances the
  // GNU version of strerror_r() will return valid information in buffer,
  // but playing it safe for now and just using the return value of strerror_r
  char* msg = strerror_r(errnum, buffer, kBufferSize);
  return std::string(msg);
}

void LogRealTime(GeneralLogger* logger) {
  timespec time; 
  clock_gettime(CLOCK_REALTIME, &time);  
  double time_conv = time.tv_sec + 1e-9 * time.tv_nsec;
  std::ostringstream s;
  // Show nanosecond precision
  s.setf(std::ios::showpoint | std::ios::fixed);
  s << std::setprecision(9);
  s << "EPOCH_TIME: " << time_conv; 
  logger->Log(s.str());
}

std::string GetCurrentTime() {
  // Obtain the system time for the header lines in log files
  time_t rawtime = time(0);
  struct tm* timeinfo = localtime(&rawtime);
  char timebuffer[20];
  strftime(timebuffer, 20, "%Y-%m-%d %H:%M:%S", timeinfo);
  std::string timestring(timebuffer);
  return timestring;
}
