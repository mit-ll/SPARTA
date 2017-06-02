//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_CIRCUIT_H_
#define CPP_BASELINE_TA2_IBM_CIRCUIT_H_

#include <vector>
#include <memory>

#include "ibm-circuit-gates.h"
#include "ibm-def.h"

class IbmCircuitParser;

// A Circuit object is collection of gates that represent an actual boolean 
// circuit. It supports a single operation Evaluate(), which returns the output
// of a circuit given its inputs. 
class Circuit {

 public:
  // Evaluates the circuit given the specified input and returns its boolean
  // value. 
  //
  // input_str: a string of bits of the form: [[0,0,1], [1,0,1], [1,1,1]]
  //
  // where the bit of the i-th index of this array is the value corresponding to
  // the i-th input wire of the circuit. IMPORTANT: Each bit array is little
  // endian - LEAST SIGNIFICANT BIT FIRST. [0,0,1] has integer value 4, NOT 1.
  //
  // short_circuit: boolean parameter which determines whether or not the
  // circuit will short-circuit. If true, the circuit will return its output
  // immediately after it knows its value. 
  BitArray Evaluate(const std::string& input);

 private:

  // The constructor is called exclusively by a CircuitParser object.
  // A Circuit takes ownership of ParserState.
  Circuit(ParserState* p) : output_gate_(p->output_gate), 
    wires_(p->wires), length_(p->length) {
    delete p;
  }
  friend class IbmCircuitParser;

  void Parse(const std::string& input);

  boost::shared_ptr<Gate> output_gate_;
  std::auto_ptr< std::vector<WirePtr> > wires_;
  int length_;

};

#endif
