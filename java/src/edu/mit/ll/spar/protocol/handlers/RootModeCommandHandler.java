//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Abstract handler class that represents a LineRawHandler
//                      that handles root mode commands. Requires the
//                      definition of a parseAndExecute(args) method that takes
//                      in a String parameter of parsable arguments
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120817       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Abstract class that resolves line raw data into fully qualified root mode
 * commands, and subsequently executes those commands in the appropriate manner.
 *
 * All subclasses must define a parseAndExecute() method.
 *
 * parseAndExecute() is meant to facilitate all necessary reads from the
 * associated LineRawReader until the next command is ready to be read. It
 * then acts upon the parsed data in whatever manner is appropriate (i.e.,
 * requesting an actor to do something, writing something to output, etc.).
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see LineRawHandler
 * @see RootModeHandler
 */
public abstract class RootModeCommandHandler extends LineRawHandler {
    /**
     * Constructor.
     *
     * @param in LineRawReader to read data from
     */
    public RootModeCommandHandler(final LineRawReader in) {
        super(in);
    }

    /**
     * Completes any required parsing on the input and responds in whatever
     * manner is appropriate to the received input. This behavior is application
     * dependent, and subclasses of RootModeCommandHandler will need to maintain
     * whatever state is required to respond to the parsed input.
     *
     * @param args String of parsable arguments passed in by a RootModeHandler
     * @throws ProtocolException if any parsing errors occur
     * @throws IOException if any I/O errors occur
     */
    public abstract void parseAndExecute(final String args)
        throws ProtocolException, IOException;
}
