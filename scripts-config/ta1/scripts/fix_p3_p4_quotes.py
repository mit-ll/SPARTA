import fileinput
import argparse
import fnmatch
import sys
import re
import os

BAD_PATTERN = re.compile(".*, '(([a-z]|\\\\')*'([a-z]|\\\\')*)+'\)")
STRING_PATTERN = re.compile("(?P<begin>.*, ')(?P<string>.*)(?P<end>'\))")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-dir', dest = 'input_dir',
          required = True,
          help = 'Input directory of test scripts')
    options = parser.parse_args()

    options.input_dir = os.path.realpath( \
                        os.path.normpath( \
                        os.path.expanduser( \
                        os.path.expandvars(options.input_dir))))
    assert os.path.isdir(options.input_dir)

    for f in os.listdir(options.input_dir):
      f = os.path.join(options.input_dir, f)
      if fnmatch.fnmatch(f, '*.q'):
        fh = open(f)
        # Anything that goes to stdout in this loop will be written to the
        # currently open file
        for line in fileinput.input(f, inplace = True):
          bad_m = BAD_PATTERN.match(line)
          if bad_m:
            string_m = STRING_PATTERN.match(line)
            assert string_m
            sys.stdout.write('%s%s%s\n' % (string_m.group('begin'),
                                           string_m.group('string').replace("'", "\\'"),
                                           string_m.group('end')))
          else:
            sys.stdout.write(line)

if __name__ == "__main__":
    main()
