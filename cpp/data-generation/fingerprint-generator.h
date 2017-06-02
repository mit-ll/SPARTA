//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Generates a random sequence of bits given a 
//                     mean size and variance.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 June 2012  yang           Original Version
//*****************************************************************

#ifndef CPP_DATA_GENERATION_FINGERPRINTGENERATOR_H_
#define CPP_DATA_GENERATION_FINGERPRINTGENERATOR_H_

#include <vector>

#include <boost/random/normal_distribution.hpp>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/variate_generator.hpp>

/// A FingerprintGenerator object takes as input a mean size and standard
/// deviation and generates sequences of random bits of size based on
/// the specified normal distrubtion. The actual size of the bit stream is
/// actually rounded down to the nearest 32-bit multiple.
class FingerprintGenerator {

 public:
  
  /// Creates a random bit generator that produces bit streams
  /// given a mean and standard deviation. The units of the parameters
  /// are in bytes.
  FingerprintGenerator(int mean, int sigma);
	
  /// Sets the seed of the boost::mt19937 random number generator.
  void SetSeed(int seed);

  /// Takes a pointer to an STL vector and populates it with random 32-bit
  /// integers until its size reaches the largest 32-bit mulitple less than the 
  /// target size. The target size is computed for each call to the method 
  /// by drawing from a normal distribution specified in the constructor of
  /// FingerprintGenerator.   
  void GetRandomBits(std::vector<int>* array);

  /// Similar to the above, but returns a char* array of random characters. The
  /// caller is reponsible for freeing the data. On return length is the size of
  /// the array.
  ///
  /// NOTE: This is a temporary, ugly hack. It allocates the array with malloc,
  /// not new, since we're using this from Python and Python frees things with
  /// free().
  char* GetRandomBits(int* length);

  /// Saves the vector as a binary file in the current directory.
  /// Ths function is for testing purposes only and will not be used
  /// in the actual design of the data generation tool.
  void SaveArray(const std::vector<int>& array, std::string filename) const;

 private:

  boost::mt19937 rng_;
  boost::normal_distribution<> nd_;
  boost::variate_generator<boost::mt19937&, 
              boost::normal_distribution<> > normrand_;
};

#endif
