//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Abstract class for handling/parsing line raw data.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120731       ni24039         Original version
// 120807       ni24039         Minor revisions in response to review 43
// 120808       ni24039         run() removed; parse() replaced with
//                              parseAndExecute()
//                              Removed BufferedWriter as part of class
//                              In response to review 44
// 120817       ni24039         Moved some concrete functionality to
//                              BasicLineRawHandler to simplify API
// 121203       ni24039         Refactoring after TA3.1 baseline commands were
//                              implemented
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Abstract class that parses line raw data.
 *
 * In order to reduce the number of handler objects created in an application,
 * one can instantiate a persistent handler and use a LineRawHandlerFactory.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see LineRawHandlerFactory
 */
public abstract class LineRawHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(LineRawHandler.class);
    /** Input that will be used to read out Strings of line raw data. */
    private LineRawReader input;

    /**
     * Constructor.
     *
     * @param in LineRawReader input
     */
    public LineRawHandler(final LineRawReader in) {
        input = in;
    }

    /**
     * Getter for LineRawReader input.
     *
     * @return LineRawReader input
     */
    protected final LineRawReader getInput() {
        return input;
    }

    /**
     * Verifies that the next 'data unit' in the LineRawReader matches the
     * expected String; if not, a ProtocolException is thrown. A 'data unit' is
     * defined as the set of bytes read in a single line raw sequence (i.e., a
     * single line in line mode, or all parsed bytes between RAW and ENDRAW
     * tokens). Note that this will not distinguish between line mode data and
     * raw mode data; as long as the raw bytes of the expected String match the
     * bytes of the data unit, no ProtocolException will be thrown.
     *
     * @param expected the token to search for in LineRawReader's data stream
     * @throws ProtocolException if the token is not found
     * @throws IOException if any I/O errors occur
     */
    protected final void verifyExpectedInput(final String expected)
        throws ProtocolException, IOException {
        String actual = input.read();
        if (!(actual.equals(expected))) {
            throw new ProtocolException(String.format(
                "Expected token '%s'; received '%s'.", expected, actual));
        }
    }

    /**
     * Reads between one and the specified number of space delimited tokens out
     * of the input, and returns them as a String array. If the specified number
     * of tokens is not found, the return array is back-filled with nulls. If
     * zero non-empty tokens are found, a ProtocolException is thrown.
     *
     * @param numTokens int
     * @return String[] array of tokens
     * @throws ProtocolException if no valid tokens are found
     * @throws IOException if any I/O errors occur
     */
    protected final String[] readTokens(final int numTokens)
        throws ProtocolException, IOException {
        assert numTokens > 0 : "readTokens must look for at least one token.";
        String[] tokens = new String[numTokens];
        // Read in a string and split on space character.
        String full = input.read();
        String[] split = full.split(" ", numTokens);
        // Confirm that a non-empty string was received.
        if (split.length < 1 && split[0].length() < 1) {
            throw new ProtocolException("Expected at least one non-empty input"
                + " token, but did not detect any tokens.");
        }
        System.arraycopy(split, 0, tokens, 0, split.length);
        // Back-fill return array with nulls.
        for (int i = split.length; i < numTokens; i++) {
            tokens[i] = null;
        }
        return tokens;
    }
}
