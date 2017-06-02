//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            mjr
// Description:        A class to locate alarm words within a given
//                     string
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_ALARM_WORDS_H_
#define CPP_BASELINE_MYSQL_SERVER_ALARM_WORDS_H_

#include <string>
#include <vector>

class AlarmWords {
 public:
	/// Constructor using the default alarm word set
	AlarmWords();
	/// Constructor using a specified alarm word set
	AlarmWords(const std::vector<std::string>& alarm_words);
	virtual ~AlarmWords() {};

	/// Finds alarm words and proximity distance
	/// (if present), calculates the proximity, and returns
	/// an SQL statement to insert this data into the join table
	/// sets stmt to the empty string if (0 or 1) alarm words are found
	void GetInsertStatement(const std::string& index_table,
			const std::string& row_id, const std::string& column,
			const std::string& data, std::string* stmt);

 private:
	///Set alarm words
	void SetAlarmWords(const std::vector<std::string>& words);
	/// Returns the default list of alarm words.  Does *not*
	/// set the alarm word list.
	static std::vector<std::string> DefaultAlarmWords();

	/// Finds the alarm words and their locations within the given input
	/// Note that alarm words are case-insensitive
	void FindAlarms(const std::string input, std::vector<std::string>& alarms,
			std::vector<int>& locations);

	/// Convert to lower-case.  Proximity searches are
	/// case-insensitive
	static std::string MakeLower(const std::string& str);

	/// Constructs the SQL statement
	std::string GetSingleStatement(
	    const std::string& index_table, const std::string& row_id,
	    const std::string& column, const std::vector<std::string> words, const std::vector<int> locations);

	/// The raw alarm words
	std::vector<std::string> raw_alarms_;
	/// The alarm words, converted to lower case, then
	/// prepended/appended with a space
	std::vector<std::string> delimited_alarms_;
};

#endif // CPP_BASELINE_MYSQL_SERVER_ALARM_WORDS_H_
