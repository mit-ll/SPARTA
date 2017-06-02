//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Test class that mimics a typical subcommand handler
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120731       ni24039         Original version
// 120808       ni24039         Revisions in response to review 44
// 120811       ni24039         Added synchronization
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers.test;

import edu.mit.ll.spar.protocol.handlers.SubcommandHandler;
import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import java.util.concurrent.Executor;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

 /**
 * Designed to emulate a typical subcommand handler. Accepts a number to start
 * a count-up sequence from and the number of milliseconds to delay before
 * parseAndExecute() completes processing. parseAndExecute() expects to
 * receive tokens that count up from the starting number to the assigned
 * command ID. The handler then indicate whether or not the full count up
 * sequence was received.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see SubcommandHandler
 */
public class CountupHandler extends SubcommandHandler {
    /** Maximum amount to delay before completing task. */
    public static final int MAX_MILLIS_DELAY = 200;
    /** Number of arguments to look for when parsing args. */
    private static final int EXPECTED_ARG_COUNT = 2;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(CountupHandler.class);
    /** Success flag. */
    private boolean success = false;

    /**
     * Constructor.
     *
     * @param in LineRawReader to read line raw data from
     * @param out Writer to write output to
     */
    public CountupHandler(final LineRawReader in,
                          final Writer out) {
        super(in, out);
    }

    /**
     * Parse and execute method.
     *
     * @param commandId command ID for this subcommand
     * @param args String of parsable arguments
     * @param executor Executor to queue and execute parsed command
     * @throws ProtocolException if parsing errors occur
     * @throws IOException if IO errors occur
     */
    public final void parseAndExecute(final int commandId,
                                      final String args,
                                      final Executor executor)
        throws ProtocolException, IOException {
        // Validate command ID.
        if (commandId < 0) {
          throw new ProtocolException("Command ID must be positive.");
        }
        // Validate args.
        final int runDelay;
        int countupStart;
        if (args == null || args.length() <= 0) {
          throw new ProtocolException("COUNTUP commands require a start "
              + "number and number of milliseconds delay; received nothing.");
        }
        String[] argArray = args.split(" ");
        if (argArray.length != EXPECTED_ARG_COUNT) {
            throw new ProtocolException(String.format("COUNTUP commands "
                  + "require a start number and number of milliseconds to "
                  + "delay; received [%s]", args));
        }
        try {
            countupStart = Integer.parseInt(argArray[0]);
            runDelay = Integer.parseInt(argArray[1]);
        } catch (NumberFormatException e) {
            throw new ProtocolException(String.format("COUNTUP parameters "
                + "must be integers; received [%s] and [%s].",
                argArray[0], argArray[1]));
        }
        if (countupStart > commandId) {
            throw new ProtocolException(String.format("Count up start number "
                + "must be less than or equal to count up stop number (count up"
                + " stop number is the command's command ID); "
                + "start: %d, stop: %d.", countupStart, commandId));
        }
        if (runDelay < 0) {
            throw new ProtocolException(String.format("Delay time must be "
                + "greater than zero; delay: %d.", runDelay));
        }

        // Validate incoming input tokens and populate results.
        try {
            // Check for count up sequence.
            for (int i = countupStart; i <= commandId; i++) {
                verifyExpectedInput(Integer.toString(i));
            }
            verifyExpectedInput("ENDCOUNTUP");
            verifyExpectedInput("ENDCOMMAND");
            success = true;
        } catch (ProtocolException e) {
            // Set success flag to false if any parsing errors occur.
            success = false;
        }
        final String results;
        if (!success) {
            results = "Did not receive a valid countup sequence.";
        } else {
            results = null;
        }

        // Submit task.
        executor.execute(new Runnable() {
          public void run() {
            // Sleep before returning results.
            try {
                Thread.sleep(runDelay);
            } catch (InterruptedException e) {
                LOGGER.error(
                    "Encountered InterruptedException during delay", e);
                System.exit(1);
            }
            try {
              writeResults(commandId, results);
            } catch (IOException e) {
              LOGGER.error("Encountered IOException when attempting to write "
                + "COUNTDOWN results", e);
              System.exit(1);
            }
          }
        });
    }

    /**
     * Helper method to build a sequence of countup strings.
     *
     * @param cuStart countup start number
     * @param cuEnd countup end number
     * @return String with countup sequence
     */
    protected static final String countupString(final int cuStart,
                                                final int cuEnd) {
        StringBuilder cuString = new StringBuilder();
        for (int i = cuStart; i <= cuEnd; i++) {
            cuString.append(String.format("%d\n", i));
        }
        return cuString.toString();
    }
}
