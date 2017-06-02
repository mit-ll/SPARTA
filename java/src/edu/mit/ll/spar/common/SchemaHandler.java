//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Parses a *.csv file representing a database schema and
//                      its constraints, and supports various operations related
//                      to using a parsed database schema.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120903       ni24039         Original Version
//*****************************************************************************
package edu.mit.ll.spar.common;

import au.com.bytecode.opencsv.CSVReader;
import java.io.InputStreamReader;
import java.io.FileInputStream;
import java.io.BufferedReader;

import java.util.Collections;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import javax.jms.TextMessage;
import javax.jms.Session;

import java.util.Scanner;
import java.util.regex.Pattern;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.UnsupportedEncodingException;
import java.io.FileNotFoundException;
import javax.jms.JMSException;
import java.io.IOException;

/**
 * Parses a *.csv file representing a database schema and its constraints. Valid
 * *.csv files representing a database schema should have the following columns:
 *
 *      name,type,min_byte_size,max_byte_size,min_value,max_value,num_values
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public class SchemaHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(SchemaHandler.class);
    /**
     * Each HashMap in this list represents a mapping of column names to column
     * values for each row in the schema.
     */
    private static List<HashMap<String, Object>> schema;
    /** Buffer size used to read *.csv file. */
    private static final int BUFFER_SIZE = 1024;

    /**
     * Constructor.
     *
     * @param schemaFile String representing path to a valid UTF-8 encoded
     *                   *.csv file
     */
    public SchemaHandler(final String schemaFile) {
        /*
         * Create mapping from CSV "type" strings to Class objects. This mapping
         * should be updated as new datatypes are supported.
         */
        HashMap<String, Class<?>> classMap = new HashMap<String, Class<?>>();
        classMap.put("string", String.class);
        classMap.put("enum", String.class);
        classMap.put("integer", Integer.class);

        // Read tokens from CSV file.
        CSVReader reader = null;
        try {
            reader = new CSVReader(
                new BufferedReader(new InputStreamReader(
                    new FileInputStream(schemaFile), "UTF-8"),
                    BUFFER_SIZE));
        } catch (FileNotFoundException e) {
            LOGGER.error(String.format("Could not find metadata file [%s]; "
                  + "current working is [%s].", schemaFile,
                  System.getProperty("user.dir")), e);
            System.exit(1);
        } catch (UnsupportedEncodingException e) {
            LOGGER.error("Could not recognize character encoding.", e);
            System.exit(1);
        }
        List<String[]> schemaRows = null;
        try {
            schemaRows = reader.readAll();
        } catch (IOException e) {
            LOGGER.error("IOException encountered while reading metadata.", e);
            System.exit(1);
        }

        // Create list of hash maps that represents the schema.
        List<HashMap<String, Object>> tempSchema =
            new ArrayList<HashMap<String, Object>>();
        // Strip off the header row.
        String[] header = schemaRows.remove(0);
        for (String[] row : schemaRows) {
            HashMap<String, Object> rowMap = new HashMap<String, Object>();
            Class<?> attrClass = null;
            for (int i = 0; i < row.length; i++) {
                // Set the class of the schema item.
                if (header[i].equals("type")) {
                    attrClass = classMap.get(row[i]);
                    if (attrClass == null) {
                        LOGGER.error(row[i] + " metadata type did not map to a"
                            + " recognized class.");
                        System.exit(1);
                    }
                    // Add the String name for the class to the HashMap.
                    rowMap.put(header[i], row[i]);
                    // Also add the actual Class object to the HashMap.
                    rowMap.put("class", attrClass);
                // Cast min_byte_size and max_byte_size entries to Integers.
                } else if (header[i].equals("min_byte_size")
                        || header[i].equals("max_byte_size")) {
                  if (row[i].length() > 0) {
                    rowMap.put(header[i], new Integer(row[i]));
                  }
                } else if (header[i].equals("name")) {
                    rowMap.put(header[i], row[i]);
                }
                /*
                 * NOTE: all other columns in the CSV file are currently
                 * ignored.
                 */
            }
            tempSchema.add(rowMap);
        }
        // Make the class' instance of the schema unmodifiable.
        schema = Collections.unmodifiableList(tempSchema);
    }

    /**
     * Getter for the List of HashMaps representation of the schema.
     *
     * @return List<HashMap<String, Object>> representation of the schema; each
     *         HashMap in the list is a mapping of column name to column values
     *         for each row in the schema.
     */
    public final List<HashMap<String, Object>> getSchema() {
      return schema;
    }

    public final String[] splitMetadata(final String metadata) 
      throws ProtocolException {
      String[] fieldArray = new String[schema.size()];
      Scanner metadataScanner = new Scanner(metadata);
      String basePattern =
        "(([^\\[\\],]*)|(\\[[^\\[\\],]*(,[^\\[\\],]*)*\\]))";
      Pattern fieldPattern = Pattern.compile(basePattern + ",");
      String matchedField = metadataScanner.findInLine(fieldPattern);
      int arrayIndex = 0;
      while (matchedField != null) {
        fieldArray[arrayIndex++] = 
          matchedField.substring(0, matchedField.length() - 1);
        matchedField = metadataScanner.findInLine(fieldPattern);
      }
      fieldPattern = Pattern.compile(basePattern);
      matchedField = metadataScanner.findInLine(fieldPattern);
      fieldArray[arrayIndex++] = matchedField;
      if (arrayIndex != schema.size()) {
        throw new ProtocolException(String.format("Metadata must have "
            + "exactly %d items; metadata contained %d items.",
            schema.size(), arrayIndex));
      }
      return fieldArray;
    }

    /**
     * Takes a JMS TextMessage and updates its properties based on the array of
     * String values received, and the previously processed schema. The array of
     * String values must have the same number of items as the schema, and must
     * have Strings that properly resolve to the type designated by the schema.
     *
     * @param values array of Strings representing values that should conform to
     *               the previously processed schema *.csv file
     * @param msg JMS TextMessage object that will have its properties updated
     *            per the array of String values and the previously processed
     *            schema file
     * @throws ProtocolException if array of String values do not conform to the
     *                           schema (this usually means the METADATA values
     *                           in a PUBLISH command were not valid, and that
     *                           the SPAR protocol was therefore violated)
     * @throws JMSException if any errors occur when setting the TextMessage's
     *                      properties
     */
    public final List<TextMessage> createMessages(final String[] values,
                                                  final String payload,
                                                  final Session session)
      throws ProtocolException, JMSException {
      if (values.length != schema.size()) {
        throw new ProtocolException(String.format("Metadata must have "
            + "exactly %d items; metadata contained %d items.",
            schema.size(), values.length));
      }
      ArrayList<TextMessage> results = new ArrayList<TextMessage>();
      int numSingletons = 0;
      for (int i = 0; i < values.length; i++) {
        if (values[i].startsWith("[") && values[i].endsWith("]")) {
          String[] fieldValues = 
            values[i].substring(1, values[i].length() - 1).split(",");
          int numFieldValues = fieldValues.length;
          for (int j = 0; j < numFieldValues; j++) {
            String[] newValues = new String[values.length];
            System.arraycopy(values, 0, newValues, 0, values.length);
            newValues[i] = fieldValues[j];
            results.addAll(this.createMessages(newValues, payload, session));
          }
        } else {
          numSingletons++;
        }
      }
      if (numSingletons == values.length) {
        TextMessage msg = session.createTextMessage(payload);
        for (int i = 0; i < values.length; i++) {
          // Extract schema information.
          HashMap<String, Object> schemaRow = schema.get(i);
          String fieldName = (String) schemaRow.get("name");
          Class<?> fieldClass = (Class) schemaRow.get("class");
          /*
           * Convert metadata token into appropriate object and set
           * TextMessage properties.
           */
          if (fieldClass.equals(Integer.class)
           || fieldClass.equals(int.class)) {
              Integer value = null;
              try {
                  value = new Integer(values[i]);
              } catch (NumberFormatException e) {
                throw new ProtocolException(String.format("Could not convert"
                  + " [%s] into a valid integer value for metadata field "
                  + "[%s].", values[i], fieldName));
              }
              msg.setIntProperty(fieldName, value);
          } else if (fieldClass.equals(String.class)) {
              msg.setStringProperty(fieldName, values[i]);
          } else {
              throw new ProtocolException(String.format("Could not convert "
                  + "[%s] into a valid value for metadata field [%s].",
                  values[i], fieldName));
          }
        }
        results.add(msg);
      }
      return results;
    }
}
