//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A "constant" gate which represents an input wire
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
// 09 Aug 2012   yang           Added SetValue() method
// 12 Sep 2012   yang           Changed class name from ConstGate to Wire
//****************************************************************

#ifndef CPP_BASELINE_TA2_STEALTH_WIRE_H_
#define CPP_BASELINE_TA2_STEALTH_WIRE_H_

#include "gate.h"

// A Wire represents an input to a Stealth circuit. Wires are inputs to the
// terminal gates in the circuit. They have no inputs and output a constant
// boolean value.
class Wire : public Gate {

 public:
  // Creates a Wire. The output is set to false by default.
  // Evaluate() should only be called after SetValue() is called.
  Wire() : output_(false) {}

  virtual ~Wire() {}

  // Simply returns the defined output value. Here, short_circuit
  // carries no meaning. There are no inputs so this parameter is
  // simply ignored.
  virtual bool Evaluate(bool short_circuit) { return output_; }

  // Sets the value to the specified boolean value.  
  void SetValue(bool val) { output_ = val; }

  // Does nothing
  virtual void Reset() {}

  // Wire has no inputs. Return 0.
  virtual int NumInputs() { return 0; }

  virtual GatePtr GetInput(int i) {
    LOG(FATAL) << "Atempting to access input to a Wire";
    return GatePtr();
  }

 private:
  bool output_;
};

typedef boost::shared_ptr<Wire> WirePtr;

#endif
