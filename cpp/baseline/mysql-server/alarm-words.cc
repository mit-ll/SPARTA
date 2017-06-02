//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            mjr
// Description:        Implementation of AlarmWords
//*****************************************************************

#include "alarm-words.h"
#include "alarm-words-default.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <cstring>

using std::string;
using std::vector;

AlarmWords::AlarmWords() {
	SetAlarmWords(AlarmWords::DefaultAlarmWords());
}

AlarmWords::AlarmWords(const vector<string>& alarm_words) {
	SetAlarmWords(alarm_words);
}


void AlarmWords::GetInsertStatement(const string& index_table,
	const string& row_id, const string& column,
	const string& data, std::string* stmt) {

	vector<string> alarms;
	vector<int> locations;

	FindAlarms(data, alarms, locations);

	(*stmt) = GetSingleStatement(index_table, row_id, column, alarms, locations);

}

void AlarmWords::FindAlarms(const string input, vector<string>& alarms, vector<int>& locations) {

	string lower_input = MakeLower(input);

	for (unsigned int i = 0; i < delimited_alarms_.size(); ++i) {
		size_t pos = lower_input.find(delimited_alarms_[i]);
		if (pos != string::npos) {
			alarms.push_back(raw_alarms_[i]);
			// The delimited alarm has a leading space
			// Add 1 to position to to get the offset
			// of the raw alarm
			locations.push_back(pos+1);
		}
	}
}


string AlarmWords::GetSingleStatement(
    const string& index_table, const string& row_id,
    const string& column, const vector<string> words, const vector<int> locations) {

	// There must be exactly two alarms to generate an insert statement
	if (words.size() != 2 || locations.size() != 2) {
		return "";
	}

	// Distance is the number of bytes between the end of the
	// First word and the beginning of the last word
	// First, take the absolute value of the difference in their locations
	int distance = abs(locations[0] - locations[1]);
	// Then, subtract the length of the first word
	if (locations[0] < locations[1]) {
		distance -= words[0].size();
	}
	else {
		distance -= words[1].size();
	}

	// Now, create the insert statement
	// Use double-quotes in case an alarm-word contains a single quote
	string stmt = "INSERT INTO " + index_table + " (id, word1, word2, field, distance) VALUES(" +
			row_id + ",\"" + words[0] + "\",\"" + words[1] + "\",\"" + column + "\"," + std::to_string(distance) + ")";

	return stmt;
}


void AlarmWords::SetAlarmWords(const vector<string>& words) {
	// Alarm words are *words*, and should not match
	// against substrings of non-alarm words
	// (if 'own' is an alarm word, the string
	// "the fence is brown" should not match as
	// containing 'own'.
	// Thus we append a space to the beginning/end of each
	// alarm word to prevent this from happening
	// (data generation promises that alarms words will
	// not be the first or last word in a field, and that
	// they will have a space on each side (and not punctuation).
	raw_alarms_.clear();
	delimited_alarms_.clear();

	vector<string>::const_iterator words_it;
	for (words_it = words.begin(); words_it != words.end(); ++words_it) {
		raw_alarms_.push_back(*words_it);
		delimited_alarms_.push_back(" " + AlarmWords::MakeLower(*words_it) + " ");
	}
}

vector<string> AlarmWords::DefaultAlarmWords() {
	int i = 0;
	vector<string> result;

	while (default_alarms[i] != 0) {
		result.push_back(default_alarms[i]);
		++i;
	}

	return result;
}

string AlarmWords::MakeLower(const string& str) {
	string lower = str;
	std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
	return lower;
}


