//****************************************************************
// Copyright MIT Lincoln Laboratory
// Project:       SPAR
// Authors:       Yang
// Description:   Unit tests for Stealth circuit scanner/parser.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 16 Aug 2012   yang           Original Version
//****************************************************************

#define BOOST_TEST_MODULE StealthParserTest

#include <cstdlib>
#include <stdio.h>
#include <typeinfo>
#include <boost/shared_ptr.hpp>

#include "stealth-circuit-gates.h"
#include "stealth-def.h"
#include "../common/lex-global.h"
#include "../common/flex-def.h"
#include "../common/lemon-def.h"
#include "../../../common/test-init.h"
#include "../../../common/logging.h"

using namespace boost;

// Runs the Lemon circuit parser on a string, storing its state information in
// ParserState.
void parse(ParserState* parser_state, const std::string& circuit) {
  
  YYSTYPE yylval;
  yyscan_t scanner;
  yylex_init_extra(yylval, &scanner);
  void* stealth_parser = ParseAlloc(malloc);
  YY_BUFFER_STATE buffer_state = yy_scan_string(circuit.c_str(), scanner);

  int lexcode;
  do {
    lexcode = yylex(scanner);
    Parse(stealth_parser, lexcode, yyget_extra(scanner), parser_state);
  } while (lexcode > 0);

  if (lexcode == -1) {
    LOG(FATAL) << "Scanner encountered error";
  }
  yy_delete_buffer(buffer_state, scanner);
  yylex_destroy(scanner);
  ParseFree(stealth_parser, free);
}

// A simple circuit with just two inputs and an output gate.
BOOST_AUTO_TEST_CASE(SimpleCircuit) {
  ParserState parser_state;
  std::string circuit = "W=2 output_gate: AND(W0,W1)";
  parse(&parser_state, circuit);

  // Verify output gate is an And gate. If not, dynamic_cast will return a NULL
  // pointer.
  shared_ptr<And> output_gate = dynamic_pointer_cast<And> 
      (parser_state.output_gate);
  BOOST_REQUIRE(output_gate != NULL);
  BOOST_CHECK_EQUAL(output_gate->NumInputs(), 2);

  // Verify the inputs are all of type Wire.
  for (int i = 0; i < output_gate->NumInputs(); ++i) {
    BOOST_CHECK(dynamic_pointer_cast<Wire> 
                (output_gate->GetInput(i)) != NULL);
  }

  delete parser_state.wires;
}


// A circuit with more inputs and depth, also using labels.
BOOST_AUTO_TEST_CASE(CompoundCircuit) {
  ParserState parser_state;
  std::string circuit = "W=3 \
                         G0: OR(W0, W1, W2) \
                         G1: XOR(W1, W2) \
                         output_gate: AND(G0, G1)";
  parse(&parser_state, circuit);

  shared_ptr<And> output_ptr = dynamic_pointer_cast<And> 
      (parser_state.output_gate);
  BOOST_REQUIRE(output_ptr != NULL);
  BOOST_CHECK_EQUAL(output_ptr->NumInputs(), 2);

  shared_ptr<Or> input_1 = dynamic_pointer_cast<Or> 
      (output_ptr->GetInput(0));
  shared_ptr<Xor> input_2 = dynamic_pointer_cast<Xor> 
      (output_ptr->GetInput(1));
  BOOST_REQUIRE(input_1 != NULL);
  BOOST_REQUIRE(input_2 != NULL);

  BOOST_CHECK_EQUAL(input_1->NumInputs(), 3);
  for (int i = 0; i < input_1->NumInputs(); ++i) {
    BOOST_CHECK(dynamic_pointer_cast<Wire> (input_1->GetInput(i)) != NULL);
  }

  BOOST_CHECK_EQUAL(input_2->NumInputs(), 2);
  for (int i = 0; i < input_2->NumInputs(); ++i) {
    BOOST_CHECK(dynamic_pointer_cast<Wire> (input_2->GetInput(i)) != NULL);
  }

  // The second input to L1G0 should be the same as the first input to L1G1.
  BOOST_CHECK_EQUAL(input_2->GetInput(0), input_1->GetInput(1));

  // the third input to L1G0 should be the same as the second input to L1G1.
  BOOST_CHECK_EQUAL(input_2->GetInput(1), input_1->GetInput(2));

  delete parser_state.wires;
}

// A circuit using Not gates and mixed wires/labels as inputs.
BOOST_AUTO_TEST_CASE(MixedCircuits) {
  ParserState parser_state;
  std::string circuit = "W=2 \
                         G0: XOR(W0, N(W1)) \
                         L \
                         G1: AND(W1, L1G0) \
                         output_gate: OR(W0, N(G0), G1)";
  parse(&parser_state, circuit);

  shared_ptr<Or> output_ptr = dynamic_pointer_cast<Or> 
      (parser_state.output_gate);
  BOOST_REQUIRE(output_ptr != NULL);
  BOOST_CHECK_EQUAL(output_ptr->NumInputs(), 3);

  // Verify the type of the Not gate.
  shared_ptr<Not> not_ptr = dynamic_pointer_cast<Not>
      (output_ptr->GetInput(1));
  BOOST_REQUIRE(not_ptr != NULL);

  // Verify the input to the Not gate.
  BOOST_CHECK(dynamic_pointer_cast<Xor> (not_ptr->GetInput(0)) != NULL);

  delete parser_state.wires;
}

