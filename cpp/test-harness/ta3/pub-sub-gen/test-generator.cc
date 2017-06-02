#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>

#include "low-match-rate-pub-sub-gen.h"
#include "test-harness/ta3/fields/field-set.h"
#include "test-harness/ta3/fields/integer-field.h"
#include "num-predicate-generators.h"
#include "common/safe-file-stream.h"
#include "common/string-algo.h"
#include "common/statics.h"
#include "common/logging.h"

#include <algorithm>

namespace po = boost::program_options;
using namespace std;

// Helper function used to create inequality subscriptions
string CreateInequality(const FieldBase* field_base,
                        NumGenerator* gt_prob_gen,
                        NumGenerator* inclusive_prob_gen,
                        default_random_engine* generic_gen,
                        string& value_string) {
  if (!(*gt_prob_gen)()) {
    if ((*inclusive_prob_gen)()) {
      uniform_int_distribution<int> un_dist(
          SafeAtoi(value_string), 
          ((IntegerField*) field_base)->MaxValue());
      return field_base->name() + " <= " + itoa(un_dist(*generic_gen));
    } else {
      uniform_int_distribution<int> un_dist(
          SafeAtoi(value_string) + 1, 
          ((IntegerField*) field_base)->MaxValue());
      return field_base->name() + " < " + itoa(un_dist(*generic_gen));
    }
  } else {
    if ((*inclusive_prob_gen)()) {
      uniform_int_distribution<int> un_dist(
          ((IntegerField*) field_base)->MinValue(),
          SafeAtoi(value_string));
      return field_base->name() + " >= " + itoa(un_dist(*generic_gen));
    } else {
      uniform_int_distribution<int> un_dist(
          ((IntegerField*) field_base)->MinValue(),
          SafeAtoi(value_string) + 1);
      return field_base->name() + " > " + itoa(un_dist(*generic_gen));
    }
  }
}

// Helper function to generate matching publications for each item in a given
// set of subscriptions.
void AppendMatchingPublications(vector<EqualitySubscription>& subs_to_match,
  LowMatchRatePubSubGen* psg, vector<string>* pubs_for_sub, 
  size_t num_pubs_per_conj) {
  size_t max_pub_len = psg->MaxPublicationSize();
  char pub[max_pub_len];
  pub[0] = '\0';
  for (size_t l = 0; l < num_pubs_per_conj; l++) {
    while ((*pub) == '\0') {
      psg->GetPublication(subs_to_match.begin(), subs_to_match.end(), 
                          max_pub_len, pub);
    }
    pubs_for_sub->push_back(string(pub));
    pub[0] = '\0';
  }
}

// Helper function to expand generated subscriptions into equality and/or
// inequality predicates.
void GeneratePredicates(EqualitySubscription* sub, FieldSet* field_set, 
    NumGenerator* ineq_prob_gen, NumGenerator* gt_prob_gen, 
    NumGenerator* inclusive_prob_gen, default_random_engine* generic_gen, 
    vector<string>* conj_subs) {
  // Obtain all fields currently in conj_subs
  set<string> curr_fields;
  for (auto sub : *conj_subs) {
    curr_fields.insert(Split(sub, ' ')[0]);
  }
  int num_conj = sub->NumPredicates();
  for (int l = 0; l < num_conj; l++) {
    const EqualityCondition* cond = sub->GetCondition(l);
    const FieldBase* field_base = field_set->Get(cond->field());
    // If field is already in conj_subs, don't add this term
    if (curr_fields.find(field_base->name()) != curr_fields.end()) {
      continue;
    }
    curr_fields.insert(field_base->name());
    string value_string = cond->value();
    if (field_base->type() != "Integer" ||
        field_base->name() == "zip" ||
        field_base->name() == "ssn" ||
        field_base->name() == "dob") {
      value_string = "'" + value_string + "'";
    }
    // INEQUALITY TERM
    if (field_base->type() == "Integer" && (*ineq_prob_gen)()) {
      conj_subs->push_back(CreateInequality(field_base,
            gt_prob_gen, inclusive_prob_gen, generic_gen,
            value_string));
    // REGULAR TERM
    } else {
      conj_subs->push_back(field_base->name() + " = " + value_string);
    }
  }
}

