///////////////////////////////////////////////////////////////////////////////
//
// Implementation of the M_OF_N user-defined-function.  See section 7.7.6
// of the TA1 for details.
//
// Copyright MIT Lincoln Laboratory
// Copyright $Date$
// Project:            SPAR
// Authors:            $Authors$
// Description:        $Description$
// Modifications:
// Date            Name        Modification
// ----            ----        ------------
// $RevDate$       $Author$    $ModDescription$ 
//
// Notes:  See Makefile for build instructions and prerequisites.
//
///////////////////////////////////////////////////////////////////////////////

// The following cruft is boilerplate for MySQL user-defined function
// development.

#if defined(STANDARD)
/* STANDARD is defined, don't use any mysql functions */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#else // !defined(STANDARD)
#include <my_global.h>
#include <my_sys.h>

#if defined(MYSQL_SERVER)
#include <m_string.h>/* To get strmov() */
#else // !defined(MYSQL_SERVER)
/* when compiled as standalone */
#include <string.h>
#define strmov(a,b) stpcpy(a,b)
#define bzero(a,b) memset(a,0,b)
#define memcpy_fixed(a,b,c) memcpy(a,b,c)
#endif // defined(MYSQL_SERVER)

#endif // defined(STANDARD)

#include <mysql.h>
#include <ctype.h>

#ifdef HAVE_DLOPEN

#if !defined(HAVE_GETHOSTBYADDR_R) || !defined(HAVE_SOLARIS_STYLE_GETHOST)
static pthread_mutex_t LOCK_hostname;
#endif

//
// User #includes go here
//
#include <stdint.h>

///// D E C L A R A T I O N S /////////////////////////////////////////////////

#if defined(__cplusplus)
extern "C" {                            // UDFs require C linkage
#endif

my_bool  M_OF_N_init(UDF_INIT* initid, UDF_ARGS* args, 
                     char* message);
void     M_OF_N_deinit(UDF_INIT *initid);
int64_t  M_OF_N(UDF_INIT* initid, UDF_ARGS* args, 
                char* result, unsigned long *length,
                char* is_null, char* error);

#if defined(__cplusplus)
} // extern "C"
#endif

///// I M P L E M E N T A T I O N /////////////////////////////////////////////

#if defined(__cplusplus)
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////
// Called by MySQL before each call to M_OF_N
//
// TAKES:    initid - MySQL UDF state
//           args   - Array of args used in the update_lookup_tables function
//           message - Text message to send back to MySQL (e.g. on error)
//
// RETURNS:  0 on success, 1 on error
//
// NOTES:    
///////////////////////////////////////////////////////////////////////////////
my_bool M_OF_N_init(UDF_INIT* initid, UDF_ARGS* args,
                      char* message)
{
    if (args->arg_count < 2) {
        strcpy(message, "Expected at least 2 arguments: m, n [,p0,...,pn]");
        return 1;
    }

    // For our purposed every arg is going to be an int result
    // (since booleans are not a supports UDF type).
    for (int i = 0 ; i < args->arg_count ; ++i) {
      args->arg_type[i] = INT_RESULT;
    }

    return 0;
}

///////////////////////////////////////////////////////////////////////////////
// Called by MySQL after each call to M_OF_N
//
// TAKES:    initid - MySQL UDF state
//
// RETURNS:  
//
// NOTES:    
//
///////////////////////////////////////////////////////////////////////////////
void M_OF_N_deinit(UDF_INIT *initid)
{
}

///////////////////////////////////////////////////////////////////////////////
// Implementation of M_OF_N user-defined function
//
// TAKES:    initid - MySQL UDF state
//           args   - Array of args passed into the function
//           result - 
//           length -
//           is_null - Flag for telling MySQL if we are returning NULL
//           error   - Flag for telling MySQL if we had an error
//
// RETURNS:  0 if true, false otherwise
//
// NOTES:    
//
///////////////////////////////////////////////////////////////////////////////
int64_t M_OF_N(UDF_INIT* initid, UDF_ARGS* args, 
               char* result, unsigned long *length, 
               char* is_null, char* error)
{
  int64_t true_count = 0;

  // Starting with the first predicate, go through each one and test for
  // true (1). Count each true result.
  for (int i = 2 ; i < args->arg_count ; ++i) {
    if (*(reinterpret_cast<uint64_t*>(args->args[i])) == 1) {
      ++true_count;
    }
  }

  // If enough predicates are true, return the true_count, so that
  // results can be ranked by number of matching predicates.
  // Otherwise, return False (0).
  if (true_count >= *(reinterpret_cast<uint64_t*>(args->args[0]))) {
        return true_count;
  }
  return 0; // not enough true predicates
}

#if defined(__cplusplus)
} // extern "C"
#endif

#endif /* HAVE_DLOPEN */
