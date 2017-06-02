//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-16 14:25:52 -0400 (Tue, 16 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Subcommand handler for UNSUBSCRIBE commands sent to a
// SPAR TA3.1 client
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
// 120815       ni24039         Revisions in response to review 62
//*****************************************************************************
package edu.mit.ll.spar.ta3.handlers;

import edu.mit.ll.spar.protocol.handlers.SubcommandHandler;
import edu.mit.ll.spar.ta3.actors.SubscribingActor;

import java.util.concurrent.Executor;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Subcommand handler that parses and acts upon an already received
 * UNSUBSCRIBE subcommand token. Handler will parse out a subscription ID
 * from the received arguments and call its SubscribingActor to unsubscribe
 * that subscription.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2985 $
 * @see SubcommandHandler
 * @see SubscribingActor
 */
public class UnsubscribeSubcommandHandler extends SubcommandHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(UnsubscribeSubcommandHandler.class);
    /** Number of arguments expected to be parsed in args. */
    private static final int EXPECTED_ARG_COUNT = 1;
    /** Subscriber that will perform the unsubscribe. */
    private SubscribingActor subscriber;

    /**
     * Constructor.
     *
     * @param in LineRawReader used for input
     * @param out ConcurrentBufferedWriter used for output
     * @param sub SubscribingActor that will perform the unsubscribe
     */
    public UnsubscribeSubcommandHandler(final LineRawReader in,
                                        final Writer out,
                                        final SubscribingActor sub) {
        super(in, out);
        subscriber = sub;
    }

    /**
     * Parse and execute method.
     *
     * @param commandId command ID for this subcommand
     * @param args String of parsable arguments
     * @param executor Executor for a NumberedCommandHandler that will execute
     *                 the parsed command
     * @throws ProtocolException if parsing errors occur
     * @throws IOException if I/O errors occur
     */
    public final void parseAndExecute(final int commandId, final String args,
        final Executor executor)
        throws ProtocolException, IOException {
        LineRawReader input = getInput();
        // Validate args.
        if (args == null || args.length() == 0) {
            throw new ProtocolException("UNSUBSCRIBE command must specify a "
                + "subscription number.");
        }
        String[] argArray = args.split(" ");
        int subscriptionId = -1;
        if (argArray.length != EXPECTED_ARG_COUNT) {
            throw new ProtocolException(String.format("UNSUBSCRIBE command must"
                + " specify a subscription number; received [%s].", args));
        }
        try {
            subscriptionId = Integer.parseInt(argArray[0]);
        } catch (NumberFormatException e) {
            throw new ProtocolException(String.format("UNSUBSCRIBE parameter "
                + "must be an integer; received [%s].", argArray[0]));
        }
        final int finalSubscriptionId = subscriptionId;
        verifyExpectedInput("ENDCOMMAND");

        // Have the SubscribingActor unsubscribe.
        executor.execute(new Runnable() {
          public void run() {
            try {
              writeResults(commandId,
                  subscriber.unsubscribe(finalSubscriptionId));
            } catch (IOException e) {
              LOGGER.error("Encountered IOException when attempting to write "
                + "UNSUBSCRIBE results", e);
              System.exit(1);
            }
          }
        });
    }
}
