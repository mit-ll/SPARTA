/******************************************************************************
 **
 ** THE CODE IN THIS FILE IS NOT MIT LINCOLN LABORATORY DEVLOPED SOURCE CODE.
 **
 ** The following is part of an implementation of the Porter stemming algorithm
 ** taken from http://tartarus.org/~martin/PorterStemmer/c_thread_safe.txt
 ** 
 *****************************************************************************/

#ifndef CPP_MYSQL_SERVER_PARSER_STEMMER_UDF_STEMMER_H_
#define CPP_MYSQL_SERVER_PARSER_STEMMER_UDF_STEMMER_H_

extern "C"
{

/// Data structures and API declarations for the Porter stemming algorithem
/// located in stemmer.c

/// Acts as state for the stem() function.  Calling create_stemmer()
/// will dynamically allocate one of these, in which case you must
/// call free_stemmer() to release the memory.  Or you can just
/// declare a struct stemmer variable and pass the address to the
/// stem function.
struct stemmer {
   char * b;       /* buffer for word to be stemmed */
   int k;          /* offset to the end of the string */
   int j;          /* a general offset into the string */
};

/// Dynamically allocates a struct stemmer
struct stemmer* create_stemmer(void);

/// Free the memory allocated in create_stemmer()
void free_stemmer(struct stemmer * z);

/// Stem the word in b where k is the index of the last character in
/// the word.  Returns the index of the last character in the stem of
/// the word.
int stem(struct stemmer * z, char * b, int k);

} // extern "C"

#endif // CPP_MYSQL_SERVER_PARSER_STEMMER_UDF_STEMMER_H_

