//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An executable that import the data from a directory full
//                     of files into MySQL.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Oct 2012   omd            Original Version
//*****************************************************************

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/assign/list_inserter.hpp>
#include <sqlite3.h>
#include <dirent.h>
#include <cstring>
#include <fcntl.h>
#include <chrono>
#include <string>
#include <thread>
#include <map>

#include "test-harness/ta1/row-hash-aggregator.h"
#include "baseline/common/mysql-connection.h"
#include "common/safe-file-stream.h"
#include "common/bpbuffer-strand.h"
#include "common/line-raw-parser.h"
#include "common/object_threads.h"
#include "common/buffer-pool.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/check.h"
#include "common/schema.h"
#include "data-inserter.h"
#include "util.h"

namespace po = boost::program_options;
using namespace std;

// Utility function to write error messages that are stored in the standard
// errno variable.
void LogFatalErrno(int err_num, const string& base_message) {
    const int kErrorBufferSize = 1024;
    char error_buffer[kErrorBufferSize];
    LOG(FATAL) << base_message << ":\n"
        << strerror_r(err_num, error_buffer, kErrorBufferSize);
}

// This is a very simple LineRawParseHandler. It simply builds up a
// LineRawData<Knot> structure for all the data between INSERT and ENDINSERT and
// then passes it to DataInserter when ENDINSERT is received.
class DataInsertParseHandler : public LineRawParseHandler {
 public:

  DataInsertParseHandler(ObjectThreads<DataInserter>* insert_pool,
                         bool hash_rows)
      : insert_pool_(insert_pool),
        hash_rows_(hash_rows),
        agg_(RowHashAggregator("INSERT", "ENDINSERT")) {}

  virtual ~DataInsertParseHandler() {}

  virtual void LineReceived(Knot data) {
    //TODO(michael) Can agg_.AddPartialResult() only be called once, outside of
    //the clauses?
    if (data == "INSERT") {
      DCHECK(insert_data_.get() == NULL);
      insert_data_.reset(new LineRawData<Knot>);
      if (hash_rows_) {
        agg_ = RowHashAggregator("INSERT", "ENDINSERT");
        agg_.AddPartialResult(data);
      }
    } else if (data == "ENDINSERT") {
      DCHECK(insert_data_.get() != NULL);
      LineRawData<Knot>* to_insert = insert_data_.release();
      LineRawData<Knot>* row_hash = nullptr;
      if (hash_rows_) {
        row_hash = new LineRawData<Knot>();
        agg_.AddPartialResult(data);
        agg_.Done();
        Knot hash_knot = agg_.GetFuture().Value();
        // NOTE(njhwang) Split for knots currently *includes* the separator
        // specified in the original knot...so we must increment the iterator
        // returned by Find for this to work properly.
        Knot id_knot = hash_knot.Split(++(hash_knot.Find(' ', hash_knot.begin())));
        LOG(DEBUG) << "Hashed row " << id_knot << ": " << hash_knot;
        row_hash->AddLine(hash_knot);
      }
      insert_pool_->AddWork(
          [to_insert, row_hash](DataInserter* inserter) {
              inserter->PerformInserts(to_insert, row_hash);
          });
    } else {
      DCHECK(insert_data_.get() != NULL);
      insert_data_->AddLine(data);
      if (hash_rows_) {
        agg_.AddPartialResult(data);
      }
    }
  }

  virtual void RawReceived(Knot data) {
    DCHECK(insert_data_.get() != NULL);
    insert_data_->AddRaw(data);
    if (hash_rows_) {
      agg_.AddPartialResult(data);
    }
  }

 private:
  ObjectThreads<DataInserter>* insert_pool_;
  unique_ptr<LineRawData<Knot> > insert_data_;
  bool hash_rows_;
  RowHashAggregator agg_;
};

// There is one thread running one of these methods for each file being
// imported. This method reads the data in the file and passes it to the
// DataInsertParseHandler which dispatches a complete row of data to insert_pool
// to be inserted into MySQL.
void ReadFromFile(const string& file_name,
                  ObjectThreads<DataInserter>* insert_pool,
                  bool hash_rows) {
  LOG(INFO) << "Reading from file: " << file_name;
  // Use a BufferPool to prevent heap fragmentation. Each row is approximately
  // 100k in size so we'll use that as our buffer size.
  const int kBufferSize = 100 << 10;
  BufferPool buffer_pool(kBufferSize);

  int fd = open(file_name.c_str(), O_RDONLY);
  if (fd < 0) {
    LogFatalErrno(
        errno, string("Error opening ") + file_name + " for reading");
  }

  LineRawParser parser(new DataInsertParseHandler(insert_pool, hash_rows));

  while (true) {
    unique_ptr<BPBuffer> buffer(buffer_pool.GetBuffer());
    int bytes_read = read(fd, buffer->buffer(), kBufferSize);
    if (bytes_read < 0) {
      LogFatalErrno(errno, string("Error reading from file ") + file_name);
    } else if (bytes_read == 0) {
      // This indicated EOR
      break;
    } else {
      Strand* data = new BPBufferStrand(buffer.release(), bytes_read);
      parser.DataReceived(data);
    }
  }
  LOG(INFO) << "All data in " << file_name << " added to MySQL";
}

