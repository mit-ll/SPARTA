# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Classes for holding specific probability distributions
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  20 Sept       JCH            Original file
# *****************************************************************

"""
This module holds various classes intended to hold very specific
probability distributions:
* Social security numbers
* Street addresses
* Unique IDs
* Fingerprints (note, though, that this class is too slow
  and is not actually used for generation at the moment.)

All the classes will provide a common set of methods, including:

* add(*args): Does nothing. Exists for compatibility with the
  distribtions in distributions.py

* generate(ind_vars): this method returns a random item from the
  distribution, and will be distribution-dependent.
"""

from __future__ import division 
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.common.spar_random as spar_random
import spar_python.common.distributions.base_distributions \
    as base_distributions
import spar_python.data_generation.spar_variables as sv
import re
import itertools
import logging
import datetime
import csv
import copy
import array
import math



class SSNDistribution(object):
    """
    This class returns a new social-security number as a nine-character
    string. There is no guarantee that it will be unique. It will,
    however, resepect the Social Security Adminsitration's reservation
    of certain Area Numbers (the first three digits): 000, 666, and
    900 through 999.
    """

    def add(self, *args):
        """
        Does nothing. Exists solely for compatibility with the more
        general distributions.
        """
        pass

    def _forbidden_area_number(self, an):
        if (an == 0) or (an == 666):
            return True
        else:
            return False


    def generate(self, *args):
        """
        Returns a random social-security number, as a string, in
        format DDDDDDDDD. That is, it will match the regular
        expression \d{9}.  Excluded Area Numbers are excluded (000,
        666, and 900-999) but other than that, it is a random
        number. There is no guarantee that the number is unique.
        """
        area_number = 0
        while self._forbidden_area_number(area_number):
            area_number = spar_random.randint(0, 899)
        group_number = spar_random.randint(0, 99)
        serial_number = spar_random.randint(0,9999)

        ssn_string = '%03d%02d%04d' % (area_number, group_number, serial_number)
        return ssn_string

    def generate_pdf(self, min, max, *args):
        """
        No different from generate, here for compatability for query
        generation
        """
        return self.generate(*args)
    
    def generate_less_than(self, minim, maxim, **kwargs):
        """
        Generate ssn less than queries
        """
        self.__total = 898999999.0
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        ssn_value = spar_random.randint(min_limit, max_limit)
        ssn_string = '%09d' % (ssn_value + 10**6)
        return ssn_string
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        """
        Generate ssn greater than queries
        """
        self.__total = 899999999.0
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        ssn_value = self.__total - spar_random.randint(min_limit, max_limit)
        ssn_string = '%09d' % (ssn_value)
        return ssn_string
    
    def generate_double_range(self, minim, maxim, **kwargs):
        """
        Generate ssn double sided range queries
        """
        self.__total = 899999999.0
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        range = max_limit - min_limit
        ssn_lower = spar_random.randint(1, self.__total-range)
        ssn_upper = ssn_lower + range 
        ssn_string_lower = '%09d' % ssn_lower
        ssn_string_upper = '%09d' % ssn_upper
        return (ssn_string_lower, ssn_string_upper)

class RandIntWithoutReplacement(object):
    """
    This class will return a random integer uniformly selected from
    between 0 and some upper bound, but will never return the same
    value twice. The upper bound is given at initilization. Note:
    objects from this class will keep trying random numbers until it
    finds one which has not been provdided yet.  So not only will it
    get slower with repeated calls, it will simply fall into an
    infinite loop when the supply of numbers is exhaused. (Note: we
    send a warning to the logging module if half or more of the
    numbers are used up.)
    """

    def __init__(self, upper_bound):
        self._upper_bound = upper_bound
        self._returned = set()

    def add(self, *args):
        """
        Does nothing. Exists solely for compatibility with the more
        general distributions.
        """
        pass


    def generate(self, *args):
        """
        Returns a random identifier which has not been returned by
        this object before. Heed class-level documentation about
        degenerate behavior as the supply of possible return-values
        shrinks over time.  Sends a warning to the logging module when
        half or more of the numbers are used up.
        """

        candidate = spar_random.randint(0, self._upper_bound)
        while candidate in self._returned:
            candidate = spar_random.randint(0, self._upper_bound)

        self._returned.add(candidate)

        # Start warning when less than half of values remain--
        # performance will start to get slow!
        if self.percent_remaining < 0.5:
            logging.warning("RandIntWithoutReplacement object now "\
                            "half exhaused (less than half of possible "\
                            "outputs remain.) Performance will start to "\
                            "degrade.")
        return candidate

    def percent_remaining(self):
        """
        This will return the percent of possible return values 'left'.
        If the object has already returned half of the possible return
        values, then this will return 0.5. If it's already returned
        three-quarters, then this will return 0.25.
        """
        num_returned = len(self._returned)
        return float(self._upper_bound - num_returned)  / self._upper_bound




        

