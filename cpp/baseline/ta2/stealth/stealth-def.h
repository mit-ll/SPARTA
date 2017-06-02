/****************************************************************
* Copyright MIT Lincoln Laboratory
* Project:       SPAR
* Authors:       Yang
* Description:   Definitions for auxillary structures used by the
*                parser.
*
* Modifications
* Date         Name             Modifications
* ----         ----             -------------
* 06 Aug 2012  Yang             Original Version
* 09 Aug 2012  Yang             Removed definition for Token.
*****************************************************************/

// This file defines several auxiliary structures used to store
// and pass state information in the parser.

#ifndef CPP_BASELINE_TA2_STEALTH_STEALTH_DEF_H_
#define CPP_BASELINE_TA2_STEALTH_STEALTH_DEF_H_

#include <vector>
#include <string>
#include <boost/shared_ptr.hpp>

#include "stealth-circuit-gates.h"

// ParserState is a structure that can be accessed by the caller of
// the parser. It's pointer is passed in to the parser as the 4th
// argument of the Parse() function. After parsing is complete,
// output_gate will contain a pointer to the final gate in the
// circuit, and wires will contain a pointer to a vector of Const
// gates, which can later be set to their needed input values.
struct ParserState {
  boost::shared_ptr<Gate> output_gate;
  std::vector<WirePtr>* wires;
};

// An InputToken is passed between the _input_ and _inputs_ rules. The
// type field specifies the token type recieved from the scanner,
// which will either be a WIRE or LABEL. If the type is WIRE, wire_num
// will be set. If the type is LABEL, label_name will be set.
struct InputToken {
  int type;
  bool is_negated;
  const char* label_name;
  int wire_num;
};

// InputsToken stores a vector of InputTokens. This state is kept
// while the parser is parsing a gate containing a long list of inputs.
// TODO(yang): InputToken objects contain memory allocated by the scanner. Need
// to create a wrapper around an InputToken that automatically frees the memory
// when destructed. Currently being freed in AddInputsToGate in the grammar
// file.
struct InputsToken {
  std::vector<InputToken>* inputs;
};

// A GateToken is created when a token of type AND, OR, or XOR is 
// encountered by the parser. A new Gate object of the corresponding
// type is instantiated and stored here until its inputs are ready to be
// specified.
struct GateToken {
  MultiInputGate* gate;
};

#endif
