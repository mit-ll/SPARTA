//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Handles/parses line raw data for subcommands executed
//                      by a NumberedCommandHandler.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120808       ni24039         Original version
// 120817       ni24039         Revisions in response to code review
// 121204       ni24039         Updates for initial release
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import java.util.concurrent.Executor;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Abstract class that facilitates handling and parsing of line raw data
 * required to build and execute subcommands executed by a
 * NumberedCommandHandler.
 *
 * parseAndExecute() should parse all information up to and including
 * the "ENDCOMMAND" string. Upon resolving the full command, it should
 * then invoke the appropriate action in response to the parsed command
 * (usually involving telling an external party to do something and write
 * results).
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see LineRawHandler
 * @see NumberedCommandHandler
 */
public abstract class SubcommandHandler extends LineRawHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(SubcommandHandler.class);
    /** Output to write results to. */
    private Writer output;

    /**
     * Constructor.
     *
     * @param in LineRawReader to read line raw data from
     * @param out Writer to write output to
     */
    public SubcommandHandler(final LineRawReader in,
                             final Writer out) {
        super(in);
        output = out;
    }

    /**
     * Completes any required parsing on the input and responds in whatever
     * manner is appropriate to the received input. This behavior is
     * application dependent, and subclasses of SubcommandHandler will need to
     * maintain whatever state is required to respond to the parsed input.
     *
     * @param commandId command ID for the subcommand being processed
     * @param args String of parsable arguments
     * @param executor Executor tied to a NumberedCommandHandler that will queue
     *                 any relevant tasks and execute them serially
     * @throws ProtocolException if any parsing errors occur
     * @throws IOException if any I/O errors occur
     */
    public abstract void parseAndExecute(final int commandId,
                                         final String args,
                                         final Executor executor)
        throws ProtocolException, IOException;

    /**
     * Writes a numbered results sequence to the output. Numbered results
     * sequences start with "RESULTS %d\n", where %d represents the command ID
     * for the command this is writing results for. This is followed by either
     * "DONE\n" in the nominal case, or a "FAILED\nfailure_dataENDFAILED\n"
     * sequence, followed by "ENDRESULTS\n".
     *
     * @param commandId command ID for the subcommand returning the results
     * @param results String containing the subcommand results; if null, the
     *                subcommand is assumed to have successfully completed,
     *                otherwise, it is assumed that results represents a failure
     *                message
     * @throws IOException if any I/O errors occur
     */
    protected final void writeResults(final int commandId, final String results)
      throws IOException {
        // TODO(njhwang) Will System.setProperty("line.separator", "\n") help
        // us in any way with platform independency?
        StringBuilder writeString =
            new StringBuilder(String.format("RESULTS %d\n", commandId));
        if (results == null) {
            writeString.append("DONE\n");
        } else {
            writeString.append(
              String.format("FAILED\n%s\nENDFAILED\n", results));
        }
        writeString.append("ENDRESULTS\n");
        output.write(writeString.toString());
        output.flush();
    }
}
