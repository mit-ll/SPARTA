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
 * Designed to emulate a typical subcommand handler. Expects to receive
 * commands that countdown from the assigned command ID to zero. When
 * parseAndExecute() is called, results are output indicating whether or not
 * the full countdown was received.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see SubcommandHandler
 */
public class CountdownHandler extends SubcommandHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(CountdownHandler.class);
    /** Success flag. */
    private boolean success = false;

    /**
     * Constructor.
     *
     * @param in LineRawReader to read line raw data from
     * @param out Writer to write output to
     */
    public CountdownHandler(final LineRawReader in,
                            final Writer out) {
        super(in, out);
    }

    /**
     * Parse and execute method.
     *
     * @param commandId commannd ID for this subcommand
     * @param args String of parsable arguments
     * @param executor Executor to execute parsed command
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
        if (args != null && args.length() > 0) {
            throw new ProtocolException(String.format("COUNTDOWN command does "
                + "not take any parameters; received [%s].", args));
        }

        // Validate incoming input tokens and populate results.
        try {
            // Check for count down sequence.
            for (int i = commandId; i >= 0; i--) {
                verifyExpectedInput(Integer.toString(i));
            }
            verifyExpectedInput("ENDCOUNTDOWN");
            verifyExpectedInput("ENDCOMMAND");
            success = true;
        } catch (ProtocolException e) {
            // Set success flag to false if any parsing errors occur.
            success = false;
        }
        final String results;
        if (!success) {
            results = "Did not receive a valid countdown sequence.";
        } else {
            results = null;
        }

        // Submit Runnable task to Executor.
        executor.execute(new Runnable() {
          public void run() {
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
     * Helper method to build a sequence of countdown strings.
     *
     * @param cdStart countdown start number
     * @return String with countdown sequence
     */
    protected static final String countdownString(final int cdStart) {
        StringBuilder cdString = new StringBuilder();
        for (int i = cdStart; i >= 0; i--) {
            cdString.append(String.format("%d\n", i));
        }
        return cdString.toString();
    }
}

