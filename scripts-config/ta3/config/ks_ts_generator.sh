#!/bin/bash

keytool -genkey -keypass SPARtest -storepass SPARtest -dname "cn=TA3 Broker, ou=SPAR, o=MIT Lincoln Laboratory, l=Lexington, st=MA, c=US" -alias ta3_broker -keyalg RSA -keystore stores/ta3_broker.ks
keytool -genkey -keypass SPARtest -storepass SPARtest -dname "cn=TA3 Server, ou=SPAR, o=MIT Lincoln Laboratory, l=Lexington, st=MA, c=US" -alias ta3_server -keyalg RSA -keystore stores/ta3_server.ks
keytool -export -storepass SPARtest -alias ta3_broker -keystore stores/ta3_broker.ks -file certs/ta3_broker_cert
keytool -export -storepass SPARtest -alias ta3_server -keystore stores/ta3_server.ks -file certs/ta3_server_cert
keytool -import -storepass SPARtest -noprompt -alias ta3_server -keystore stores/ta3_broker.ts -file certs/ta3_server_cert
keytool -import -storepass SPARtest -noprompt -alias ta3_broker -keystore stores/ta3_server.ts -file certs/ta3_broker_cert

for ((i=0; i < $1; i++))
do
  keytool -genkey -keypass SPARtest -storepass SPARtest -dname "cn=TA3 Broker, ou=SPAR, o=MIT Lincoln Laboratory, l=Lexington, st=MA, c=US" -alias ta3_client$i -keyalg RSA -keystore stores/ta3_client$i.ks
  keytool -export -storepass SPARtest -alias ta3_client$i -keystore stores/ta3_client$i.ks -file certs/ta3_client${i}_cert
  keytool -import -storepass SPARtest -noprompt -alias ta3_client$i -keystore stores/ta3_broker.ts -file certs/ta3_client${i}_cert
  keytool -import -storepass SPARtest -noprompt -alias ta3_broker -keystore stores/ta3_client$i.ts -file certs/ta3_broker_cert
done
