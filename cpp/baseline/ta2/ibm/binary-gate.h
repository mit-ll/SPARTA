//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    An IBM gate with 2 inputs
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Aug 2012   Yang           Original Version
//****************************************************************

#ifndef CPP_CIRCUIT_EVAL_IBM_BINARY_GATE_H_
#define CPP_CIRCUIT_EVAL_IBM_BINARY_GATE_H_

#include "gate.h"

// The gate types specified by IBM either take a single input or two inputs.
// This abstract class defines an IBM gate that takes two inputs. Derived
// classes which define specific gate types must implement the EvaluateImpl()
// method.
class BinaryGate : public Gate {

 public:

  virtual ~BinaryGate() {}

  // Assigns the specified gate as the left input
  void AddLeftInput(GatePtr input);
  
  // Assigns the specified gate as the right input
  void AddRightInput(GatePtr input);

  // Set the constant to the specified value. Constant is least-significant-bit
  // to most-significant-bit.
  void SetConstant(BitArray constant) {
    constant_ = constant;
  }
  // If evaluated_ is true, this method will immediately return the base class
  // member output_. Otherwise, it will call EvaluateImpl() and then set
  // evaluated_ to true.
  virtual BitArray Evaluate();

  virtual const BitArray& constant() {
    return constant_;
  }

  virtual GatePtr left_input() {
    return left_input_;
  }

  virtual GatePtr right_input() {
    return right_input_;
  }

  // Recursively calls Reset(), which sets the value of evaluated_ to false for
  // itself and all of its children.
  virtual void Reset() {
    left_input_->Reset();
    right_input_->Reset();
    evaluated_ = false;
  }

  // By default, evaluated_ is set to false when a BinaryGate type is
  // instantiated.
  BinaryGate() : evaluated_(false) {}
 
 private:
  // Implementations of gate operations should be defined in the derived class.
  virtual BitArray EvaluateImpl() = 0;

  // If true, the gate's "cached" output value is returned immediately when
  // Evaluate() is called. Otherwise, the output_ value is recomputed. Reset()
  // sets this value to false.
  bool evaluated_;
  BitArray constant_;
  GatePtr left_input_;
  GatePtr right_input_;

};

#endif
