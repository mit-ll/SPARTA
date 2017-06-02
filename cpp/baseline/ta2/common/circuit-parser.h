//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Flex/lemon parser wrapper 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_COMMON_CIRCUIT_PARSER_H_
#define CPP_BASELINE_TA2_COMMON_CIRCUIT_PARSER_H_

#include <cstdlib>
#include <string>
#include <memory>

#include "baseline/ta2/common/lex-global.h"
#include "baseline/ta2/common/flex-def.h"
#include "baseline/ta2/common/lemon-def.h"

class Circuit;

// Flex and Lemon have a lot of boilerplate code. Most of it needs to be
// executed in the same way regardless of which performer we need a parser for.
// This base class consolidates the intialization and teardown code for
// Flex/Lemon in one place.
class CircuitParser {

 public:

  // The only job of the derived class is to implement how parsing works for the
  // circuit of the performer. When parsing is complete, a Circuit object is
  // returned.
  virtual std::auto_ptr<Circuit> ParseCircuit(const std::string& input) = 0;

  // This version takes no input and reads its input through stdin.
  virtual std::auto_ptr<Circuit> ParseCircuit() = 0;
  
  // Free the scanner and parser objects
  virtual ~CircuitParser() {
    Destroy();
  }

 protected:

  // Allocate a Flex scanner and Lemon parser
  CircuitParser() {
    Init();
  }

  YYSTYPE yylval_;
  yyscan_t scanner_;
  void* parser_ ;
  YY_BUFFER_STATE buffer_state_;

 private:

  void Init() {
    yylex_init_extra(yylval_, &scanner_);
    parser_ = ParseAlloc(malloc);
  }

  void Destroy() {
    yylex_destroy(scanner_);
    ParseFree(parser_, free);
  }



};

#endif
