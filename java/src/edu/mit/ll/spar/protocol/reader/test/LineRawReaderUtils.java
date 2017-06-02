//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2014-06-09 09:15:28 -0400 (Mon, 09 Jun 2014) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Helper methods used in LineRawReader tests.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120727       ni24039         Original Version
// 120803       ni24039         Minor stylistic changes
//*****************************************************************************
package edu.mit.ll.spar.protocol.reader.test;

import java.util.Random;

/**
 * Set of helper methods used for testing LineRawReader.
 *
 * @author  ni24039 (last updated by $Author: mi24752 $)
 * @version $Revision: 4983 $
 * @see edu.mit.ll.spar.protocol.reader.LineRawReader
 */
final class LineRawReaderUtils {
    /** ASCII maximum value. */
    private static final int ASCII_MAX_VALUE = 127;
    /** Byte's maximum value. */
    private static final int BYTE_MAX_VALUE = 127;
    /** ASCII line feed. */
    private static final int ASCII_LF = 10;
    /** ASCII carriage return. */
    private static final int ASCII_CR = 13;

    /** Suppresses default constructor for noninstantiability. */
    private LineRawReaderUtils() {
        throw new AssertionError();
    }

    /**
     * Creates a valid raw mode integer/byte stream pair.
     *
     * Method will construct a String with the following:
     *  - {%d}\n, whered is the number of bytes to be sent
     *  - byte sequence
     *
     * @param data String representing data to send
     * @return String representing integer/byte stream pair.
     */
   public static String rawSequence(final String data) {
        return data.length() + "\n" + data;
    }

    /**
     * Creates a valid raw mode command sequence.
     *
     * Method will construct a String with the following:
     *  - RAW\n
     *  - data sequence (assumed to be filled with valid integer/
     *    char stream pairs)
     *  - ENDRAW\n
     *
     *  @param data String representing sequence of integer/char stream pairs
     *  @return String representing fully qualified raw mode command sequence
     */
    public static String rawModeWrapper(final String data) {
        return "RAW\n" + data + "ENDRAW\n";
    }

    /**
     * Creates a randomized char array with '\n' at the end.
     *
     * @param rand random number generator
     * @param length length of array to produce
     * @return randomized char array with '\n' at the end
     */
    public static char[] randomLineChars(final Random rand, final int length) {
        char[] randomChars = new char[length];
        for (int i = 0; i < length - 1; i++) {
            int rn;
            do {
                rn = rand.nextInt(ASCII_MAX_VALUE);
            // Avoid \r and \n.
            } while (rn == ASCII_LF || rn == ASCII_CR);
            randomChars[i] = (char) rn;
        }
        // Add \n.
        randomChars[length - 1] = '\n';
        return randomChars;
    }

    /**
     * Creates a randomized char array.
     *
     * @param rand random number generator
     * @param length length of array to produce
     * @return randomized char array
     */
    public static char[] randomRawChars(final Random rand, final int length) {
        char[] randomChars = new char[length];
        for (int i = 0; i < length; i++) {
            randomChars[i] = (char) (rand.nextInt(BYTE_MAX_VALUE));
        }
        return randomChars;
    }
}
