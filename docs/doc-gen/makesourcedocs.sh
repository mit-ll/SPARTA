#!/bin/bash

# Cpp docs, uses Doxyfile config
doxygen
# javadocs
# -d: output directory
# -private: include public, protected, and private components in output
# -sourcepath: sourcepath
# -classpath: location of class files
# -subpackages: resursively cover all packges under the top-level 'edu' package
activemq_jars=../../java/jars/third_party/activemq/activemq-all-5.5.1.jar
checkstyle_jars=../../java/jars/third_party/checkstyle/checkstyle-5.4.jar
jewelcli_jars=../../java/jars/third_party/jewelcli/jewelcli-0.7.6.jar
junit_jars=../../java/jars/third_party/junit/junit-4.10.jar
opencsv_jars=../../java/jars/third_party/opencsv/opencsv-2.3.jar
slf4j_jars=../../java/jars/third_party/slf4j/slf4j-api-1.5.11.jar
thirdparty_jars=$activemq_jars:$checkstyle_jars:$jewelcli_jars:$junit_jars:$opencsv_jars
javadoc -d javadoc -private -sourcepath ../../java/src -classpath $thirdparty_jars -subpackages edu
# python docs, uses epydoc
epydoc --config epydoc_config
