/*****************************************************************
* Copyright MIT Lincoln Laboratory
* Project:       SPAR
* Authors:       Yang
* Description:   Lexer grammar for generating tokens for Stealth
* Modifications
* Date         Name            Modification
* ----         ----            ------------
* 25 July 2012 Yang            Original Version
******************************************************************
*
* This file defines the grammar rules for generating tokens from
* a string representation of a Stealth circuit. Flex takes this
* grammar file as an input and outputs source code for a scanner
* that can produce tokens from a character stream based on the
* rules defined below.
*
* The Stealth circuit grammar looks like the following:
*
* W=3, G=2, F=1
* G0: OR(W0, NOT(W1))
* G2: AND(W0, W1, W2)
* output_gate: XOR(G0, G2)      
*
* The first line specifies the number of inputs (W), the maximum
* number of gates at each level (G) and the circuit class (F).
* Each line following the first defines a single gate with possibly
* negated inputs. The inputs to these gates are either wires or
* labels. Additionally, we are guarenteed that if a label appears
* as an input, it has already been defined above. Finally, the final
* line specifies the output gate.
*
* The following are generated tokens:
*
* LPAREN, RPAREN, COLON, NUM_INPUTS, LABEL, WIRE, 
* AND, OR, NOT, XOR, and OUTPUT
*
* These tokens are fed into a parser which produces a grammatical
* construction based on the sequence of tokens.
*/

%{
#include <cstdlib>
/* The generated file ends up in a variant directory (./debug for debug builds,
  ./opt for release builds, etc.) so this header will be in the directory above
  when the build happens. */
#include "../../common/lex-global.h"
#include "stealth-parser.h"

#define YY_INPUT(buf, result, max_size) \
 { \
 int c = getchar(); \
 result = (c == EOF) ? YY_NULL : (buf[0] = c , 1); \
   }

%}

%option reentrant noyywrap
%option header-file="stealth-scanner.yy.h"
%option outfile="stealth-scanner.yy.cpp"
%option extra-type="YYSTYPE"

NUM [0-9]+

%%

[ \n\t\r]  /* ignore whitespace */

"ENDCIRCUIT\n" { yyterminate(); }

"(" { return LPAREN; }

")" { return RPAREN; }

":" { return COLON; }

"," /* ignore comma */

 /* NUM_INPUTS token contains the number of inputs that
    appear in the circuit. They are labeled starting
    at W0. */
W={NUM} {
  yyextra.int_val = atoi(yytext+2);
  return NUM_INPUTS;
}

G={NUM} /* ignore number of gates per level parameter */
F={NUM} /* ignore circuit class parameter */
X={NUM} /* ignore XOR parameter. denotes the num of gates in each XOR level*/
D={NUM} /* ignore depth. denotes num levels */
L /* ignore level marker. simply separates lines by circuit level.*/

 /* LABEL contains the name of the gate, which is used to refer to
    the gate as inputs. The parser takes ownership of yylval.str_val
    and is responsible for freeing the variable after use. */ 
G{NUM} {
  yyextra.str_val = strdup(yytext);
  return LABEL; 
}

 /* An OUTPUT token vim contains the string "output_gate" */
output_gate { return OUTPUT; }

 /* A WIRE token contains the number between 0 and W-1 
    corresponding to the input */
W{NUM} {
  yyextra.int_val = atoi(yytext+1);
  return WIRE; 
}

 /* Return tokens for the gate type */
AND { return AND; }
OR { return OR; }
XOR { return XOR; }
N { return NOT; }

%%
