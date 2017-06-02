//****************************************************************
// Copyright MIT Lincoln Laboratory
// Project:       SPAR
// Authors:       Yang
// Description:   Definition of YYSTYPE for passing token values
//                between scanner and parser.
//
// Modifications
// Date         Name            Modifications
// ----         ----            -------------
// 26 July 2012 Yang            Original Version
//****************************************************************

#ifndef CPP_BASELINE_TA2_COMMON_LEX_GLOBAL_H_
#define CPP_BASELINE_TA2_COMMON_LEX_GLOBAL_H_

struct yystype {
  const char* str_val;
  int int_val;
};

#define YYSTYPE yystype

#endif

extern YYSTYPE yylval;
