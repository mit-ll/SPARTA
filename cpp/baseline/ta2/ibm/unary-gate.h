//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A single input IBM gate.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Aug 2012   Yang           Original Version
//****************************************************************

#ifndef CPP_CIRCUIT_EVAL_IBM_UNARY_GATE_H_
#define CPP_CIRCUIT_EVAL_IBM_UNARY_GATE_H_

#include "gate.h"

// This class extends the IBMGate interface for gates with a single
// input. The specific gate operation is left undefined and must be
// implmeneted in EvaluateImp() in a subclass of UnaryGate.

class UnaryGate: public Gate {

 public:

  virtual ~UnaryGate() {}

  // Asigns the specified gas as the input
  void AddInput(GatePtr input);

  // Assigns the specified vector as the constant
  void SetConstant(BitArray constant);

  virtual BitArray Evaluate();

  const BitArray& constant() const { return constant_; }
  GatePtr input() const { return input_; }
  virtual void Reset();

  UnaryGate() : evaluated_(false) {}

 private:

  // Implementation of the specific gate operation should be
  // defined in the subclass.
  virtual BitArray EvaluateImpl() = 0;
  
  bool evaluated_;
  BitArray constant_;
  GatePtr input_;

};

#endif
