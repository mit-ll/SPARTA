//****************************************************************
// Copyright MIT Lincoln Laboratory
// Project:       SPAR
// Authors:       Yang
// Description:   Unit tests for circuit classes
// 
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
// 09 Aug 2012   yang           Added unit tests for XOR
//****************************************************************

#define BOOST_TEST_MODULE GatesTest

#include <bitset>
#include <vector>
#include <string>
#include <math.h>

#include <boost/shared_ptr.hpp>

#include "stealth-circuit-gates.h"
#include "../../../common/logging.h"
#include "../../../common/test-init.h"
#include "../../../common/check.h"

// Helper method for testing truth tables of single gates. Allocates wires and 
// assigns them to the specified MultiInputGate being tested.
void InitializeLines(int num_inputs, 
                     MultiGatePtr gate, std::vector<WirePtr>* wires) {
  for (int i = 0; i < num_inputs; ++i) {
    WirePtr wire(new Wire());
    wires->push_back(wire);
    gate->AddInput(wire);
  }
}

// Checks to see if Evaluate() of ConstGate produces the correct output
BOOST_AUTO_TEST_CASE(ConstGateEvaluation) {
  Wire one;
  one.SetValue(1);
  BOOST_CHECK_EQUAL(one.Evaluate(false), 1);
  
  Wire zero;
  zero.SetValue(0);
  BOOST_CHECK_EQUAL(zero.Evaluate(false), 0);
}

// Checks to see if Evaluate() of Not produces the correct output
BOOST_AUTO_TEST_CASE(NotEvaluation) {
  WirePtr one(new Wire());
  one->SetValue(1);
  GatePtr output_gate(new Not(one));
  BOOST_CHECK_EQUAL(output_gate->Evaluate(true), 0);

  WirePtr zero(new Wire());
  zero->SetValue(0);
  GatePtr output_gate2(new Not(zero));
  BOOST_CHECK_EQUAL(output_gate2->Evaluate(true), 1);
}

// Checks to see if Evaluate() of And produce the correct output
BOOST_AUTO_TEST_CASE(AndEvaluation) {
  const int kNumInputs = 3;
  boost::shared_ptr<And> output_gate(new And());
  std::vector<WirePtr> wires;
  InitializeLines(kNumInputs, output_gate, &wires);

  // Test the evaluate method on all possible combinations
  // of binary inputs of size kNumInputs.
  for (int i = 0; i < pow(2, kNumInputs); ++i) {
    std::bitset<kNumInputs> inputs(i);
    // Set all wires to their respective values in the bitset.
    for (unsigned int j = 0; j < wires.size(); ++j) {
      wires[j]->SetValue(inputs[j]);
    }
    BOOST_CHECK_EQUAL(output_gate->Evaluate(true), inputs.all());
    output_gate->Reset();
    BOOST_CHECK_EQUAL(output_gate->Evaluate(false), inputs.all());
    output_gate->Reset();
  }
}

// Checks to see if Evaluate of Or produces the correct output
BOOST_AUTO_TEST_CASE(OrWorks) {
  const int kNumInputs = 5;
  boost::shared_ptr<Or> output_gate(new Or());
  std::vector<WirePtr> wires;
  InitializeLines(kNumInputs, output_gate, &wires);

  // Test the evaluate method on all possible combinations
  // of binary inputs of size kNumInputs.
  for (int i = 0; i < pow(2, kNumInputs); ++i) {
    std::bitset<kNumInputs> inputs(i);
    for (unsigned int j = 0; j < wires.size(); ++j) {
       wires[j]->SetValue(inputs[j]);
    }
    BOOST_CHECK_EQUAL(output_gate->Evaluate(true), inputs.any());
    output_gate->Reset();
    BOOST_CHECK_EQUAL(output_gate->Evaluate(false), inputs.any());
    output_gate->Reset();
  }
}

// Checks to see if Evaluate() of Xor produces the correct output
BOOST_AUTO_TEST_CASE(XorWorks) {
  const int kNumInputs = 5;
  boost::shared_ptr<Xor> output_gate(new Xor());
  std::vector<WirePtr> wires;
  InitializeLines(kNumInputs, output_gate, &wires);

  // Test the evaluate method on all possible combinations
  // of binary inputs of size kNumInputs.
  for (int i = 0; i < pow(2, kNumInputs); ++i) {
    std::bitset<kNumInputs> inputs(i);
    for (unsigned int j = 0; j < wires.size(); ++j) {
      wires[j]->SetValue(inputs[j]);
    }
    BOOST_CHECK_EQUAL(output_gate->Evaluate(true), inputs.count() % 2);
    output_gate->Reset();
    BOOST_CHECK_EQUAL(output_gate->Evaluate(false), inputs.count() % 2);
    output_gate->Reset();
  }
}

// Checks to see if a circuit of multiple levels produces the correct output.
// Wires are also attached to multiple circuits to check for memory management
// when testing with --valgrind enabled.
BOOST_AUTO_TEST_CASE(SimpleCircuit) {
  boost::shared_ptr<Xor> output_gate(new Xor());
  boost::shared_ptr<And> gate1(new And());
  boost::shared_ptr<Or> gate2(new Or());
  boost::shared_ptr<Not> not1(new Not(gate1));
  output_gate->AddInput(not1);
  output_gate->AddInput(gate2);

  WirePtr in1(new Wire());
  WirePtr in2(new Wire());

  gate1->AddInput(in1);
  gate1->AddInput(in2);
  gate2->AddInput(in1);
  gate2->AddInput(in2);

  in1->SetValue(0);
  in2->SetValue(0);

  BOOST_CHECK_EQUAL(output_gate->Evaluate(true), 1);
  output_gate->Reset();
  
  in1->SetValue(1);
  in2->SetValue(0);

  BOOST_CHECK_EQUAL(output_gate->Evaluate(false), 0);
}
