//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2012-12-21 16:15:00 -0500 (Fri, 21 Dec 2012) $
// Project:             SPAR
// Authors:             ni24039
// Description:         BasicLineRawHandler; abstract handler class that
//                      requires the definition of a parseAndExecute(args)
//                      method that takes in a String parameter of parsable
//                      arguments
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
 * Abstract class that provides means to resolve line raw data into
 * fully qualified commands, and subsequently execute those commands in
 * the appropriate manner.
 *
 * All subclasses must define a parseAndExecute() method.
 *
 * parseAndExecute() is meant to facilitate all necessary reads from the
 * associated LineRawReader and resolve valid line raw data to act upon. It
 * then acts upon the parsed data in whatever manner is appropriate (i.e.,
 * launching a thread to execute a task, writing something to output, etc.).
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2118 $
 * @see LineRawHandler
 * @see LineRawHandlerFactory
 */
public abstract class BasicLineRawHandler extends LineRawHandler {
    /**
     * Constructor.
     *
     * @param in LineRawReader input
     */
    public BasicLineRawHandler(final LineRawReader in) {
        super(in);
    }

    /**
     * Completes any required parsing on the input and responds in whatever
     * manner is appropriate to the received input. This behavior is
     * application dependent, and subclasses of LineRawHandler will need to
     * maintain whatever state is required to respond to the parsed input.
     *
     * @param args String of parsable arguments
     * @throws ProtocolException if any parsing errors occur
     * @throws IOException if any I/O errors occur
     */
    public abstract void parseAndExecute(final String args)
        throws ProtocolException, IOException;
}
