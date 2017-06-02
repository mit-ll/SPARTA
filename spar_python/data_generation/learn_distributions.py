# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Learn distributions for data-gen variables
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Sept 2012   jch           copied from learn_education.py
# *****************************************************************


"""
Learns and column-distributions for later data-generation. Final result will be
a dictionary which maps field names to distributions. Various command-line
options can be used to specify the source of the training data and so on.
"""

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)


import re
import spar_python.common.distributions.base_distributions as base_distributions
import spar_python.common.distributions.distribution_holder as distribution_holder
import spar_python.common.distributions.bespoke_distributions as bespoke_distributions
import spar_python.data_generation.learning.url_dict as url_dict
import spar_python.common.distributions.text_generator as text_generator
import spar_python.common.distributions.xml_generator as xml_generator
import spar_python.common.distributions.text_distribution as text_distribution
import logging
import csv
import zipfile
import hashlib

import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.sanitization as sanitization
import spar_python.common.spar_random as spar_random


INCOME_FUZZ_FACTOR = 0.1

def _files_generator(key, options, logger):
    """
    Returns a generator of already-opened file() objects, where the open
    files are those listed in url_dict.url_dict[key].
    """
    data_dir = os.path.join(options.data_dir, key)
    files_dict = url_dict.url_dict[key]
    file_descriptors = files_dict.keys()
    # Note: the next line is present for reproducability. (Dictionaried can
    # return keys in any order, so this normalizes the order across runs.)
    # This is no longer needed now that url_dict is an OrderedDict,
    # but we'll keep it just in case.
    file_descriptors.sort()
    for file_descriptor in file_descriptors:
        (file_name, _, hash_val) = files_dict[file_descriptor]
        data_file = os.path.join(data_dir, file_name)

        
        try:
            with open(data_file, 'r') as f:
                logger.info("Checking hash of file %s", file_name)
                recomputed_hashval = hashlib.sha1(f.read()).hexdigest()
                if hash_val != recomputed_hashval:
                    
                    error_str = "File %s does not have the expected hash. "\
                                "Reproducability with previous runs cannot "\
                                "be guaranteed. " % file_name
                    logger.error(error_str)
                    raise RuntimeError(error_str)
        except IOError:
            if options.allow_missing_files:
                logger.info("Missing file: %s", data_file)
                continue
            else:
                logger.exception("Missing file:")
                sys.exit(1)




        logger.info("Getting data from %s" % file_name)
        
        # Most downloaded files will be text, but
        # at least one will be zip. If so, check to see if
        # we have already unzipped it. If not, unzip it
        (base_name, extension) = os.path.splitext(file_name)
        if extension == '.zip':
            logger.info("Oh, it's a zip file. "\
                        "Do I already have the contents?")
            # Do we already have the unzipped files?
            unzipped_file = os.path.join(data_dir, base_name)
            if not os.path.exists(unzipped_file):
                logger.info("Guess not. I'll try to unzip it.")
                logger.info("Do I have the archive?")
                if os.path.exists(data_file):
                    logger.info("Yes, I do. Unzipping %s....", data_file)
                    zf = zipfile.ZipFile(data_file)
                    try:
                        zf.extractall(data_dir)
                    except zipfile.BadZipfile:
                        logging.error("Problem reading zipfile %s",
                                      file_name)
                        # Don't have the unzipped file, and can't unzip
                        # the zip file. Give up.
                        break
                    else:
                        logger.info("...done")
                        zf.close()
                        data_file = unzipped_file
                        file_name = base_name

                else:                    
                    # Don't have the unzipped or zipped file. Give up.
                    logging.error("Can't find %s or %s.",
                                  base_name, file_name)
                    if not options.allow_missing_files:
                        sys.exit(1)
            else:
                logger.info("Yes, I do.")
                data_file = unzipped_file
                file_name = base_name



        try:
            with open(data_file, 'r') as f:
                yield (file_name, f)
        except IOError:
            if options.allow_missing_files:
                logger.info("Missing file: %s", data_file)
                continue
            else:
                logger.exception("Missing file:")
                sys.exit(1)





