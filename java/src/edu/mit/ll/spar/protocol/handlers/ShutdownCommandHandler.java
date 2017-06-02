//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Subcommand handler for SHUTDOWN commands sent to a
//                      system under test.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;

/**
 * Subcommand handler that parses and acts upon an already received
 * SHUTDOWN subcommand token.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see RootModeCommandHandler
 */
public class ShutdownCommandHandler extends RootModeCommandHandler {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(ShutdownCommandHandler.class);
    /** Output. */
    private Writer output;

    /**
     * Constructor.
     *
     * @param in LineRawReader used for input
     * @param out Writer used for output
     */
    public ShutdownCommandHandler(final LineRawReader in,
                                  final Writer out) {
        super(in);
        output = out;
    }

    /**
     * Parse and execute method.
     *
     * @param args String of parsable arguments (in this case, should be null or
     *             empty)
     * @throws ProtocolException if parsing errors occur
     */
    public final void parseAndExecute(final String args)
        throws ProtocolException {
        // Validate args.
        if (args != null && args.length() != 0) {
            throw new ProtocolException(String.format("SHUTDOWN command does "
                + "not take any parameters; received [%s].", args));
        }
        /*
         * Note that this doesn't actually do anything. While this could invoke
         * a shutdown command for the system under test, that would require this
         * to have access to the system under test's shutdown command, and also
         * be smart enough to gracefully terminate line raw handling processes
         * while the system under test shuts down. It was deemed simpler to just
         * have a stubbed handler for SHUTDOWN commands, allow the
         * RootModeHandler to report back to the application that a SHUTDOWN was
         * received, and have the application itself invoke the shutdown
         * sequence.
         */
    }
}
