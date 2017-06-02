//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A Stealth gate with more than one input.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 June 2012  yang           Original Version
//****************************************************************

#ifndef CPP_BASELINE_TA2_MULTI_GATE_H_
#define CPP_BASELINE_TA2_MULTI_GATE_H_

#include <boost/shared_ptr.hpp>
#include <vector>
#include "gate.h"

// A MultiInputGate is a Gate that has two or more inputs.
class MultiInputGate : public Gate {

 public:
  virtual ~MultiInputGate() {}

  // Adds a new input gate
  void AddInput(GatePtr input);

  // Returns the GatePtr at the specified index
  virtual GatePtr GetInput(int i);

  // Checks if an existing output value is cached. If so, returns it.
  // If not, calls EvaluateImpl(), caches the output, and returns it.
  virtual bool Evaluate(bool short_circuit);

  // Recursively clears all cached output values
  virtual void Reset();

  // Returns the number of inputs assigned to the gate
  virtual int NumInputs();

 protected:
  // A MultiInputGate should never be instantiated directly.
  MultiInputGate() : evaluated_(false) {}

  // All subclasses of MultiInputGate need to implement this
  // method to define the logical operations they support.
  //
  // Performs an operation on inputs_ and returns a single
  // boolean value as output. Should only be called if two or more
  // inputs are defined. If a logic operation can be short circuited,
  // short_circuit tells the method whether or not to do so. If
  // the operation cannot short circuit, the boolean is simply
  // passed to its children.
  virtual bool EvaluateImpl(bool short_circuit) = 0;

 private: 
  // Vector of shared pointers to Gate objects
  std::vector<GatePtr> inputs_;

  // Logic value of output. At instantiation, this variable might
  // contain garbage values.
  bool output_;

  // TRUE if output is cached and can be safely returned
  // without computation. The value output_ should never 
  // be returned if evaluated_ is false. 
  bool evaluated_;
};

typedef boost::shared_ptr<MultiInputGate> MultiGatePtr;

#endif