int main(int argc, char** argv) {
  Initialize();

  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("field_file,f", po::value<string>(),
       "Path to the file that specifies which metadata fields will be active")
      ("output_dir,o", po::value<string>(),
       "The path to where output files should be placed")
      ("num_clients,c", po::value<size_t>()->default_value(5),
       "Number of clients to create subscriptions for")
      ("subs_per_client", po::value<string>()->default_value("POISSON 2"),
       "Distribution to use for # of subscriptions per client. "
       "Can be a string of the form 'CONSTANT x' or 'POISSON x'.")
      ("conjunction_size", po::value<string>()->default_value("POISSON 2"),
       "Distribution to use for # of predicates per conjunction. "
       "See the requirements for subs_per_client.")
      ("disjunction_prob", po::value<float>()->default_value(0.5),
       "Probability that a subscription will be a disjunction of terms. Note that if "
       "this is greater than 0, the effective match rate will likely be higher "
       "than what match_rate is set to.")
      ("disjunction_size", po::value<string>()->default_value("POISSON 2"),
       "Distribution to use for # of terms per disjunction. "
       "See the requirements for subs_per_client.")
      ("threshold_prob", po::value<float>()->default_value(0.0),
       "Probability that a disjoined term will be an at least "
       "threshold subscription. Only supported by ACS with single equalities.")
      ("num_pubs,p", po::value<size_t>()->default_value(1000),
       "Number of publications to generate.")
      ("inequality_prob", po::value<float>()->default_value(0.0),
       "Probability that a subscription involving a number field will be "
       "an inequality check. Only supported by Argon. Note that if this is "
       "greater than 0, the effective match rate will likely be higher than "
       "what match_rate is set to.")
      ("inclusive_prob", po::value<float>()->default_value(0.5),
       "Probability that an inequality subscription will be based on an "
       "inclusive range (otherwise, will be exclusive). Only supported by Argon.")
      ("gt_prob", po::value<float>()->default_value(0.5),
       "Probability that an inequality subscription will be based on a "
       "greater than comparison (otherwise, will be less than). Only supported "
       "by Argon.")
      ("negation_prob", po::value<float>()->default_value(0.0),
       "Probability that a multi-term conjunction or disjunction is "
       "negated via DeMorgan's Law.")
      ("match_rate", po::value<string>()->default_value("POISSON 2"),
       "Distribution to use for # of conjunctive equalities to match for each "
       "publication.")
      ("client_targeter", po::value<string>()->default_value("UNIFORM"),
       "Distribution to use for targeting clients with subscriptions. "
       "Currently unused.")
      ("rand_seed", po::value<int>()->default_value(0),
       "Random seed to use.")
      ("num_pubs_per_conj", po::value<size_t>()->default_value(0),
       "Number of publications to generate for each conjunctive equality; "
       "used to produce a set of publications that are guaranteed to match "
       "each client.")
      ("replication_factor", po::value<size_t>()->default_value(1),
       "Number of times each conjunctive equality will be used in the "
       "subscription set. Useful for generating high match rates.")
      ("overgeneration_factor", po::value<float>()->default_value(1.5),
       "Multiplier applied to the number of subscriptions to generate."
       "Should be set to 1 if there is no randomness in the generation "
       "parameters; otherwise, this should be greater than 1 to account "
       "for randomness in the cardinality of conjunctions, number of "
       "subscribers per client, etc. Note that if this is greater than 1, "
       "the effective match rate will be lower than what match_rate is set "
       "to.")
      ("keep_exhausted_fields", "If set, will ensure generation will keep "
       "exhausted fields for future generation. Useful for generating data "
       "with high cardinality conjunctions and/or limited field cardinalites.")
      ("verbose,v", "If set, will output all messages at DEBUG level and "
       "above. Otherwise, will output all messages at INFO level and above.");

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

  // Validate input arguments
  if (vm.count("help")) {
    std::cout << desc << std::endl;
    exit(0);
  }
  if (vm.count("verbose") > 0) {
    Log::SetApplicationLogLevel(DEBUG);
  } else {
    Log::SetApplicationLogLevel(INFO);
  }
  if (vm.count("field_file") == 0) {
    LOG(FATAL) << "You must supply the --field_file/-f option";
  }
  if (vm.count("output_dir") == 0) {
    LOG(FATAL) << "You must supply the --output_dir/-o option";
  }

  size_t num_clients = vm["num_clients"].as<size_t>();
  float disjunction_prob = vm["disjunction_prob"].as<float>();
  float threshold_prob = vm["threshold_prob"].as<float>();
  float inequality_prob = vm["inequality_prob"].as<float>();
  float gt_prob = vm["gt_prob"].as<float>();
  float inclusive_prob = vm["inclusive_prob"].as<float>();
  float negation_prob = vm["negation_prob"].as<float>();
  size_t num_pubs = vm["num_pubs"].as<size_t>();
  int rand_seed = vm["rand_seed"].as<int>();
  size_t num_pubs_per_conj = vm["num_pubs_per_conj"].as<size_t>();
  size_t replication_factor = vm["replication_factor"].as<size_t>();
  float overgeneration_factor = vm["overgeneration_factor"].as<float>();

  if (num_clients <= 0 || disjunction_prob < 0 || threshold_prob < 0 || 
      num_pubs <= 0 || num_pubs_per_conj < 0 || inequality_prob < 0) {
    LOG(FATAL) << "Check that you are not passing any negative/zero value "
               << "options that would not make sense.";
  }
  if (replication_factor < 1) {
    LOG(FATAL) << "Replication factor must be at least 1";
  }
  if (overgeneration_factor < 1.0) {
    LOG(FATAL) << "Overgeneration factor must be at least 1.0";
  }

  // Parse schema file and populate fields
  FieldSet field_set;
  SafeIFStream field_file(vm["field_file"].as<string>().c_str());
  field_set.AppendFromFile(&field_file);
  field_set.SetSeed(rand_seed);

  // Instantiate various random generators
  unique_ptr<NumGenerator> subs_per_client_gen;
  unique_ptr<NumGenerator> disj_card_gen;
  unique_ptr<NumGenerator> conj_card_gen;
  unique_ptr<NumGenerator> match_rate_gen;
  unique_ptr<NumGenerator> disj_prob_gen;
  unique_ptr<NumGenerator> thresh_prob_gen;
  unique_ptr<NumGenerator> ineq_prob_gen;
  unique_ptr<NumGenerator> gt_prob_gen;
  unique_ptr<NumGenerator> inclusive_prob_gen;
  unique_ptr<NumGenerator> negation_prob_gen;
  default_random_engine generic_gen(rand_seed);
  size_t avg_subs_per_client = 0;
  size_t avg_disj_card = 0;
  size_t avg_conj_card = 0;
  size_t avg_match_rate = 0;

  vector<string> parts = Split(vm["subs_per_client"].as<string>(), ' ');
  if (parts[0] == "POISSON") {
    avg_subs_per_client = SafeAtoi(parts[1]);
    if (replication_factor > num_clients) {
      LOG(WARNING) << "Replication factor may be such that the number of "
                   << "unique subscriptions is insufficient to prevent the "
                   << "same subscription from appearing on the same client. "
                   << "Consider setting overgeneration_factor larger than 1.";
    }
    subs_per_client_gen.reset(new
        TruncatedPoissonNumGenerator(avg_subs_per_client, rand_seed));
  } else if (parts[0] == "CONSTANT") {
    avg_subs_per_client = SafeAtoi(parts[1]);
    if (overgeneration_factor == 1) {
      CHECK(replication_factor <= num_clients) << "Replication factor must be "
        << "less than or equal to number of clients. Consider setting "
        << "overgeneration_factor larger than 1.";
    }
    subs_per_client_gen.reset(new ConstantNumGenerator(avg_subs_per_client));
  } else {
    LOG(FATAL) << "Did not recognize subs_per_client generator";
  }

  parts = Split(vm["disjunction_size"].as<string>(), ' ');
  if (parts[0] == "POISSON") {
    avg_disj_card = SafeAtoi(parts[1]);
    disj_card_gen.reset(new TruncatedPoissonNumGenerator(avg_disj_card, rand_seed));
  } else if (parts[0] == "CONSTANT") {
    avg_disj_card = SafeAtoi(parts[1]);
    disj_card_gen.reset(new ConstantNumGenerator(avg_disj_card));
  } else {
    LOG(FATAL) << "Did not recognize disjunction_size generator";
  }

  parts = Split(vm["conjunction_size"].as<string>(), ' ');
  if (parts[0] == "POISSON") {
    avg_conj_card = SafeAtoi(parts[1]);
    conj_card_gen.reset(new TruncatedPoissonNumGenerator(avg_conj_card, rand_seed));
  } else if (parts[0] == "CONSTANT") {
    avg_conj_card = SafeAtoi(parts[1]);
    conj_card_gen.reset(new ConstantNumGenerator(avg_conj_card));
  } else {
    LOG(FATAL) << "Did not recognize conjunction_size generator";
  }

  parts = Split(vm["match_rate"].as<string>(), ' ');
  if (parts[0] == "POISSON") {
    avg_match_rate = SafeAtoi(parts[1]);
    if (avg_match_rate <= num_clients*avg_subs_per_client - 1) {
      LOG(WARNING) << "Match rate will likely exceed expected total "
                   << "number of subscriptions, which may make "
                   << "publication generation take longer";
    }
    match_rate_gen.reset(new TruncatedPoissonNumGenerator(avg_match_rate,
          rand_seed));
  } else if (parts[0] == "CONSTANT") {
    avg_match_rate = SafeAtoi(parts[1]);
    CHECK(avg_match_rate <= num_clients*avg_subs_per_client) << 
      "Match rate exceeds expected total number of subscriptions.";
    match_rate_gen.reset(new ConstantNumGenerator(avg_match_rate));
  } else {
    LOG(FATAL) << "Did not recognize match_rate generator";
  }

  disj_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, disjunction_prob, rand_seed));
  thresh_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, threshold_prob, rand_seed));
  ineq_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, inequality_prob, rand_seed));
  gt_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, gt_prob, rand_seed));
  inclusive_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, inclusive_prob, rand_seed));
  negation_prob_gen.reset(
      new CoinTossNumGenerator(1, 0, negation_prob, rand_seed));

  // Determine number of EqualitySubscriptions to create
  size_t num_subs = 
    size_t(
      float(num_clients * avg_subs_per_client) * (
        (1 - disjunction_prob) +
        disjunction_prob * float(avg_disj_card) * (
          threshold_prob + 1)) *
      overgeneration_factor / float(replication_factor));

  // Print out summary of parameter selections
  LOG(INFO) << "Test generation parameters:";
  LOG(INFO) << "    Random seed of " << rand_seed;
  LOG(INFO) << "    " << field_set.Size() << " possible fields";
  LOG(INFO) << "    " << num_clients << " clients";
  LOG(INFO) << "    ~" << avg_subs_per_client << " subs per client";
  LOG(INFO) << "    ~" << disjunction_prob*100 << "% of subs will be disjunctions "
                      << "(rest will be conjunctions)";
  LOG(INFO) << "    ~" << threshold_prob*100 << "% of disjoined terms will be thresholds";
  LOG(INFO) << "    ~" << inequality_prob*100 << "% of terms on number fields "
            << "will be inequalities";
  LOG(INFO) << "    ~" << gt_prob*100 << "% of inequalities on number fields "
            << "will be 'greater than'";
  LOG(INFO) << "    ~" << inclusive_prob*100 << "% of inequalities on number fields "
            << "will be inclusive";
  LOG(INFO) << "    ~" << negation_prob*100 << "% of multi-term top-level "
            << "conjunctions or disjunctions will be negated via DeMorgan's";
  LOG(INFO) << "    ~" << avg_conj_card << " terms in each conjunction";
  LOG(INFO) << "    ~" << avg_disj_card << " terms in each disjunction";
  LOG(INFO) << "    " << num_pubs << " publications";
  LOG(INFO) << "    ~" << avg_match_rate << " conjunctions matched "
            << "per publication";
  LOG(INFO) << "    Using replication factor of " << replication_factor;
  LOG(INFO) << "    Using overgeneration factor of " << overgeneration_factor;
  if (vm.count("keep_exhausted_fields") > 0) {
    LOG(INFO) << "    Recycling exhausted fields"; 
  }
  LOG(INFO) << "Creating " << num_subs << " conjunctive subscriptions. "
            << "These will be used as the basis for more complex "
            << "subscriptions (e.g., disjunctions of conjunctions, " 
            << "at least thresholds, etc.)";

  // Instantiate subscription generator and generate all conjunctive
  // subscriptions
  LowMatchRatePubSubGen psg(&field_set, rand_seed, vm.count("keep_exhausted_fields") > 0);
  psg.GenerateSubscriptions(num_subs, std::ref(*conj_card_gen));

  // Print out more info about the generated subscriptions for debug purposes
  const vector<vector<EqualitySubscription>>* all_subsets = psg.GetAllSubsets();
  LOG(DEBUG) << "Generated " << all_subsets->size() << " subsets";
  for (size_t i = 0; i < all_subsets->size(); i++) {
    LOG(DEBUG) << "Subset " << i << " has " <<  (all_subsets->at(i)).size()
               << " subscriptions";
  }
  LowMatchRatePubSubGen::SubsetIterator subset_start, subset_end;
  for (size_t i = 1; i <= field_set.Size(); i++) {
    psg.GetSubsetsGE(i, &subset_start, &subset_end);
    LOG(DEBUG) << (subset_end - subset_start) << " sets with >= " << i << 
      " subscriptions";
  }
  LOG(DEBUG) << "Printing out all generated conjunctive subscriptions "
             << "([subset number][subscription number])...";
  vector<EqualitySubscription>* all_subs = new vector<EqualitySubscription>();
  for (size_t i = 0; i < all_subsets->size(); i++) {
    for (size_t j = 0; j < (all_subsets->at(i)).size(); j++) {
      EqualitySubscription sub = (all_subsets->at(i)).at(j);
      all_subs->push_back(sub);
      LOG(DEBUG) << "[" << i << "][" << j << "] " << sub.ToString();
    }
  }

  // Shuffle subscriptions randomly distribute compatible subsets to different
  // clients
  random_shuffle(all_subs->begin(), all_subs->end(), 
      [&] (int i) { std::uniform_int_distribution<int> distribution(0,i-1);
                    return distribution(generic_gen);});

  // Replicate subscriptions as needed
  size_t num_orig_subs = all_subs->size();
  for (size_t i = 0; i < replication_factor - 1; i++) {
    for (size_t j = 0; j < num_orig_subs; j++) {
      all_subs->push_back(all_subs->at(j));
    }
  }

  // Generate more complex subscriptions as needed and map them to clients
  num_subs = num_subs*replication_factor;
  int rem_subs = num_subs;
  map<size_t, vector<string>> all_sql_subs;
  map<size_t, vector<vector<string>>> all_pub_per_sub;
  for (size_t i = 0; i < num_clients; i++) {
    // Determine number of subscriptions for this client
    int num_client_subs = (*subs_per_client_gen)();
    LOG(DEBUG) << "Client #" << i << " has " << num_client_subs << 
      " subscriptions";
    vector<string> sql_subs;
    // Generate each subscription for this client
    for (int j = 0; j < num_client_subs; j++) {
      vector<string> pubs_for_sub;
      // Determine if this subscription will be a disjunction of terms
      int value = (*disj_prob_gen)();

      // DISJUNCTION OF CONJUNCTIONS
      if (value) {
        // Determine number of disjoined conjunctions
        CHECK(rem_subs > 0) << "Ran out of generated conjunctive equalities. "
          << "Consider setting the overgeneration factor to something higher.";
        int num_disj = std::min((*disj_card_gen)(), rem_subs);
        LOG(DEBUG) << "Generating disjunction with " << num_disj << " terms";
        vector<string> disj_subs;
        // Build disjunction out of individual conjunctions
        for (int k = 0; k < num_disj; k++) {
          CHECK(all_subs->size() > num_subs-rem_subs) << "Ran out of "
            << "generated conjunctive equalities. Consider setting the "
            << "overgeneration factor to something higher.";
          EqualitySubscription sub = all_subs->at(num_subs-rem_subs);

          // Generate matching publications for this conjunction
          vector<EqualitySubscription> subs_to_match;
          subs_to_match.push_back(sub);
          AppendMatchingPublications(subs_to_match, &psg, &pubs_for_sub,
              num_pubs_per_conj);

          // Generate each predicate for this conjunction
          vector<string> conj_subs;
          GeneratePredicates(&sub, &field_set, ineq_prob_gen.get(),
              gt_prob_gen.get(), inclusive_prob_gen.get(), &generic_gen,
              &conj_subs);
          int num_conj = sub.NumPredicates();
          LOG(DEBUG) << "Processing conjunction with " << num_conj << " terms";

          // Build SQL string for this conjunction
          if (num_conj == 0) {
            LOG(FATAL) << "This should never happen!";

          // DISJUNCTIVE TERM BASED ON SINGLE-CONJUNCTION PREDICATE
          } else if (num_conj == 1) {

            // AT LEAST THRESHOLD DISJUNCTIVE TERM
            if ((*thresh_prob_gen)()) {
              LOG(DEBUG) << "Creating a threshold subscription with one "
                         << "positive term";
              string thresh_sql;
              vector<string> thresh_preds;
              rem_subs -= 1;
              CHECK(all_subs->size() > num_subs-rem_subs) << "Ran out of "
                << "generated conjunctive equalities. Consider setting the "
                << "overgeneration factor to something higher.";
              EqualitySubscription thresh_sub = all_subs->at(num_subs-rem_subs);
              thresh_sql += "M_OF_N(1,";
              int num_thresh_conj = thresh_sub.NumPredicates();
              LOG(DEBUG) << "Processing conjunction with " << num_thresh_conj << " terms";
              // Add matching predicates of threshold subscription
              thresh_preds.push_back(conj_subs[0]);
              // Determine non-matching predicates of threshold subscription
              GeneratePredicates(&thresh_sub, &field_set, ineq_prob_gen.get(),
                  gt_prob_gen.get(), inclusive_prob_gen.get(), &generic_gen,
                  &thresh_preds);
              thresh_sql += itoa(thresh_preds.size()) + ",";
              // Shuffle threshold predicates
              random_shuffle(thresh_preds.begin(), thresh_preds.end(),
                [&] (int i) { uniform_int_distribution<int> distribution(0,i-1);
                    return distribution(generic_gen);});
              // Complete SQL string
              thresh_sql += Join(thresh_preds, string(","));
              thresh_sql += ")";
              disj_subs.push_back(thresh_sql);

            // SIMPLE DISJUNCTIVE TERM
            } else {
              disj_subs.push_back(conj_subs[0]);
            }

          // DISJUNCTIVE TERM BASED ON MULTI-CONJUNCTION PREDICATE
          } else {

            // AT LEAST THRESHOLD DISJUNCTIVE TERM
            if ((*thresh_prob_gen)()) {
              LOG(DEBUG) << "Creating a threshold subscription with " 
                         << num_conj << " positive terms";
              string thresh_sql;
              vector<string> thresh_preds;
              rem_subs -= 1;
              CHECK(all_subs->size() > num_subs-rem_subs) << "Ran out of "
                << "generated conjunctive equalities. Consider setting the "
                << "overgeneration factor to something higher.";
              LOG(DEBUG) << "Using index " << num_subs-rem_subs;
              EqualitySubscription thresh_sub = all_subs->at(num_subs-rem_subs);
              LOG(DEBUG) << "Read out sub: " << thresh_sub.ToString();
              thresh_sql += "M_OF_N(" + itoa(num_conj) + ",";
              int num_thresh_conj = thresh_sub.NumPredicates();
              LOG(DEBUG) << "Processing conjunction with " << num_thresh_conj << " terms";
              // Add matching predicates of threshold subscription
              for (int l = 0; l < num_conj; l++) {
                thresh_preds.push_back(conj_subs[l]);
              }
              // Determine non-matching predicates of threshold subscription
              GeneratePredicates(&thresh_sub, &field_set, ineq_prob_gen.get(),
                  gt_prob_gen.get(), inclusive_prob_gen.get(), &generic_gen,
                  &thresh_preds);
              thresh_sql += itoa(thresh_preds.size()) + ",";
              // Shuffle threshold predicates
              random_shuffle(thresh_preds.begin(), thresh_preds.end(),
                [&] (int i) { uniform_int_distribution<int> distribution(0,i-1);
                    return distribution(generic_gen);});
              // Complete SQL string
              thresh_sql += Join(thresh_preds, string(","));
              thresh_sql += ")";
              disj_subs.push_back(thresh_sql);

            // SIMPLE DISJUNCTIVE TERM
            } else {
              string conj_sql;
              int value = (*negation_prob_gen)();
              // Group each conjunction by parentheses
              for (int k = 0; k < num_conj; k++) {
                if (value) {
                  conj_sql += "(NOT " + conj_subs[k] + ")";
                } else {
                  conj_sql += "(" + conj_subs[k] + ")";
                }
                if (k < num_conj - 1) {
                  if (value) {
                    conj_sql += " OR "; 
                  } else {
                    conj_sql += " AND "; 
                  }
                }
              }
              if (value) {
                conj_sql = "NOT (" + conj_sql + ")";
              }
              disj_subs.push_back(conj_sql);
            }
          }

          // Update index to use for next subscription retrieval
          rem_subs -= 1;
        }

        // Build SQL-esque string for disjunction
        if (num_disj == 0) {
          LOG(FATAL) << "This should never happen!";

        // SINGLE TERM DISJUNCTION
        } else if (num_disj == 1) {
          sql_subs.push_back(disj_subs[0]);

        // MULTIPLE TERM DISJUNCTION
        } else {
          string disj_sql;
          int value = (*negation_prob_gen)();
          // Group each conjunction by parentheses
          for (int k = 0; k < num_disj; k++) {
            if (value) {
              disj_sql += "(NOT " + disj_subs[k] + ")";
            } else {
              disj_sql += "(" + disj_subs[k] + ")";
            }
            if (k < num_disj - 1) {
              if (value) {
                disj_sql += " AND "; 
              } else {
                disj_sql += " OR "; 
              }
            }
          }
          if (value) {
            disj_sql = "NOT (" + disj_sql + ")";
          }
          sql_subs.push_back(disj_sql);
        }

      // CONJUNCTION-ONLY SUBSCRIPTION
      } else {
        LOG(DEBUG) << "Using index " << num_subs-rem_subs;
        CHECK(all_subs->size() > num_subs-rem_subs) << "Ran out of "
          << "generated conjunctive equalities. Consider setting the "
          << "overgeneration factor to something higher.";
        EqualitySubscription sub = all_subs->at(num_subs-rem_subs);
        LOG(DEBUG) << "Read out sub: " << sub.ToString();

        // Generate matching publications for this conjunction
        vector<EqualitySubscription> subs_to_match;
        subs_to_match.push_back(sub);
        AppendMatchingPublications(subs_to_match, &psg, &pubs_for_sub,
            num_pubs_per_conj);

          // Generate each predicate for this conjunction
        vector<string> conj_subs;
        GeneratePredicates(&sub, &field_set, ineq_prob_gen.get(),
            gt_prob_gen.get(), inclusive_prob_gen.get(), &generic_gen,
            &conj_subs);
        int num_conj = sub.NumPredicates();

        // Build SQL-esque string for this conjunction
        if (num_conj == 0) {
          LOG(FATAL) << "This should never happen!";

        // SINGLE-TERM CONJUNCTION
        } else if (num_conj == 1) {
          sql_subs.push_back(conj_subs[0]);

        // MULTI-TERM CONJUNCTION
        } else {
          string conj_sql;
          int value = (*negation_prob_gen)();
          // Group each conjunction by parentheses
          for (int k = 0; k < num_conj; k++) {
            if (value) {
              conj_sql += "(NOT " + conj_subs[k] + ")";
            } else {
              conj_sql += "(" + conj_subs[k] + ")";
            }
            if (k < num_conj - 1) {
              if (value) {
                conj_sql += " OR "; 
              } else {
                conj_sql += " AND "; 
              }
            }
          }
          if (value) {
            conj_sql = "NOT (" + conj_sql + ")";
          }
          sql_subs.push_back(conj_sql);
        }

        // Update index to use for next subscription retrieval
        rem_subs -= 1;
      } 

      // Update publications for the conjunctive term that this subscription is
      // based on
      all_pub_per_sub[i].push_back(pubs_for_sub);
    }

    // Update vector of all subscriptions
    all_sql_subs[i] = sql_subs;
  }

  LOG(INFO) << "Wasted " << rem_subs << " equality conjunctions";

  // Print pubs per sub to output file
  if (num_pubs_per_conj > 0) {
    SafeOFStream pub_per_sub_file;
    string pub_per_sub_path = vm["output_dir"].as<string>() +
      "all-pubs-for-each-sub";
    pub_per_sub_file.open(pub_per_sub_path.c_str());
    for (auto pub_per_sub_map : all_pub_per_sub) {
      for (size_t i = 0; i < pub_per_sub_map.second.size(); i++) {
        for (size_t j = 0; j < pub_per_sub_map.second[i].size(); j++) {
        pub_per_sub_file << pub_per_sub_map.first << " " 
                         << i << " " << pub_per_sub_map.second[i][j] << endl;
        }
      }
    }
  }

  // Print subscription mapping to output file
  SafeOFStream sub_output_file;
  string sub_output_path = vm["output_dir"].as<string>() + "all-subscriptions";
  sub_output_file.open(sub_output_path.c_str());
  for (auto sub_map : all_sql_subs) {
    for (size_t i = 0; i < sub_map.second.size(); i++) {
      sub_output_file << sub_map.first << " " << i << " " << sub_map.second[i] << endl;
    }
  }
  sub_output_file.close();

  // Generate publications for all conjunctive subscriptions
  LOG(INFO) << "Generating publications. If this hangs for a long time, it's "
            << "possible the field set size, number of requested "
            << "subscriptions, and cardinality of conjunctions is such that "
            << "it is impossible to achieve the desired match rate. Consider "
            << "lowering the match rate, setting the keep_exhausted_fields "
            << "flag, expanding the field set, or lowering the number of "
            << "requested subscriptions and/or cardinality of conjunctions.";
  SafeOFStream pub_output_file;
  string pub_output_path = vm["output_dir"].as<string>() + "all-publications";
  pub_output_file.open(pub_output_path.c_str());
  SafeOFStream pub_match_file;
  string pub_match_path = vm["output_dir"].as<string>() + "all-pub-matches";
  pub_match_file.open(pub_match_path.c_str());
  // TODO how to do better targeting of clients?
  size_t max_pub_len = psg.MaxPublicationSize();
  char pub[max_pub_len];
  pub[0] = '\0';
  vector<EqualitySubscription> matching_subs;
  for (size_t i = 0; i < num_pubs; i++) {
    // Loop until a publication is found that can match the desired number of
    // matches
    while ((*pub) == '\0') {
      int num_matches = (*match_rate_gen)();
      matching_subs = psg.GetPublication(num_matches, max_pub_len, pub);
    }

    // Print out which conjunctive expressions this publication will match
    // TODO easier way to map this to actual subscriptions, and not just the
    // conjunctive expression they were based on?
    for (auto match_sub : matching_subs) {
      vector<string> conj_subs;
      GeneratePredicates(&match_sub, &field_set, ineq_prob_gen.get(),
          gt_prob_gen.get(), inclusive_prob_gen.get(), &generic_gen,
          &conj_subs);
      int num_conj = match_sub.NumPredicates();

      // Build SQL-esque string for this conjunction
      if (num_conj == 0) {
      } else if (num_conj == 1) {
        pub_match_file << i << " " << conj_subs[0] << endl;
      } else {
        string conj_sql;
        for (int k = 0; k < num_conj; k++) {
          // Group each conjunction by parentheses
          conj_sql += "(" + conj_subs[k] + ")";
          if (k < num_conj - 1) {
            conj_sql += " AND "; 
          }
        }
        pub_match_file << i << " " << conj_sql << endl;
      }
    }

    // Print out publication to file
    pub_output_file << "METADATA\n" << pub << endl;
    pub[0] = '\0';
  }

  // Wrap up
  pub_output_file.close();
  pub_match_file.close();
  LOG(INFO) << "Data generation complete.";
}
