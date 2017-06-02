# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        example arg_parser for remote runner
# *****************************************************************

import argparse

def parse_args(extra_args, ssh_user):
  if not ssh_user:
    ssh_user = "unspecified"
  parser = argparse.ArgumentParser('Example Remote Runner custom arg_parser')
  parser.add_argument('--apple', type=str, dest = 'apple',
                      default = 'Honeycrisp', help = 'Favorite type of apple')
  parser.add_argument('--bread', type=str, dest = 'bread',
                      default = 'sourdough', help = 'Favorite kind of bread')
  parser.add_argument('--cheese', type=str, dest = 'cheese',
                      default = 'cheddar', help = 'Favorite kind of cheese') 

  extra_args_list = extra_args.split()
  extra_options = parser.parse_args(extra_args_list)
  
  extra_options.user = ssh_user
  
  return extra_options
  
  
  