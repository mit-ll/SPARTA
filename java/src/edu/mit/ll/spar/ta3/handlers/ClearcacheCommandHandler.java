//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Subcommand handler for CLEARCACHE commands sent to a
//                      SPAR actor
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.handlers;

import edu.mit.ll.spar.protocol.handlers.RootModeCommandHandler;
import edu.mit.ll.spar.ta3.actors.PubSubActor;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Subcommand handler that parses and acts upon an already received
 * CLEARCACHE subcommand token. Handler will have the PubSubActor call
 * its clearcache() method.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see RootModeCommandHandler
 * @see PubSubActor
 */
public class ClearcacheCommandHandler extends RootModeCommandHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(ClearcacheCommandHandler.class);
    /** Actor whose cache needs to be cleared. */
    private PubSubActor actor;
    /** Output. */
    private Writer output;

    /**
     * Constructor.
     *
     * @param in LineRawReader used for input
     * @param out Writer used for output
     * @param act PubSubActor that will have its cache cleared
     */
    public ClearcacheCommandHandler(final LineRawReader in,
                                    final Writer out,
                                    final PubSubActor act) {
        super(in);
        output = out;
        actor = act;
    }

    /**
     * Parse and execute method.
     *
     * @param args String of parsable arguments (in this case, should be null or
     *             empty)
     * @throws ProtocolException if parsing errors occur
     * @throws IOException if I/O errors occur
     */
    public final void parseAndExecute(final String args)
        throws ProtocolException, IOException {
        // Validate args.
        if (args != null && args.length() != 0) {
            throw new ProtocolException(String.format("CLEARCACHE command does "
                + "not take any parameters; received [%s].", args));
        }
        // Have the actor process CLEARCACHE.
        try {
          actor.clearcache();
          output.write("DONE\n");
          output.flush();
        } catch (Exception e) {
          String errorMessage = "Encountered exception during actor "
            + "CLEARCACHE. Terminating application.";
          LOGGER.error(errorMessage, e);
          System.exit(1);
        }
    }
}