class AddressDistribution(base_distributions.SimpleConditionalDistribution):
    """
    This class generates random street addresses. Upon initialization,
    it knows no street addresses. It exepcts to be given a squence of 
    (street_name, zip_code) pairs through add(). When generate() is called,
    it selects a random street
    from the given zip code. It then appends a random house number and
    (sometimes, randomly) a random apartment number.
    
    Note: subclasses distributions.SimpleConditionalDistribution, but
    is hard-coded to use zip-codes as a independent variable.
    """
    
    def __init__(self):
        super(AddressDistribution, self).__init__(sv.VARS.ZIP_CODE)
        self.PERCENT_LIVING_IN_APT = 20
        self.HIGHEST_APT_NUMBER = 20

    def generate(self, ind_vars):
        street_name = \
            super(AddressDistribution, self).generate(ind_vars)
        house_number = spar_random.randint(1, 500)

        return_me = str(house_number) + " " + street_name

        if (spar_random.randint(0, 100) <= self.PERCENT_LIVING_IN_APT):
            apt_number = spar_random.randint(1,self.HIGHEST_APT_NUMBER)
            return_me += ", APT " + str(apt_number)
            
        return return_me
    
    def generate_street_pdf(self, min, max, ind_vars):
        return super(AddressDistribution,self).generate_pdf(min,max, ind_vars)
        
    def generate_pdf(self, min, max, ind_vars):
        street_name = \
            super(AddressDistribution, self).generate_pdf(min, max, ind_vars)
        house_number = spar_random.randint(1, 500)

        return_me = str(house_number) + " " + street_name

        if (spar_random.randint(0, 100) <= self.PERCENT_LIVING_IN_APT):
            apt_number = spar_random.randint(1,self.HIGHEST_APT_NUMBER)
            return_me += ", APT " + str(apt_number)
            
        return return_me
    
    def generate_less_than(self, minim, maxim, **kwargs):
        """
        Generate address less than queries
        """
        db_size = kwargs['db_size']
        street_name = \
            super(AddressDistribution, self).generate_less_than(minim, maxim, **kwargs)
        av = (maxim+minim)/2
        house_number = int(max(1, math.log(db_size/500)*av))
        return str(house_number) + " " + street_name
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        """
        Generate address greater than queries
        """
        db_size = kwargs['db_size']
        street_name = \
            super(AddressDistribution, self).generate_greater_than(minim, maxim, **kwargs)
        av = (maxim+minim)/2
        house_number = 500 - int(max(1, math.log(db_size/500)*av))
        return str(house_number) + " " + street_name
    
    def generate_double_range(self, minim, maxim, **kwargs):
        """
        Generate address double sided range queries
        """
        house_number = spar_random.randint(1,500)
        (street_name_low, street_name_up) = \
            super(AddressDistribution, self).generate_double_range(minim, maxim, **kwargs)
        return_me_low = str(house_number) + " " + street_name_low
        return_me_up = str(house_number) + " " + street_name_up + ', APT 20' 
        return (return_me_low, return_me_up)
    

        
class FingerprintDistribution(object):
    """
    This class generates random 'fingerprints', which are really just
    random character strings in some range of lengths (set at
    initialization). 
    """

    # Fingerprints will not be longer than this
    MAX_FINGERPRINT_SIZE = 94000
    # Or shorter than this
    MIN_FINGERPRINT_SIZE = 90000

    def __init__(self):
        pass
        
    def add(self, *args):
        """
        Does nothing. Exists only so that this class provides the same
        interface as all the other distributions.
        """
        pass

    def generate(self, *args):
        """
        Generates a random fingerprint (character string) of some
        length chosen randomly from the range of valid lengths.
        """
        fp_length = spar_random.randint(
                self.MIN_FINGERPRINT_SIZE, self.MAX_FINGERPRINT_SIZE)
        return_me = spar_random.bytes(fp_length)
        return bytearray(return_me)



