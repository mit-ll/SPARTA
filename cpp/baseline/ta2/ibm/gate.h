//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    Abstract class definition for IBM circuit gates
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Aug 2012   Yang           Original Version
//****************************************************************

#ifndef CPP_CIRCUIT_EVAL_IBM_GATE_H_
#define CPP_CIRCUIT_EVAL_IBM_GATE_H_

#include <boost/shared_ptr.hpp>
#include <boost/dynamic_bitset.hpp>

typedef boost::dynamic_bitset<> BitArray;
// This abstract class serves as the base class for IBM circuit gates. It
// requires that all derived gate types implement the Evaluate() and Reset()
// methods at minimum.
class Gate {
  
 public:

  virtual ~Gate() {}

  // Evaluate performs a bit-wise boolean gate operation on the 
  // gate's inputs. This value is then cached and will be returned immediately 
  // (without recomputation) for all future calls to Evaluate() unless Reset() 
  // is called.
  virtual BitArray Evaluate() = 0;

  // Gates do not recompute their output if their inputs have not changed
  // because they cache their output value. However, the user can call Reset()
  // which should recursively clear the cache for the specified gate and all of
  // its children. A call to Reset() on the output gate resets the entire 
  // circuit.
  virtual void Reset() = 0;

 protected:

  const BitArray& output() const{ return output_; }
  
  void SetOutput(BitArray output) {
    output_ = output;
  }
 
 private:
  BitArray output_;

};
typedef boost::shared_ptr<Gate> GatePtr;

#endif
