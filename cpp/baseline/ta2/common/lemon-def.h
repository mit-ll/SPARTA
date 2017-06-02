//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Method declarations and type definitions 
//                     for instantiating a lemon parser using the
//                     auto-generated source stealth-parser.cpp. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Aug 2012   yang           Original Version
//*****************************************************************

#ifndef CPP_BASELINE_TA2_COMMON_LEMON_DEF_H_
#define CPP_BASELINE_TA2_COMMON_LEMON_DEF_H_

// These methods are defined in the auto-generated source stealth-parser.cpp. 
// Depending on the build settings, they will be created in different 
// subdirectories. Any class that wishes to instantiate a Lemon parser should 
// include this file, rather than directly including stealth-parser.h.

struct ParserState;

// Using the specified allocation procedure, returns a void pointer
// that references a newly allocated lemon parser. This pointer is taken as
// the first argument in the Parse method.
void* ParseAlloc(void* (*allocProc)(size_t));

// Parse processes the lexer token given by the lexcode, defined in
// lemon's auto-generated header stealth-parser.h. YYSTYPE is a global
// structure that contains any data associated with a token type. The 
// ParserState* points to a struct which contains the output gate and input
// wires of the completed circuit.
void* Parse(void*, int, YYSTYPE, ParserState*);

// Using the specified deallocation procedure, frees the lemon parser.
void* ParseFree(void*, void(*freeProc)(void*));

#endif