def learn_pums_dists(options, logger, pums_files):
    """
    Learn the distribution over PUMS variables. Return a dictionary from
    variable-names to distribution objects, all of which support a
    generate(independent_vars) method.

    PUMS variables:
    * SEX
    * CITIZENSHIP
    * INCOME
    * AGE
    * RACE
    * STATE
    * WEEKS_WORKED
    * HOURS_WORKED
    * MILITARY_SERVICE
    * MARITAL_STATUS
    * GRADE_ENROLLED
    * LANGUAGE
    """
    # Store final distributions in a dictionary
    pums_dist_dict = {}


    for (dep_var, ind_vars) in sv.PUMS_VARS_DEPS:
        if ind_vars == []:
            # purely-independent vars can be held in a plain
            # CompactDiscreteDistribution
            if dep_var in sv.ENUM_VARS:
                pums_dist_dict[dep_var] =\
                    base_distributions.CompactIndependentDistribution(comp_enum = 
                                                                      sv.VAR_TO_ENUM[dep_var])
            else:
                pums_dist_dict[dep_var] =\
                    base_distributions.CompactIndependentDistribution()

        else:
            # this is a conditional distribution, so need one
            if dep_var in sv.ENUM_VARS:
                pums_dist_dict[dep_var] = \
                    base_distributions.CompactConditionalDistribution(*ind_vars, 
                                                                      comp_enum = 
                                                                      sv.VAR_TO_ENUM[dep_var])
            else:
                pums_dist_dict[dep_var] = \
                    base_distributions.CompactConditionalDistribution(*ind_vars)

    #
    # Learning the variables with one pass thru the data
    #    
    # Start getting the data
    record_handler = sv.SPAR_RECORD_HANDLER
        
    # Learn the vars
    count = 0
    for (filename, f) in pums_files:
        logger.info("Reading data from %s", filename)
        # Now iterate over the rows of data, adding them to the
        # distributions
        for weight, row in record_handler.record_generator(f):
            # Update the user, if necessary
            count += 1
            if count % 10000 == 0:
                logger.info("Processed %sK records", count/1000)
                
            # Okay. Now add the row to all distributions
            for (dep_var, ind_vars) in sv.PUMS_VARS_DEPS:
                dep_var_val = row[dep_var]
                ind_var_vals = [row[x] for x in ind_vars]
                pums_dist_dict[dep_var].add(dep_var_val, 
                                            weight, 
                                            *ind_var_vals)
                
    # Add some fuzzing to the INCOME distribution
    unfuzzed_income_dist = pums_dist_dict[sv.VARS.INCOME]
    peak = 1
    lower = peak * (1 - INCOME_FUZZ_FACTOR)
    upper = peak * (1 + INCOME_FUZZ_FACTOR)
    
    fuzzed_dist = \
        bespoke_distributions.FuzzedNumericDistribution(unfuzzed_income_dist,
                                                        lower,
                                                        peak,
                                                        upper)
    pums_dist_dict[sv.VARS.INCOME] = fuzzed_dist


    return pums_dist_dict



def learn_name_dists(options, logger, names_files):
    """
    Learn the distribution of first and last names from census data.
    Last names will have an independent distribution, but first names
    will be conditioned on sex. Returns a dictionary from variable
    names (FIRST_NAME, LAST_NAME) to distribtion objects which support
    a generate(ind_vars) method.
    """

    # Return a dictionary containing distributions for first and last names.
    name_dists = {}
    name_dists[sv.VARS.LAST_NAME] = \
        base_distributions.CompactIndependentDistribution()
    name_dists[sv.VARS.FIRST_NAME] = \
        base_distributions.CompactConditionalDistribution(sv.VARS.SEX)

    # We're parsing three files with the same format, so let's
    # factor out how they differ: filenames, var name, and ind var name
    processing_parameters = {
        'last_names.txt' : (sv.VARS.LAST_NAME, None),
        'female_first_names.txt' : (sv.VARS.FIRST_NAME, sv.SEX.Female),
        'male_first_names.txt':  (sv.VARS.FIRST_NAME, sv.SEX.Male)}


    # Process the files

    # Each file consists of lines of the form:
    #  JENNIFER       0.932  7.586      6
    #
    # In order, these are:
    # * The name
    # * Frequency in percent
    # * Cumulative frequence of this and all previous names
    # * Rank-- e.g. this is the 7th most frequent female first name
    #
    # We only care about the name and the (indivdiual) frequency.
    line_format = re.compile("([A-Z]+) *(\d.\d\d\d)D*") 

    for (filename, f) in names_files:
        logger.info("Reading data from %s" % filename)
        (dep_var_name, ind_var) = processing_parameters[filename]


        # We now know which entry of the dictionary we want to extend.
        # Lets just fetch it once and for all
        dist_to_extend = name_dists[dep_var_name]

        # Iterate through the entires
        for line in f:
            # Parse the line
            match_object = line_format.match(line) 
            if not (match_object == None):
                name = match_object.group(1)
                percentage_str = match_object.group(2)

                # All entries of the file have a freqency in the format D.DDD
                # where D is a digit. So I multiple by 1000 to make it an int.
                #
                # Also, many entries actually have a weight of 0.000, so I
                # add 1 so that they have some probability of being chosen
                # at all.
                weight = (float(percentage_str) * 1000) + 1

                # Store the name and weight
                if ind_var == None:
                    dist_to_extend.add(name, weight)
                else:
                    dist_to_extend.add(name, weight, ind_var)
            

    # We're done, right?
    return name_dists



