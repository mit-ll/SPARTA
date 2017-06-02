//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            mjr
// Description:        Unit tests for AlarmWords
//*****************************************************************


#define BOOST_TEST_MODULE AlarmWords

#include "../../common/test-init.h"

#include "alarm-words.h"

#include <string>
#include <vector>

using std::string;
using std::vector;

BOOST_AUTO_TEST_CASE(SpecialAlarmWords) {

	vector<string> alarms;
	alarms.push_back("frumious");
	alarms.push_back("Jubjub");
	alarms.push_back("tumtum");
	alarms.push_back("manxome");
	alarms.push_back("Tulgey");
	alarms.push_back("UFFISH");
	alarms.push_back("galumphing");
	alarms.push_back("chortled");
	alarms.push_back("beam");

	string line1 = "'Twas brillig, and the slithy toves Did gyre and gimble in the wabe; All mimsy were the borogoves, And the mome raths outgrabe.";
	string line2 = "Beware the Jabberwock, my son! The jaws that bite, the claws that catch! Beware the Jubjub bird, and shun The frumious Bandersnatch!";
	string line3 = "He took his vorpal sword in hand: Long time the manxome foe he sought— So rested he by the Tumtum tree, And stood awhile in thought.";
	string line4 = "And as in uffish thought he stood, The Jabberwock, with eyes of flame, Came whiffling through the tulgey wood, And burbled as it came!";
	string line5 = "One, two! One, two! and through and through	The vorpal blade went snicker-snack! He left it dead, and with its head He went galumphing back.";
	string line6 = "\"And hast thou slain the Jabberwock? Come to my arms, my beamish boy! O frabjous day! Callooh! Callay!\" He chortled in his joy.";
	string line7 = "'Twas brillig, and the slithy toves Did gyre and gimble in the wabe; All mimsy were the borogoves, And the mome raths outgrabe";

	std::string table_name = "alarms_table";
	std::string row_id = "12345";
	std::string column_name = "notes1";
	std::string result;

	AlarmWords aw(alarms);

	// no matches expected
	aw.GetInsertStatement(table_name, row_id, column_name, line1, &result);
	BOOST_CHECK_EQUAL(result.size(), 0);
	aw.GetInsertStatement(table_name, row_id, column_name, line5, &result);
	BOOST_CHECK_EQUAL(result.size(), 0);
	aw.GetInsertStatement(table_name, row_id, column_name, line6, &result);
	BOOST_CHECK_EQUAL(result.size(), 0);
	aw.GetInsertStatement(table_name, row_id, column_name, line7, &result);
	BOOST_CHECK_EQUAL(result.size(), 0);

	// matches expected
	aw.GetInsertStatement(table_name, row_id, column_name,
			line2, &result);
	BOOST_CHECK(result.find("INSERT") != string::npos);
	BOOST_CHECK(result.find("20") != string::npos); // distance
	BOOST_CHECK(result.find("frumious") != string::npos);
	BOOST_CHECK(result.find("Jubjub") != string::npos);
	BOOST_CHECK(result.find("12345") != string::npos);
	BOOST_CHECK(result.find("notes1") != string::npos);
	BOOST_CHECK(result.find("alarms_table") != string::npos);
	aw.GetInsertStatement(table_name, row_id, column_name,
			line3, &result);
	BOOST_CHECK(result.find("INSERT") != string::npos);
	BOOST_CHECK(result.find("36")); // distance
	BOOST_CHECK(result.find("tumtum") != string::npos);
	BOOST_CHECK(result.find("manxome") != string::npos);
	BOOST_CHECK(result.find("12345") != string::npos);
	BOOST_CHECK(result.find("notes1") != string::npos);
	BOOST_CHECK(result.find("alarms_table") != string::npos);
	aw.GetInsertStatement(table_name, row_id, column_name,
			line4, &result);
	BOOST_CHECK(result.find("INSERT") != string::npos);
	BOOST_CHECK(result.find("82") != string::npos); // distance
	BOOST_CHECK(result.find("UFFISH") != string::npos);
	BOOST_CHECK(result.find("Tulgey") != string::npos);
	BOOST_CHECK(result.find("12345") != string::npos);
	BOOST_CHECK(result.find("notes1") != string::npos);
	BOOST_CHECK(result.find("alarms_table") != string::npos);

}