class DOBDistribution(object):
    """
    PUMS generates ages, but we need DOBs. The simplest thing to so is
    wrap the 'age' distribution in another class (this one) to turn
    ages into DOBs. A DOB is created by subtracting both age (in
    years) plus a random number of days (from 0 to 365) from
    'now'. For repeatability, 'now' is hard-coded to be 1 Jan, 2013.
    """

    def __init__(self, age_distribution):
        self.curr_year = 2013
        self.age_dist = age_distribution
        
    def __format_value(self, age):
        assert age < 140
        assert age >= 0
        dob = self.curr_year - age
        dob_obj = datetime.date(dob, 01, 01)
        fraction = spar_random.randint(0,365)
        dob_obj = dob_obj - datetime.timedelta(fraction)
        return dob_obj 
    
    def generate(self, *args):
        """
        Returns a random date of birth in ISO format: a string of the
        form YYYY-MM-DD. Age is chosen according to underlying distribution
        """
        return self.__format_value(int(self.age_dist.generate()))
      
    def generate_conditional_pdf(self, min, max, *args):
        return self.generate_pdf(min, max)
        
    def generate_pdf(self, min, max, *args):
        """
        Returns a random date of birth in ISO format: a string of the
        form YYYY-MM-DD. Age is randomly chosen from ages that have a 
        probability greater than min and less than max probability
        """
        return self.__format_value(int(self.age_dist.generate_pdf(min, max)))

    def generate_less_than(self, minim, maxim, **kwargs):
        age = self.age_dist.generate_greater_than(minim, maxim, **kwargs)
        assert age < 140
        assert age >= 0
        dob = self.curr_year - age
        dob_obj = datetime.date(dob, 01, 01)
        fraction = spar_random.randint(int(365*minim),int(365*maxim))
        dob_obj = dob_obj - datetime.timedelta(fraction)
        return dob_obj
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        db_size = kwargs['db_size']
        age = self.age_dist.generate_less_than(minim, maxim, **kwargs)
        assert age < 140
        assert age >= 0
        dob = self.curr_year - age
        dob_obj = datetime.date(dob, 01, 01)
        fraction = spar_random.randint(int(min(365,minim*db_size)), 
                                       int(min(365,maxim*db_size)))
        dob_obj = dob_obj - datetime.timedelta(fraction)
        return dob_obj
    
    def generate_double_range(self, minim, maxim, **kwargs):
        db_size = kwargs['db_size']
        (age_low, age_upper) = self.age_dist.generate_double_range(minim, maxim, **kwargs)
        assert age_low <= age_upper
        if age_low == age_upper:
            dob = self.curr_year - age_low
            dob_obj_low = datetime.date(dob, 01, 01)
            fraction = spar_random.randint(1,int(min(365,maxim*db_size)))
            dob_obj_up = dob_obj_low + datetime.timedelta(fraction)
        else:
            dob_up = self.curr_year - age_low
            dob_low = self.curr_year - age_upper
            dob_obj_low = datetime.date(dob_low, 01, 01)
            dob_obj_up = datetime.date(dob_up, 01,01)
            fraction = spar_random.randint(int(365*minim),int(365*maxim))
            dob_obj_up = dob_obj_up + datetime.timedelta(fraction)
            
        return (dob_obj_low, dob_obj_up)
 

class FuzzedNumericDistribution(object):
    """
    This distribution 'fuzzes' an underlying numeric distribution (one which
    generates only numeric values. By 'fuzz', we mean that it will add some 
    addiitonal randomness to the underlying distribution by:
    
    1) Drawing a value `x` from the underlying distibution,
    
    2) Drawing a fuzz-factor `z` from the triangle distribution 
    [lower, peak, upper] (where lower, peak, upper are provided at 
    initialization), and
    
    3) Returning x*z.
    """
    
    def __init__(self, numeric_dist, lower, peak, upper, round=True):
        assert lower <= peak
        assert peak <= upper
        self.numeric_dist = numeric_dist
        self.lower = lower
        self.peak = peak
        self.upper = upper
        self.round = round
        
    def add(self, *args):
        pass
    
    def __fuzz_number(self,underlying_random):
        fuzz_factor = spar_random.triangle(self.lower, self.peak, self.upper)
        val = underlying_random * fuzz_factor
        if self.round:
            return int(round(val))
        else:
            return val
        
    def generate(self, *args):
        return self.__fuzz_number(self.numeric_dist.generate(*args))
        
    
    def generate_pdf(self, min, max, *args):
        return self.__fuzz_number(self.numeric_dist.generate_pdf(min, max, *args))
    
    def generate_conditional_pdf(self, min, max, *args):
        return self.__fuzz_number(self.numeric_dist.generate_conditional_pdf(min, 
                                                                             max, 
                                                                             *args))
    
    def generate_less_than(self, minim, maxim, **kwargs):
        """
        Generate less than queries
        """
        return self.__fuzz_number(self.numeric_dist.generate_less_than(minim, 
                                                                       maxim,
                                                                      **kwargs))
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        """
        Generate greater than queries
        """
        return self.__fuzz_number(self.numeric_dist.generate_greater_than(minim, 
                                                                          maxim, 
                                                                          **kwargs))
    
    def generate_double_range(self, minim, maxim, **kwargs):
        """
        Generate double sided range queries
        """
        (lower, upper) = self.numeric_dist.generate_double_range(minim, maxim, **kwargs)
        return (self.__fuzz_number(lower), self.__fuzz_number(upper))
    