def learn_zipcode_dists(options, logger, zipcode_files):
    """
    Learn the set of zip codes in each state, and the city associated
    with each zip code, and embed these into distributions for
    consistency with everything else.
    """

    # Return a dictionary containing distributions for first and last names.
    zipcode_dists = {}

    #
    # First, we process what can be learned from the zip-code files
    #
    zipcode_dists[sv.VARS.ZIP_CODE] =\
        base_distributions.SimpleConditionalDistribution(sv.VARS.STATE)

    # If we need to optimize, replace this distribution with a dict
    zipcode_dists[sv.VARS.CITY] =\
        base_distributions.SimpleConditionalDistribution(sv.VARS.ZIP_CODE)


    # process each file:
    for (filename, f) in zipcode_files:
        
        csv_reader = csv.DictReader( f, skipinitialspace=True)

        # parse each line, store in the appropraite directory
        for row in csv_reader:

            zip_code = row['zip code']
            state = row['state']
            # The state strings in the enum have no spaces but the
            # states in the file *do* have spaces. So we need to
            # replace the space with an underscore, turning 'New York'
            # into 'New_York'.
            state = state.replace(' ', '_')
            city = row['city']

            zipcode_dists[sv.VARS.ZIP_CODE].add(zip_code, 1, state)
            zipcode_dists[sv.VARS.CITY].add(city, 1, zip_code)

    return zipcode_dists


def learn_street_address_dists(options, logger, streets_files):
    """
    Learn the set of unique street names in each zip code. Works by
    parsing the streets_files, line by line, and feeding each line into
    and underlying bespoke_distributions.AddressDistribution.
    """
    
    address_dist = bespoke_distributions.AddressDistribution()

    logger.info("Getting street-name data")
    count = 0
    for (_, csv_file_handle) in streets_files: 
        csv_dict_reader = csv.DictReader(csv_file_handle)
        for d in csv_dict_reader:
            count += 1
            if count % 10000 == 0:
                logger.info("Processed %sK records", count/1000)

            zip_str = d['zip']
            street_str = d['fullname']
            address_dist.add(street_str, 1, zip_str)

    
    address_dict = {}
    address_dict[sv.VARS.STREET_ADDRESS] = address_dist
    return address_dict



def train_text_engine(options, logger, text_files):
    """
    Train a TextGeneration on the provided works.
    The results will be used to instanitate TextDistributions.
    """
    # Process the files
    file_generator = (f for (_,f) in text_files)
    tg = text_generator.TextGenerator(file_generator)
    logger.info("Finished training on text corpus")
    return tg



def make_xml_distribution(pums_dict, names_dict):
    
    # The XML generator actually uses a little distribution holder of its 
    # own, internally, so we need to build that.
    
    vars = [sv.VARS.SEX,
            sv.VARS.CITIZENSHIP,
            sv.VARS.AGE,
            sv.VARS.RACE,
            sv.VARS.STATE,
            sv.VARS.FIRST_NAME,
            sv.VARS.LAST_NAME]

    var_order = vars
    var_names = [sv.VARS.to_string(x) for x in vars]
    dist_dict = { }
    dist_dict.update(pums_dict)
    dist_dict.update(names_dict)
    
    dist_holder = distribution_holder.DistributionHolder(var_order, 
                                                         var_names, 
                                                         dist_dict)

    return xml_generator.XmlGenerator(dist_holder)
    
