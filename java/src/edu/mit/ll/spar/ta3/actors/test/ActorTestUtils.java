//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Utilities for testing PubSubActors.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.actors.test;

import edu.mit.ll.spar.common.SchemaHandler;

import java.util.HashMap;
import java.util.List;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Utilities for testing PubSubActors.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
final class ActorTestUtils {
    /** Logger for this class. */
    private static final Logger LOGGER = LoggerFactory.getLogger(
      ActorTestUtils.class);

    /**
     * Suppresses default constructor for noninstantiability.
     */
    private ActorTestUtils() {
        throw new AssertionError();
    }

    /**
     * Generates a PUBLISH command with all 'a's for String metadata fields,
     * and various set enum values and integer values for the remaining fields.
     *
     * @param sh SchemaHandler
     * @return StringBuilder
     */
    public static StringBuilder generatePublishCommand1(
        final SchemaHandler sh) {
      List<HashMap<String, Object>> schema = sh.getSchema();
      StringBuilder publishString = new StringBuilder();
      publishString.append("PUBLISH\nMETADATA\n");
      for (HashMap<String, Object> row : schema) {
        String type = (String) row.get("type");
        String name = (String) row.get("name");
        if (type.equals("string")) {
          int maxSize = ((Integer) row.get("max_byte_size")).intValue();
          // TODO(njhwang) Generate more interesting string w allowed characters
          for (int i = 0; i < maxSize; i++) {
            publishString.append("a");
          }
        } else if (type.equals("enum")) {
          if (name.equals("state")) {
            publishString.append("District_of_Columbia");
          } else if (name.equals("sex")) {
            publishString.append("Female");
          } else if (name.equals("race")) {
            publishString.append("[Two_or_More_Races,Asian,White]");
          } else if (name.equals("marital_status")) {
            publishString.append("Never_Married");
          } else if (name.equals("school_enrolled")) {
            publishString.append("Graduate_or_professional_school");
          } else if (name.equals("citizenship")) {
            publishString.append("Yes_Born_Abroad_US_Parents");
          } else if (name.equals("military_service")) {
            publishString.append("Previous_Active_Duty");
          } else if (name.equals("language")) {
            publishString.append("OTHER_ATHAPASCAN_EYAK_LANGUAGES");
          } else {
            LOGGER.error("Could not deduce enum name {}.", name);
            System.exit(1);
          }
        } else if (type.equals("integer")) {
          if (name.equals("income")) {
            publishString.append(Integer.MAX_VALUE);
          } else if (name.equals("hours_worked_per_week")) {
            publishString.append("167");
          } else if (name.equals("weeks_worked_last_year")) {
            publishString.append("52");
          } else {
            LOGGER.error("Could not deduce integer name {}.", name);
            System.exit(1);
          }
        } else {
          LOGGER.error("Could not deduce metadata type {}.", type);
          System.exit(1);
        }
        publishString.append(",");
      }
      publishString.deleteCharAt(publishString.length() - 1);
      publishString.append("\n");
      return publishString;
    }

    /**
     * Generates a PUBLISH command with all 'b's for String metadata fields,
     * and various set enum values and integer values for the remaining fields.
     * The set values are different from those of generatePublishCommand1 to
     * facilitate testing of matched vs unmatched subscriptions while
     * publishing.
     *
     * @param sh SchemaHandler
     * @return StringBuilder
     */
    public static StringBuilder generatePublishCommand2(
        final SchemaHandler sh) {
      List<HashMap<String, Object>> schema = sh.getSchema();
      StringBuilder publishString = new StringBuilder();
      publishString.append("PUBLISH\nMETADATA\n");
      for (HashMap<String, Object> row : schema) {
        String type = (String) row.get("type");
        String name = (String) row.get("name");
        if (type.equals("string")) {
          int maxSize = ((Integer) row.get("max_byte_size")).intValue();
          // TODO(njhwang) Generate more interesting string w allowed characters
          for (int i = 0; i < maxSize; i++) {
            publishString.append("b");
          }
        } else if (type.equals("enum")) {
          if (name.equals("state")) {
            publishString.append("California");
          } else if (name.equals("sex")) {
            publishString.append("Male");
          } else if (name.equals("race")) {
            publishString.append("American_Indian");
            publishString.append("[Two_or_More_Races,American_Indian,African_American]");
          } else if (name.equals("marital_status")) {
            publishString.append("Married");
          } else if (name.equals("school_enrolled")) {
            publishString.append("Not_In_School");
          } else if (name.equals("citizenship")) {
            publishString.append("Yes_Born_In_US");
          } else if (name.equals("military_service")) {
            publishString.append("Active_Duty");
          } else if (name.equals("language")) {
            publishString.append("OTHER_URALIC_LANGUAGES");
          } else {
            LOGGER.error("Could not deduce enum name {}.", name);
            System.exit(1);
          }
        } else if (type.equals("integer")) {
          if (name.equals("income")) {
            publishString.append("0");
          } else if (name.equals("hours_worked_per_week")) {
            publishString.append("0");
          } else if (name.equals("weeks_worked_last_year")) {
            publishString.append("0");
          } else {
            LOGGER.error("Could not deduce integer name {}.", name);
            System.exit(1);
          }
        } else {
          LOGGER.error("Could not deduce metadata type {}.", type);
          System.exit(1);
        }
        publishString.append(",");
      }
      publishString.deleteCharAt(publishString.length() - 1);
      publishString.append("\n");
      return publishString;
    }
}
