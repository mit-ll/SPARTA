/*****************************************************************
* Copyright MIT Lincoln Laboratory
* Project:       SPAR
* Authors:       Yang
* Description:   Lexer grammar for generating tokens for IBM
* Modifications
* Date         Name            Modification
* ----         ----            ------------
* 21 Sept 2012 Yang            Original Version
******************************************************************
* 
* This file defines the grammar rules for generating tokens from a string
* representation of an IBM circuit. Flex takes this grammar file as an input
* and outputs source code for a scanner that can produce tokens from a
* character stream based on the rules defined below.
*
* The IBM circuit grammar looks like the following:
*
* W=4, D=5, L=4
* L1G1: LMULconst(W0, [0,1,1,1,0])
* L1G2: LMUL(W0, W1)
*
* The first line specifies the number of input wires (W), the maximum depth of 
* the circuit (D), and the batch-size (L). Each line following the first defines
*  a single gate. The inputs to these gates are either previously defined gates 
* or wires. The final gate is the output gate.
*/

%{
#include <cstdlib>
#include "../../common/lex-global.h"
#include "ibm-parser.h"

#define YY_INPUT(buf, result, max_size) \
 { \
 int c = getchar(); \
 result = (c == EOF) ? YY_NULL : (buf[0] = c , 1); \
   }

%}

%option reentrant noyywrap
%option header-file="ibm-scanner.yy.h"
%option outfile="ibm-scanner.yy.cpp"
%option extra-type="YYSTYPE"

NUM [0-9]

%%

[ \t\n\r] /* ignore whitespace */

"ENDCIRCUIT\n" { yyterminate(); }

"(" { return LPAREN; }

")" { return RPAREN; }

":" { return COLON; }

"[" { return LBRACKET; }

"]" { return RBRACKET; }

"," /* ignore */

W={NUM}+ {
   yyextra.int_val = atoi(yytext+2);
   return NUM_INPUTS;
}

L={NUM}+ {
   yyextra.int_val = atoi(yytext+2);
   return LENGTH;
}

D={NUM}+.{NUM}+ /* ignore depth.*/

G{NUM}+ {
   yyextra.str_val = strdup(yytext);
   return LABEL;
}

W{NUM}+ {
   yyextra.int_val = atoi(yytext+1);
   return WIRE;
}


{NUM} {
   yyextra.int_val = atoi(yytext);
   return NUM;
}

LMUL { return MUL; }
LMULconst { return MULCONST; }
LADD { return ADD; }
LADDconst { return ADDCONST; }
LSELECT { return SELECT; }
LROTATE { return ROTATE; }

%%

