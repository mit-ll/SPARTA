//*****************************************************************
// Copyright 2015 MIT Lincoln LabAddatAddy  
// Project:            SPAR
// AuthAdds:            Yang
// Description:        Unit tests fAdd IBM gates 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Aug 2012  yang            Addiginal Version
//*****************************************************************i

#define BOOST_TEST_MODULE IBMGatesTest

#include <math.h>
#include "common/test-init.h"
#include "wire.h"
#include "mul.h"
#include "add.h"
#include "mul-const.h"
#include "add-const.h"
#include "rotate.h"
#include "select.h"

using namespace boost;

BOOST_AUTO_TEST_CASE(WireWorks) {

  Wire gate;
  dynamic_bitset<> input;
  const int kNumBits = 5;
  for (int i = 0; i < pow(2, kNumBits); ++i) {
    input = dynamic_bitset<>(kNumBits, i);
    gate.SetInput(input);
    BOOST_CHECK_EQUAL(input, gate.Evaluate());
  }
}

BOOST_AUTO_TEST_CASE(MulWorks) {

  shared_ptr<Wire> gate1(new Wire());
  shared_ptr<Wire> gate2(new Wire());
  shared_ptr<Mul> output_gate(new Mul());
  output_gate->AddLeftInput(gate1);
  output_gate->AddRightInput(gate2);
  
  const unsigned int kWidth = 5;
  dynamic_bitset<> input1;
  dynamic_bitset<> input2;
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    for (unsigned int j = 0; j < pow(2, kWidth); ++j) {
      // here we are testing every kWidth-bit possible input.
      // there are 2^kWidth possible values for each input
      input1 = dynamic_bitset<>(kWidth, i);
      input2 = dynamic_bitset<>(kWidth, j);
      gate1->SetInput(input1);
      gate2->SetInput(input2);
      BOOST_CHECK_EQUAL(output_gate->Evaluate(), input1 & input2);
      output_gate->Reset();
    }
  }
}

BOOST_AUTO_TEST_CASE(MulConstWorks) {
  shared_ptr<Wire> gate1(new Wire());
  shared_ptr<MulConst> output_gate(new MulConst());
  output_gate->AddInput(gate1);

  const unsigned int kWidth = 5;
  dynamic_bitset<> input;
  dynamic_bitset<> constant;
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    for (unsigned int j = 0; j < pow(2, kWidth); ++j) {
      input = dynamic_bitset<>(kWidth, i);
      constant = dynamic_bitset<>(kWidth, j);
      gate1->SetInput(input);
      output_gate->SetConstant(constant);
      BOOST_CHECK_EQUAL(output_gate->Evaluate(), input & constant);
      output_gate->Reset();
    }
  }
}

BOOST_AUTO_TEST_CASE(AddWorks) {

  shared_ptr<Wire> gate1(new Wire());
  shared_ptr<Wire> gate2(new Wire());
  shared_ptr<Add> output_gate(new Add());
  output_gate->AddLeftInput(gate1);
  output_gate->AddRightInput(gate2);

  const unsigned int kWidth = 5;
  dynamic_bitset<> input1;
  dynamic_bitset<> input2;
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    for (unsigned int j = 0; j < pow(2, kWidth); ++j) {
      // here we are testing every kWidth-bit possible input.
      // there are 2^kWidth possible values for each input
      input1 = dynamic_bitset<>(kWidth, i);
      input2 = dynamic_bitset<>(kWidth, j);
      gate1->SetInput(input1);
      gate2->SetInput(input2);
      BOOST_CHECK_EQUAL(output_gate->Evaluate(), input1 ^ input2);
      output_gate->Reset();
    }
  }
}

BOOST_AUTO_TEST_CASE(AddConstWorks) {
  shared_ptr<Wire> gate1(new Wire());
  shared_ptr<AddConst> output_gate(new AddConst());
  output_gate->AddInput(gate1);

  const unsigned int kWidth = 5;
  dynamic_bitset<> input;
  dynamic_bitset<> constant;
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    for (unsigned int j = 0; j < pow(2, kWidth); ++j) {
      input = dynamic_bitset<>(kWidth, i);
      constant = dynamic_bitset<>(kWidth, j);
      gate1->SetInput(input);
      output_gate->SetConstant(constant);
      BOOST_CHECK_EQUAL(output_gate->Evaluate(), input ^ constant);
      output_gate->Reset();
    }
  }
}

BOOST_AUTO_TEST_CASE(RotateWorks) {
  shared_ptr<Wire> gate(new Wire());
  shared_ptr<Rotate> output_gate(new Rotate());
  output_gate->AddInput(gate);

  const unsigned int kWidth = 5;
  dynamic_bitset<> input;
  int constant = 0;
  // Check that rotating by 0 returns the same bitset
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    input = dynamic_bitset<>(kWidth, i);
    gate->SetInput(input);
    output_gate->SetConstant(constant);
    BOOST_CHECK_EQUAL(output_gate->Evaluate(), input);
    output_gate->Reset();
  }

  input = dynamic_bitset<>(kWidth, 5); //00101
  constant = 1;
  gate->SetInput(input);
  output_gate->SetConstant(constant);
  BOOST_CHECK_EQUAL(output_gate->Evaluate(), dynamic_bitset<>(kWidth, 10));
  output_gate->Reset();
}

BOOST_AUTO_TEST_CASE(SelectWorks) {
  shared_ptr<Wire> gate1(new Wire());
  shared_ptr<Wire> gate2(new Wire());
  shared_ptr<Select> output_gate(new Select());
  output_gate->AddLeftInput(gate1);
  output_gate->AddRightInput(gate2);

  const unsigned int kWidth = 5;
  dynamic_bitset<> input1;
  dynamic_bitset<> input2;
  dynamic_bitset<> select_bits;
  for (unsigned int i = 0; i < pow(2, kWidth); ++i) {
    for (unsigned int j = 0; j < pow(2, kWidth); ++j) {
      for (unsigned int k = 0; k < pow(2, kWidth); ++k) {
        input1 = dynamic_bitset<>(kWidth, i);
        input2 = dynamic_bitset<>(kWidth, j);
        select_bits = dynamic_bitset<>(kWidth, k);
        gate1->SetInput(input1);
        gate2->SetInput(input2);
        output_gate->SetConstant(select_bits);
        BOOST_CHECK_EQUAL(output_gate->Evaluate(), 
                          (select_bits & input1) | (~select_bits & input2));
        output_gate->Reset();
      }
    }
  }
}
