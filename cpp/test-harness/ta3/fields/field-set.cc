//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of FieldSet 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Jan 2013   omd            Original Version
//*****************************************************************

#include "field-set.h"

#include "common/safe-file-stream.h"
#include "common/string-algo.h"
#include "date-field.h"
#include "equi-probable-closed-set-field.h"
#include "integer-field.h"

using std::string;

FieldSet::FieldSet() {
  SetupFactories();
}

FieldSet::~FieldSet() {
  for (auto f : fields_) {
    delete f;
  }
}

void FieldSet::AddField(std::unique_ptr<FieldBase> field) {
  fields_.push_back(field.release());
}

const FieldBase* FieldSet::Get(size_t i) const {
  DCHECK(i < fields_.size());
  return fields_[i];
}

void FieldSet::AppendFromFile(std::istream* fields_file) {
  while (fields_file->good()) {
    string line;
    getline(*fields_file, line);
    if (line.empty() || line[0] == '#') {
      continue;
    }
    size_t name_end = line.find(' ');
    CHECK(name_end != string::npos)
        << "Illegal line in fields file:\n" << line;
    string name = line.substr(0, name_end);
    size_t factory_end = line.find(' ', name_end + 1);
    CHECK(factory_end != string::npos)
        << "Illegal line in fields file:\n" << line;
    string factory_name = line.substr(name_end + 1, factory_end - name_end - 1);
    CHECK(factory_map_.find(factory_name) != factory_map_.end())
        << "No field factory named " << factory_name
        << ". Error parsing line in fields file:\n" << line;

    string config_data = line.substr(factory_end + 1, string::npos);
    std::unique_ptr<FieldBase> field(
        factory_map_[factory_name](name, config_data));
    AddField(std::move(field));
  }
  CHECK(fields_file->eof()) << "Error reading set of fields from file.";
}

void FieldSet::AddFieldFactory(const string& factory_name,
                               FieldFactory factory) {
  CHECK(factory_map_.find(factory_name) == factory_map_.end())
      << "Factory " << factory_name << " already registered";
  factory_map_[factory_name] = factory;
}

void FieldSet::SetSeed(int seed) {
  // In order to prevent all the fields from generating values in sync we keep
  // incrementing the seed for each field.
  int seed_inc = 0;
  for (auto f : fields_) {
    f->SetSeed(seed + seed_inc);
    ++seed_inc;
  }
}

size_t FieldSet::TotalMaxLength() const {
  size_t result = 0;
  for (const auto& f : fields_) {
    result += f->MaxLength();
  }
  return result;
}

////////////////////////////////////////////////////////////////////////////////
// FieldFactories and SetupFactories method.
////////////////////////////////////////////////////////////////////////////////

FieldBase* EquiProbableClosedSetFactory(const string& name,
                                        const string& values_filename) {
  SafeIFStream values_file(values_filename.c_str());
  return new EquiProbableClosedSetField(name,  &values_file);
}

// Constructs a DateField from a line that contains the start and end dates.
FieldBase* DateFieldFactory(const string& name, const string& date_spec) {
  std::vector<string> dates = Split(date_spec, ' ');
  CHECK(dates.size() == 2)
      << "Unexpected format for DateField. Expected two space separated dates "
      << "found '" << date_spec << "'";
  return new DateField(name, dates[0], dates[1]);
}

// A factory that whose config string is assumed to be a space-separated triple.
// The first value should be a printf-style format string specifying how the
// integers should be formatted. The other two values indicate the range
// (inclusive start, exclusive end) of values that should be generated.
inline FieldBase* IntegerFieldFactory(const std::string& name,
                                      const std::string& config) {
  auto config_values = Split(config, ' ');
  CHECK(config_values.size() == 3);
  return new IntegerField(
      name, config_values[0],
      SafeAtoi(config_values[1]), SafeAtoi(config_values[2]));
}

// TODO(odain) Currently this uses a fixed mapping from names to facotries. It
// might be worthwhile to consider a more flexible design in which field types
// can register themselves with the FieldSet.
void FieldSet::SetupFactories() {
  AddFieldFactory("EquiProbableClosedSet", &EquiProbableClosedSetFactory);
  AddFieldFactory("DateField", &DateFieldFactory);
  AddFieldFactory("IntegerField", &IntegerFieldFactory);
}
