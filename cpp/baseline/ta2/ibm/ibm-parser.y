/***************************************************************
* Copyright 2015 MIT Lincoln Laboratory
* Project:        SPAR
* Authors:        Yang
* Description:    Lemon grammar file for Stealth circuits
*
* Modifications
* Date         Name             Modification
* ----         ----             ------------
* 21 Sept 2012 Yang             Original Version
***************************************************************/

%include {

#include <cstdlib>
/* cassert is required by lemon */
#include <cassert>
#include <map>
#include <vector>
#include <string>
#include <boost/shared_ptr.hpp>


#include "baseline/ta2/common/lex-global.h"

/* auto-generated header containing macros for Flex tokens */
#include "ibm-parser.h"

#include "baseline/ta2/ibm/ibm-def.h"
#include "baseline/ta2/ibm/ibm-circuit-gates.h"
#include "common/logging.h"

std::vector<WirePtr>* wires;
std::map<std::string, GatePtr> gates;

}

%extra_argument {ParserState* parser_state}

%token_type {YYSTYPE}
%type input {InputToken}
%type gate {GateToken}
%type bits {BitsToken}

program ::= circuit .
circuit ::= headers gate_defs .

headers ::= headers header .
headers ::= header .

/* Create the wires */
header ::= NUM_INPUTS(B) . {
   wires = new std::vector<WirePtr>();
   for (int i=0; i < B.int_val; ++i) {
      wires->push_back(boost::shared_ptr<Wire>(new Wire()));
   }
   parser_state->wires = wires;
}

/* Set the length of the bit array. */
header ::= LENGTH(B) . {
  parser_state->length = B.int_val;
}

gate_defs ::= gate_defs gate_def .
gate_defs ::= gate_def .

gate_def ::= LABEL(B) COLON gate(C) . {
  GatePtr gate(C.gate);
  gates[B.str_val] = gate;
  free((void*)B.str_val);
  parser_state->output_gate = gate;
}

/* Both inputs to Mul are either of type Wire or Gate */
gate(A) ::= MUL LPAREN input(B) input(C) RPAREN . {
   Mul* gate = new Mul();
   if (B.type == WIRE) {
     gate->AddLeftInput((*wires)[B.int_val]);
   } else {
     gate->AddLeftInput(gates[B.str_val]);
     free((void*)B.str_val);
   }
   if (C.type == WIRE) {
     gate->AddRightInput((*wires)[C.int_val]);
   } else {
     gate->AddRightInput(gates[C.str_val]);
     free((void*)C.str_val);
   }
   A.gate = gate;
}

/* Both inputs to Add are either of type Wire or Gate */
gate(A) ::= ADD LPAREN input(B) input(C) RPAREN . {
   Add* gate = new Add();
   if (B.type == WIRE) {
     gate->AddLeftInput((*wires)[B.int_val]);
   } else {
     gate->AddLeftInput(gates[B.str_val]);
     free((void*)B.str_val);
   }
   if (C.type == WIRE) {
     gate->AddRightInput((*wires)[C.int_val]);
   } else {
     gate->AddRightInput(gates[C.str_val]);
     free((void*)C.str_val);
   }
   A.gate = gate;
}

/* The first input to MulConst is either a Wire or Gate.
   The second input is always a bit array. */
gate(A) ::= MULCONST LPAREN input(B) LBRACKET bits(C) RBRACKET RPAREN . {
   MulConst* gate = new MulConst();
   if (B.type == WIRE) {
     gate->AddInput((*wires)[B.int_val]);
   } else {
     gate->AddInput(gates[B.str_val]);
     free((void*)B.str_val);
   }
   gate->SetConstant(*C.bits);
   delete C.bits;
   A.gate = gate;
}

/* The first input to AddConst is either a Wire or Gate.
   The second input is always a bit array. */
gate(A) ::= ADDCONST LPAREN input(B) LBRACKET bits(C) RBRACKET RPAREN . {
   AddConst* gate = new AddConst();
   if (B.type == WIRE) {
     gate->AddInput((*wires)[B.int_val]);
   } else {
     gate->AddInput(gates[B.str_val]);
     free((void*)B.str_val);
   }
   gate->SetConstant(*C.bits);
   delete C.bits;
   A.gate = gate;
}

/* The first and second inputs to Select are either Wires or Gates.
   The third input is a bit array. */
gate(A) ::= SELECT LPAREN input(B) input(C) LBRACKET bits(D) RBRACKET RPAREN . {
   Select* gate = new Select();
   if (B.type == WIRE) {
      gate->AddLeftInput((*wires)[B.int_val]);
   } else {
      gate->AddLeftInput(gates[B.str_val]);
      free((void*)B.str_val);
   }
   if (C.type == WIRE) {
      gate->AddRightInput((*wires)[C.int_val]);
   } else {
      gate->AddRightInput(gates[C.str_val]);
      free((void*)C.str_val);
   }
   gate->SetConstant(*D.bits);
   delete D.bits;
   A.gate = gate;
}

/* The first input to Rotate is a Wire nr Gate. The second input is an integer */
gate(A) ::= ROTATE LPAREN input(B) NUM(C) RPAREN . {
   Rotate* gate = new Rotate();
   if (B.type == WIRE) {
      gate->AddInput((*wires)[B.int_val]);
   } else {
      gate->AddInput(gates[B.str_val]);
      free((void*) B.str_val);
   }
   gate->SetConstant(C.int_val);
   A.gate = gate;
} 

input(A) ::= LABEL(B) . {
  A.type = LABEL;
  A.str_val = B.str_val;
}

input(A) ::= WIRE(B) . {
  A.type = WIRE;
  A.int_val = B.int_val;
}

bits(A) ::= bits(B) NUM(C) . {
   B.bits->push_back(C.int_val);
   A.bits = B.bits;
}

bits(A) ::= NUM(B) . {
   A.bits = new boost::dynamic_bitset<>();
   A.bits->push_back(B.int_val);
}

  
