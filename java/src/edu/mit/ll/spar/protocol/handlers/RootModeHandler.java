//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Parses and acts upon input when in root mode for a line
//                      raw protocol.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120811       ni24039         Original version
// 120817       ni24039         Revisions in response to review 62
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import java.util.Collections;
import java.util.Map;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Class that facilitates handling and parsing of line raw data in root mode,
 * and executing the relelvant RootModeCommandHandler.
 *
 * All line raw protocols begin in root mode and wait to receive proper command
 * tokens. To this end, this class relies on a LineRawHandlerFactory map as a
 * parameter that maps token Strings to the appropriate RootModeCommandHandler
 * factory. For example, if the protocol supports the root mode commands
 * "STARTUP" and "SHUTDOWN", the mapping would map the "STARTUP" String to a
 * LineRawHandlerFactory that produces StartupCommandHandlers, and map the
 * "SHUTDOWN" String to one that produces ShutdownCommandHandlers.
 *
 * When parseAndExecute() is called, RootModeHandler will resolve the new
 * LineRawHandler that needs to be invoked, as well as any parameters that need
 * to be passed to it. The new LineRawHandler's parseAndExecute() method will
 * then be invoked for further processing. For convenience, a RootModeHandler's
 * parseAndExecute() method will return the token String that identifies the
 * resulting handler that was just invoked. This, for example, allows a user to
 * know that a "SHUTDOWN" command was just received, and can begin shutting down
 * the master application while the ShutdownCommandHandler does its thing.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see LineRawHandler
 * @see LineRawHandlerFactory
 * @see RootModeCommandHandler
 */
public class RootModeHandler extends LineRawHandler {
    /**
     * Number of tokens to look for when parsing with
     * LineRawHandler.readTokens(). This comprises the name of the root mode
     * command to invoke, and the String of arguments to pass to that root mode
     * command's LineRawHandler.
     */
    private static final int DESIRED_TOKEN_COUNT = 2;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(RootModeHandler.class);
    /**
     * Mapping between token Strings to the LineRawHandlerFactory
     * that will be invoked when that token is received.
     */
    private Map<String, LineRawHandlerFactory> factoryMap;

    /**
     * Constructor.
     *
     * @param in LineRawReader to read data from
     * @param map factory map representing command mapping
     */
    public RootModeHandler(
        final LineRawReader in,
        final Map<String, LineRawHandlerFactory> map) {
        super(in);
        // Make sure map cannot be tinkered with.
        factoryMap = Collections.unmodifiableMap(map);
    }

    /**
     * Parses the next command and executes the appropriate command
     * handler.
     *
     * This will resolve the next command and its associated
     * parameters if it receives a valid set of tokens. It will then
     * invoke the appropriate command handler's parseAndExecute() method
     * for further parsing of the data needed to execute the command.
     *
     * @return String representing command that was invoked by this call
     * @throws ProtocolException if any parsing errors occur
     * @throws IOException if any I/O errors occur
     */
    public final String parseAndExecute()
        throws ProtocolException, IOException {
        // Read in the command token and parameters.
        String[] tokens = readTokens(DESIRED_TOKEN_COUNT);
        // Check if a constructor is mapped to the received command token.
        if (!(factoryMap.containsKey(tokens[0]))) {
            throw new ProtocolException(String.format(
                "Unrecognized root mode command [%s].", tokens[0]));
        }
        // Instantiate the new command handler.
        LineRawHandler handler = factoryMap.get(tokens[0]).getHandler();
        assert handler instanceof RootModeCommandHandler : "Root mode can only "
            + "launch RootModeCommandHandlers.";
        // Execute the command handler with any received parameters.
        ((RootModeCommandHandler) handler).parseAndExecute(tokens[1]);
        // Return the command name to the caller.
        return tokens[0];
    }
}