class FooInputs(Exception):
      pass
  
class FooDistribution(object):
    """
    Generates a random integer between 1 and 2**65-1 (i.e., a non-negative 
    integer representable in 64 bits) from a very strange distribution:
    
    * First, we choose a random bit-length between 0 and 64.
    
    * We then choose a random n-bit integer and return it.

    This distribution ensures that we will be able to generate interesting
    range queries (small ranges with lots of value, large ranges with few 
    values, etc.)
    """
    
    def __init__(self):
        pass
    
    def add(self, *args):
        pass
    
    
    def generate(self, *args):
        
        
        # Get the bit-length
        bit_length = spar_random.randint(0,64)
        # Now, skep it a bit toward shorter numbers
        if bit_length == 64:
            if spar_random.randint(1,5000) != 1:
                bit_length = spar_random.randint(0, 63)

        # Generate a random int of that bit-length
        if bit_length == 0:
            return 0
        else:
            return_me = 1
            random_bits = bit_length - 1
            for _ in xrange(random_bits):
                return_me *= 2
                return_me += spar_random.randbit()
            return return_me
        
    def __prob_b(self, b):
        '''This function calculates the given probability of chosing
        a certain bit length'''
        if not b == 64:
            return 319999/20160000.
        else:
            return 1/320000.
        
    def __close_enough(self, actual_density, desired_density):
        '''Returns true if the density is within 0.5 of the actual density'''
       
        density_ratio = actual_density / desired_density
        upper_bound = 1.5   
        lower_bound = 0.5
        return ((density_ratio >= lower_bound) 
                  and (density_ratio <= upper_bound))
  
    def __bucket_density(self, db_size):
        '''Calculates the actual density for the buckets and returns
        those values as a list'''
        density = {}
        for bit_len in xrange(65):
            if bit_len == 0:
                bin_size = 1 
            else:
                b = bit_len
                bin_size = (2**b) - (2 ** (b - 1))
            density[bit_len] = self.__prob_b(bit_len) * db_size / bin_size
        return density
    
        
    def generate_pdf(self, minim, maxim, *ind_vars):
        '''
        Returns a value with the given record set size (expressed as a 
        percentage of database size), can be db_size agnostic becuase 
        min and max are normalized
        '''
        record_set_min = minim*10**9
        record_set_max = maxim*10**9
        bit_len = None
        for b in xrange(65):
            expected = self.__prob_b(b)*10**9/(2**b-2**(b-1))
            if expected >= record_set_min and expected <= record_set_max:
                bit_len = b
        if bit_len is None:
            return 0 
        value = spar_random.randint(2**(bit_len-1),2**(bit_len)-1)
        return value
        
    def generate_conditional_pdf(self, pdf_lower,pdf_upper,*args):
        '''
        Returns a value with the given record set size (expressed as a 
        percentage of database size), can be db_size agnostic becuase 
        min and max are normalized
        '''
        return self.generate_pdf(pdf_lower, pdf_upper)
        
    def generate_two_sided(self, record_set_size, range_size, db_size):
        '''Returns a tuple containing a the lower and upper values of a
        randomly generated range'''       
        #Get the desired density by dividing by the range of the bucket           
        desired_density = record_set_size / range_size

        #Find all bit lengths that have that density
        density = self.__bucket_density(db_size)
        close_enoughs = []          
        min_bit_length = range_size.bit_length() + 1
        for bit_len in xrange(min_bit_length, 65):
            if self.__close_enough(density[bit_len], desired_density):
                    close_enoughs.append(bit_len)
        
        if len(close_enoughs)==0:
            raise FooInputs
        elif len(close_enoughs) == 1:
            bit_length = close_enoughs[0]
        else:
            bit_length = spar_random.choice(close_enoughs)
        
        #Generate a random range of bit length range_size
        range = 1
        for _ in xrange(range_size.bit_length()-1):
            range *= 2 
            range +=spar_random.randbit() 
        assert range.bit_length() == range_size.bit_length()
        
        #generate random starting point within the bucket for the range, 
        #the lower value is generated randomly and then multiplied by 2
        #because randint cannot compute values larger than 2**63
        lower_half =  spar_random.randint(2**(bit_length-1)/2,(2**(bit_length)-range_size)/2)
        lower = lower_half * 2
        upper = lower+range

        return (lower, upper)
        
  
    def generate_greater_than(self, record_set_size, db_size):
        '''Returns a single value which is the lower bound of a randomly
         generated range'''
        #find the nearest bit_length that has a count close to record_set_size
        cum_count = 0
        density = self.__bucket_density(db_size)
        bit_length = None
        for b in xrange(64, 0,-1):
            cum_count+=density[b]*((2**b) - (2 ** (b - 1)))
            #either it is close enough or the count has gotten 
            #bigger than the record_set_size and we need to stop
            if self.__close_enough(cum_count,record_set_size)\
               or cum_count > record_set_size:
                    bit_length = b
                    break
        #this checks to see for the case where the record_set_size is
        #somewhere in the bitlength but the granularity is too fine so we
        #need for further refine where we are generating our random range
        #from 
        if bit_length is None:
            raise FooInputs
        
        if not self.__close_enough(cum_count, record_set_size):
            records_in_range = record_set_size
            for b in xrange(64,bit_length,-1):
                records_in_range -= self.__prob_b(b)*db_size
            records_in_range = self.__prob_b(bit_length)*db_size-records_in_range
            range = int(records_in_range * (2**bit_length-2**(bit_length-1)) / \
                        (self.__prob_b(bit_length)*db_size)) 
        else:
            range = 0    
                       
        #Generate random value of that length
        if bit_length == 0:
            return 1
        else:
            b = bit_length
            #generate a random start offset that is less than the size of the bucket
            #minus the randomly generated range. We only generate half of this value
            #randomly and then multiply by 2 because randint cannot handle values 
            #large than 2**63
            random_start_half = spar_random.randint(1,(2**b-2**(b-1)-range)/2)
            random_start = random_start_half * 2
            #add that offset to the lower end of the bucket as well as the range value
            return random_start+2**(b-1)+range
        