// This finds all the files in dir_path and lanches a thread to read the data in
// each one. Those threads run the ReadFromFile method above and that uses the
// insert_pool to actually put the data in MySQL.  It will keep looking for
// files in the directory until num_files have been found. Once all files have
// been found this blocks, waiting for all the spawned threads to finish
// processing their files.
void DirectoryWatchLoop(const string& dir_path, 
                        int num_files,
                        ObjectThreads<DataInserter>* insert_pool, 
                        bool hash_rows) {
  // Maintain a map from file name to the the thread that is processing that
  // file. We need a map as we may need to read the directory several times.
  map<string, std::thread*> file_threads;

  // Once we've checked the directory once we'll wait a few seconds before
  // checking it again.
  bool wait = false;
  const int kNumWaitSeconds = 5;

  do {
    if (wait) {
      LOG(DEBUG) << "Directory reading thread sleeping for " << kNumWaitSeconds
          << " seconds. Will check for new files after that.";
      this_thread::sleep_for(chrono::seconds(kNumWaitSeconds));
    }

    DIR* dir = opendir(dir_path.c_str());
    if (dir == NULL) {
      LogFatalErrno(errno, string("Error opening directory ") + dir_path);
    }
    // Find all the existing files in the directory.
    struct dirent dir_entry;
    struct dirent* readdir_result_ptr;
    while (true) {
      readdir_r(dir, &dir_entry, &readdir_result_ptr);
      if (readdir_result_ptr == NULL) {
        break;
      }
      if (dir_entry.d_type != DT_REG && dir_entry.d_type != DT_FIFO) {
        LOG(DEBUG) << "Skipping non-file " << dir_entry.d_name;
        continue;
      }

      if (file_threads.find(dir_entry.d_name) == file_threads.end()) {
        LOG(INFO) << "Starting thread to read from file: " << dir_entry.d_name;

        std::thread* file_thread = new std::thread(
            [dir_entry, &dir_path, insert_pool, hash_rows]() {
              ReadFromFile(dir_path + "/" + dir_entry.d_name, 
                           insert_pool, 
                           hash_rows);
            });
        file_threads.insert(make_pair(dir_entry.d_name, file_thread));
        LOG(DEBUG) << "Running " << file_threads.size() << " threads";
      } else {
        LOG(DEBUG) << "Already reading from file " << dir_entry.d_name;
      }
    }
    wait = true;
    closedir(dir);
  } while (file_threads.size() < static_cast<size_t>(num_files));


  LOG(DEBUG) << "Waiting for all reading threads to complete";
  for (auto t = file_threads.begin(); t != file_threads.end(); ++t) {
    t->second->join();
    delete t->second;
  }
}

int main(int argc, char** argv) {
  Initialize();
  Log::SetOutputStream(&std::cerr);

  string host, user, pwd, db;
  string data_file_path, schema_file_path, stopwords_file_path,
         data_dir_path;
  int max_insert_threads, num_files;
  bool hash_rows = false;

  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print this help message")
      ("host", po::value<string>(&host)->default_value("localhost"),
       "MySQL host")
      ("user", po::value<string>(&user)->default_value("root"),
       "User name for MySQL connection")
      ("pwd", po::value<string>(&pwd), "Password for MySQL connection")
      ("db", po::value<string>(&db)->default_value("spar"),
       "Database to use")
      ("schema-file,f", po::value<string>(&schema_file_path),
       "Path to a file holding the schema info")
      ("num-files,n", po::value<int>(&num_files)->default_value(-1),
       "This will keep looking for new files in --data-dir until it has "
       "found this many files.")
      ("stopwords", po::value<string>(&stopwords_file_path),
       "Path to the file containing the stop words")
      ("data-dir,d", po::value<string>(&data_dir_path),
       "The directory to watch for files containing data.")
      ("log-level", po::value<int>()->default_value(1),
       "The logging level for the program. 0 = DEBUG, 1 = INFO, "
       "2 = WARNING, and 3 = ERROR")
      ("max-insert-threads",
       po::value<int>(&max_insert_threads)->default_value(100),
       "The number of threads to use for inserts into MySQL.")
       ("hash-rows", "If set, hashes of each row will be inserted into "
        "the database as well. Note that this requires a table to be defined "
        "in the file specified by -f/--schema-file named 'row_hashes' with "
        "the fields 'id' and 'hash'.");

  po::variables_map vm;

  try {
    po::store(po::parse_command_line(argc, argv, desc), vm);
  }
  catch (const boost::bad_any_cast &ex) {
    LOG(FATAL) << ex.what();
  }
  catch (const boost::program_options::invalid_option_value& ex) {
    LOG(FATAL) << ex.what();
  }


  po::notify(vm);    

  if (vm.count("help")) {
    cout << desc << endl;
    exit(0);
  }

  if (vm.count("hash-rows") > 0) {
    hash_rows = true;
  }

  CHECK(vm["log-level"].as<int>() >= 0 && vm["log-level"].as<int>() <= 3);
  Log::SetApplicationLogLevel(
      static_cast<LogLevel>(vm["log-level"].as<int>()));

  CHECK(num_files > 0)
      << "You must specify the number of files expected in --data-dir";

  SafeIFStream schema_file(schema_file_path.c_str());
  Schema schema(&schema_file);

  set<string> stop_words;
  GetStopWords(stopwords_file_path, &stop_words);

  // A closure that can construct a DataInserter
  auto data_inserter_factory =
      [host, user, pwd, db, &schema, &stop_words](){
        MySQLConnection* connection = new MySQLConnection(host, user, pwd, db);
        connection->Connect();
        return new DataInserter(auto_ptr<MySQLConnection>(connection),
                                &schema, stop_words);
      };

  ObjectThreads<DataInserter> insert_pool(data_inserter_factory);
  insert_pool.set_max_threads(max_insert_threads);

  DirectoryWatchLoop(data_dir_path, num_files, &insert_pool, hash_rows);
  LOG(INFO) << "All done! Shutting down.";
}
