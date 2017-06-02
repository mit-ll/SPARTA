//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Unit tests for CircuitParser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012  yang            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE IBMParserTest

#include <string>
#include <memory>
#include <boost/dynamic_bitset.hpp>

#include "circuit.h"
#include "ibm-circuit-parser.h"
#include "common/test-init.h"

using namespace std;
using namespace boost;

// Check that a circuit object returns the correct value given its circuit and
// input strings. Create a simple 2-input one-gate circuit and verify its logic
// table.
BOOST_AUTO_TEST_CASE(ParseMul) {
  
  string circuit_str = "W=2L=3G1: LMUL(W0, W1)";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in1(3, 7ul);
  BitArray in2(3, 7ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[111,111]"), in1 & in2);

  in1 = BitArray(3, 1ul);
  in2 = BitArray(3, 4ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[100,001]"), in1 & in2);

  in1 = BitArray(3, 3ul);
  in2 = BitArray(3, 6ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[110,011]"), in1 & in2);
}

BOOST_AUTO_TEST_CASE(ParseMulConst) {
  string circuit_str = "W=1L=4G1: LMULconst(W0, [1,1,1,0])";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in(4, 15ul);
  BitArray constant(4, 7ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[1111]"), in & constant);

  in = BitArray(4, 1ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[1000]"), in & constant);

}

BOOST_AUTO_TEST_CASE(ParseAdd) {
  string circuit_str = "W=2L=2G0: LADD(W0, W1)";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in1(2, 3ul);
  BitArray in2(2, 2ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[11,01]"), in1 ^ in2);
}

BOOST_AUTO_TEST_CASE(ParseAddConst) {

  string circuit_str = "W=1L=4G3: LADDconst(W0, [0,1,0,1])";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in(4, 4ul);
  BitArray constant(4, 10ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[0010]"), in ^ constant);

  in = BitArray(4, 0ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[0000]"), in ^ constant);
}

BOOST_AUTO_TEST_CASE(ParseSelect) {
  string circuit_str = "W=2L=3G4: LSELECT(W0, W1, [0,1,0])";
  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in1(3, 1ul);
  BitArray in2(3, 4ul);
  BitArray constant(3, 5ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[[1,0,0],[0,0,1]"), 
                    (in1 & ~constant) | (in2 & constant));
}

BOOST_AUTO_TEST_CASE(ParseRotate) {
  string circuit_str = "W=1L=3G1: LROTATE(W0, 2)";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BitArray in(3, 1ul);
  BOOST_CHECK_EQUAL(c->Evaluate("[[1,0,0]]"), BitArray(3, 4ul));
}

BOOST_AUTO_TEST_CASE(ParseCircuitFromAppendix) {
  string circuit_str = "W=4, L=5\
                        G3: LMULconst(W2, [0,1,1,0,1])\
                        G2: LMUL(W2, W0)\
                        G0: LROTATE(W2,4)\
                        G1: LMUL(G2, W2)\
                        G2: LMULconst(L1G0, [0,0,1,0,1])\
                        G0: LADD(G3, W0)\
                        G2: LMULconst(G1, [0,0,0,0,0])\
                        G0: LMULconst(G1, [1,1,0,1,0])\
                        G0: LSELECT(G0, G0, [0,0,1,1,0])\
                        G2: LSELECT(G2, G2, [1,1,1,1,0])\
                        G0: LSELECT(G0, G2, [0,0,0,0,1])\
                        G1: LADDconst(G2, [1,0,0,0,0])\
                        G3: LMULconst(G1, [0,1,0,0,0])\
                        G1: LADD(G3, G0)\
                        G2: LMULconst(G1, [1,1,0,1,0])";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BOOST_CHECK_EQUAL(c->Evaluate("[[1,1,0,1,0], [0,1,0,1,1], [0,1,0,1,0],\
                                [1,1,0,1,1]]"), BitArray(5, 0ul));

}

// The gate that trivializes most outputs from the Appendix example is the gate
// L3G2, which is multiply by 0. This test replaces it with a passthrough
// (multiply by 1).
BOOST_AUTO_TEST_CASE(ParseCircuitFromAppendix2) {
  string circuit_str = "W=4, L=5\
                        G3: LMULconst(W2, [0,1,1,0,1])\
                        G2: LMUL(W2, W0)\
                        G0: LROTATE(W2,4)\
                        G1: LMUL(G2, W2)\
                        G2: LMULconst(G0, [0,0,1,0,1])\
                        G0: LADD(G3, W0)\
                        G2: LMULconst(G1, [1,1,1,1,1])\
                        G0: LMULconst(G1, [1,1,0,1,0])\
                        G0: LSELECT(G0, G0, [0,0,1,1,0])\
                        G2: LSELECT(G2, G2, [1,1,1,1,0])\
                        G0: LSELECT(G0, G2, [0,0,0,0,1])\
                        G1: LADDconst(G2, [1,0,0,0,0])\
                        G3: LMULconst(G1, [0,1,0,0,0])\
                        G1: LADD(G3, G0)\
                        G2: LMULconst(G1, [1,1,0,1,0])";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BOOST_CHECK_EQUAL(c->Evaluate("[[1,1,0,1,0], [0,1,0,1,1], [0,1,0,1,0],\
                                [1,1,0,1,1]]"), BitArray(5, 8ul));

}

// This one makes the additional change of inverting L6G3.
BOOST_AUTO_TEST_CASE(ParseCircuitFromAppendix3) {
  string circuit_str = "W=4, L=5\
                        G3: LMULconst(W2, [0,1,1,0,1])\
                        G2: LMUL(W2, W0)\
                        G0: LROTATE(W2,4)\
                        G1: LMUL(G2, W2)\
                        G2: LMULconst(G0, [0,0,1,0,1])\
                        G0: LADD(G3, W0)\
                        G2: LMULconst(G1, [1,1,1,1,1])\
                        G0: LMULconst(G1, [1,1,0,1,0])\
                        G0: LSELECT(G0, G0, [0,0,1,1,0])\
                        G2: LSELECT(G2, G2, [1,1,1,1,0])\
                        G0: LSELECT(G0, G2, [0,0,0,0,1])\
                        G1: LADDconst(G2, [1,0,0,0,0])\
                        G3: LMULconst(G1, [1,0,1,1,1])\
                        G1: LADD(G3, G0)\
                        G2: LMULconst(G1, [1,1,0,1,0])";

  IbmCircuitParser p;
  std::auto_ptr<Circuit> c = p.ParseCircuit(circuit_str);
  BOOST_CHECK_EQUAL(c->Evaluate("[[1,1,0,1,0], [0,1,0,1,1], [0,1,0,1,0],\
                                [1,1,0,1,1]]"), BitArray(5, 3ul));

}