class LastUpdatedDistribution(object):
    """
    Given a row_dict with a datetime entry for spar_vars.VARS.DOB,
    compute an integer representing a number of seconds between 1 Jan 1970 and
    1 Jan 2014, guaranteed to be after the DOB provided. 
    """
    midnight = datetime.time()
    zero_utc = datetime.datetime(1970, 1, 1, 0, 0, 0, 0) 
    upper_bound = datetime.datetime(2014, 1, 01)
    
    def __init__(self, dob_dist):
        self.dob_dist = dob_dist
    
    def add(self, *args):
        pass
    
    def _dob_to_last_updated(self, dob):
        dob_datetime = datetime.datetime.combine(dob, self.midnight)

        lower_bound = max(self.zero_utc, dob_datetime)
        
        delta = self.upper_bound - lower_bound
        
        seconds_in_delta = delta.total_seconds()
        
        random_seconds = spar_random.randint(0, seconds_in_delta)

        if lower_bound == self.zero_utc:
            return int(random_seconds)
        else:
            dob_delta = dob_datetime - self.zero_utc
            dob_delta_seconds = dob_delta.total_seconds()
            return int(random_seconds + dob_delta_seconds)
    
    def generate_pdf(self, min, max, ind_vars):
        dob = self.dob_dist.generate_pdf(min, max, ind_vars)
        return self._dob_to_last_updated(dob)
    
    def generate(self, ind_vars):
        return self._dob_to_last_updated(ind_vars[sv.VARS.DOB])

    def generate_less_than(self, minim, maxim, **kwargs):
        """
        Generate less than queries
        """
        delta = self.upper_bound - self.zero_utc
        delta = delta.total_seconds()
        return spar_random.randint(delta*minim, delta*maxim)
    
  
    def generate_greater_than(self, minim, maxim, **kwargs):
        """
        Generate greater than queries
        """
        delta = self.upper_bound - self.zero_utc
        delta = delta.total_seconds()
        return int(delta - spar_random.randint((delta*minim)/2.0, (delta*maxim)/2.0))

    def generate_double_range(self, minim, maxim, **kwargs):
        """
        Generate double sided range queries
        """
        delta = self.upper_bound - self.zero_utc
        delta = delta.total_seconds()
        min_limit = int(minim*delta)
        max_limit = int(maxim*delta)
        range = spar_random.randint(min_limit, max_limit)
        lower = spar_random.randint(1,delta-range)
        upper = lower + range 
        return (lower, upper)
        
        
