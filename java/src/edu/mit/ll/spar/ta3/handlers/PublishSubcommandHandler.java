//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Subcommand handler for PUBLISH commands sent to a SPAR
//                      TA3.1 server
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120731       ni24039         Original version
// 120817       ni24039         Revisions in response to review 62
//*****************************************************************************
package edu.mit.ll.spar.ta3.handlers;

import edu.mit.ll.spar.protocol.handlers.SubcommandHandler;
import edu.mit.ll.spar.ta3.actors.PublishingActor;

import java.util.concurrent.Executor;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Subcommand handler that parses and acts upon an already received
 * PUBLISH subcommand token. Handler will parse out metadata and a payload
 * from the input data and call its PublishingActor to publish a message
 * with the parsed out metadata and payload.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see SubcommandHandler
 * @see PublishingActor
 */
public class PublishSubcommandHandler extends SubcommandHandler {
    /** Publisher to perform the publish. */
    private PublishingActor publisher;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(PublishSubcommandHandler.class);

    /**
     * Constructor.
     *
     * @param in LineRawReader used for input
     * @param out ConcurrentBufferedWriter used for output
     * @param pub PublishingActor that will perform the publish
     */
    public PublishSubcommandHandler(final LineRawReader in,
                                    final Writer out,
                                    final PublishingActor pub) {
        super(in, out);
        publisher = pub;
    }

    /**
     * Parse and execute method. This will process METADATA and PAYLOAD
     * tokens and invoke the PublishingActor's publish() method.
     *
     * @param commandId command ID for this subcommand
     * @param args String of parsable arguments
     * @param executor Executor for a NumberedCommandHandler that will execute
     *                 the parsed command
     * @throws ProtocolException if parsing errors occur
     * @throws IOException if I/O errors occur
     */
    public final void parseAndExecute(final int commandId,
                                      final String args,
                                      final Executor executor)
        throws ProtocolException, IOException {
        // Validate args.
        if (args != null && args.length() != 0) {
            throw new ProtocolException(String.format("PUBLISH command does "
                + "not take any parameters; received [%s].", args));
        }
        // Validate incoming input tokens.
        LineRawReader input = getInput();
        verifyExpectedInput("METADATA");
        // Note that metadata will be validated by the server upon publishing.
        final String metadata = input.read();
        /*
         * Note that payload will be read in its entirety here, even if it is
         * composed of raw data.
         */
        verifyExpectedInput("PAYLOAD");
        StringBuilder totalPayload = new StringBuilder();
        // TODO(njhwang) is it better to convert a bunch of char[] to Strings
        // and then concat, or to concat a bunch of char[] and then convert to
        // String?
        String partialPayload = input.read();
        while (!partialPayload.equals("ENDPAYLOAD")) {
          totalPayload.append(partialPayload);
          partialPayload = input.read();
        }
        final String finalPayload = totalPayload.toString();
        verifyExpectedInput("ENDPUBLISH");
        verifyExpectedInput("ENDCOMMAND");
        // Have the PublishingActor publish the data.
        executor.execute(new Runnable() {
          public void run() {
            try {
              writeResults(commandId,
                publisher.publish(metadata, finalPayload));
            } catch (IOException e) {
              LOGGER.error("Encountered IOException when attempting to write "
                + "PUBLISH results", e);
              System.exit(1);
            }
          }
        });
    }
}