def make_text_distributions(text_engine):

    dist_dict = {}
    dist_dict[sv.VARS.NOTES1] = \
        text_distribution.TextDistribution(text_engine, 5000, 10000, 
                                           add_alarmwords = True)
    dist_dict[sv.VARS.NOTES2] = \
        text_distribution.TextDistribution(text_engine, 500, 2000,
                                           add_alarmwords = True)
    dist_dict[sv.VARS.NOTES3] = \
        text_distribution.TextDistribution(text_engine, 200, 250, 
                                           add_alarmwords = True)
    dist_dict[sv.VARS.NOTES4] = \
        text_distribution.TextDistribution(text_engine, 20, 50)

    return dist_dict


def make_distribution_holder(options, logger, 
                             pums_dict, 
                             names_dict,
                             zipcode_dict,
                             address_dict,
                             text_engine):
    """
    Take learned  distributions of demographic data, add the 'fixed' 
    (not-learned) distributions, and embed everything into a 
    DistributionHolder object.
    """

    
    dist_dict = {}
    # Tells the data-generator the order in which to call these distributions
    # Note: Age and fingerprint are special cases, not included here.

    var_names = [sv.VARS.to_string(x) for x in sv.VAR_GENERATION_ORDER]

    dist_dict.update( pums_dict )

    dist_dict.update( names_dict )

    dist_dict.update( zipcode_dict )

    dist_dict.update( address_dict )

    text_dist_dict = make_text_distributions(text_engine)
    
    dist_dict.update( text_dist_dict )

    dist_dict[sv.VARS.SSN] = bespoke_distributions.SSNDistribution()

    # Note: used to try to generate fingerprints in python
    # We're not doing that for the moment, but leaving this here
    # in case we do so again.
    #
    dist_dict[sv.VARS.FINGERPRINT] = \
        bespoke_distributions.FingerprintDistribution()

    dist_dict[sv.VARS.DOB] = \
        bespoke_distributions.DOBDistribution(dist_dict[sv.VARS.AGE])

    dist_dict[sv.VARS.LAST_UPDATED] = \
        bespoke_distributions.LastUpdatedDistribution(dist_dict[sv.VARS.DOB])
        
    dist_dict[sv.VARS.FOO]  = \
        bespoke_distributions.FooDistribution()

    dist_dict[sv.VARS.XML] = \
        make_xml_distribution(pums_dict, names_dict)


    dh = distribution_holder.DistributionHolder(sv.VAR_GENERATION_ORDER, 
                                                var_names, dist_dict)

    return dh


def learn_distributions(options, logger):
    """
    Learn the distributions of demographic data, suitable for creating
    randrom rows of data. Returns the resulting distribution holder.
    """
    #this seed is hard-coded so that the random element of learning are
    #repeatable
    seed = int(81991)
    spar_random.seed(seed)
    
    logger.info("Learning PUMS distributions")
    pums_files = _files_generator('PUMS', options, logger)
    pums_dict = learn_pums_dists(options, logger, pums_files)

    logger.info("Learning name distributions data")
    names_files = _files_generator('names', options, logger)
    names_dict = learn_name_dists(options, logger, names_files)
    
    logger.info("Learning zip-code distributions")
    zipcode_files = _files_generator('zipcodes', options, logger)
    zipcode_dict = learn_zipcode_dists(options, logger, zipcode_files)

    logger.info("Learning street-address distributions")
    streets_files = _files_generator('streets', options, logger)
    address_dict = learn_street_address_dists(options, logger, streets_files)


    logger.info("Training on text corpus")
    # Get the names files
    texts_key = 'texts'
    text_files = _files_generator(texts_key, options, logger)
    text_engine = train_text_engine(options, logger, text_files)


    dist_holder = make_distribution_holder(options, logger, 
                                           pums_dict,    
                                           names_dict,
                                           zipcode_dict,
                                           address_dict,
                                           text_engine)    

    sanitization.sanitize_distribution(dist_holder)
    return dist_holder
