//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Handles/parses line raw data for the COMMAND root mode
//                      command
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120731       ni24039         Original version
// 120808       ni24039         Revisions in response to review 44
// 120811       ni24039         Revisions in response to review 44
// 120816       ni24039         Revisions in response to code review
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import edu.mit.ll.spar.common.SerialExecutor;

import java.util.Collections;
import java.util.Map;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.IOException;

/**
 * Class that facilitates handling and parsing of line raw numbered
 * commands (i.e., "COMMAND %d"), and executing the relevant SubcommandHandler.
 *
 * NumberedCommandHandler will be responsible for handling all line raw data
 * from the time a "COMMAND %d" is received, until after the "ENDCOMMAND" string
 * is received.
 *
 * This class relies on a LineRawHandlerFactory mapping as a parameter that can
 * map received token Strings to the appropriate SubcommandHandler factory. For
 * example, if this NumberedCommandHandler supports the subcommands "EATDINNER"
 * and "WASHDISHES", the mapping would map the "EATDINNER" string to a
 * EatDinnerSubcommandHandler factory and map the "WASHDISHES" string to the
 * WashDishesSubcommandHandler factory.
 *
 * When parseAndExecute() is called, NumberedCommandHandler will resolve
 * the new SubcommandHandler that needs to be invoked, as well as any parameters
 * that need to be passed to it. The new SubcommandHandler's parseAndExecute()
 * method will then be invoked for further processing.
 *
 * Note that commands are all executed serially, and that no threads are spawned
 * by this handler to parallelize command execution. This was designed to
 * ensure commands are executed and completed in the order that they were
 * received. However, commands can be parsed in parallel to other commands being
 * executed.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see RootModeCommandHandler
 * @see RootModeHandler
 * @see LineRawHandlerFactory
 * @see SubcommandHandler
 */
public class NumberedCommandHandler extends RootModeCommandHandler {
    /** Number of tokens to look for when parsing. This comprises the subcommand
     * name, as well as any arguments that should be passed to the associated
     * SubcommandHandler. */
    private static final int DESIRED_TOKEN_COUNT = 2;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(NumberedCommandHandler.class);
    /**
     * The mapping between received token Strings and the factory
     * that will be invoked when that token is received.
     */
    private Map<String, LineRawHandlerFactory> factoryMap;
    /**
     * Executor for numbered commands. This will ensure that commands are
     * executed in the order they are received, and allows parsed commands to be
     * queued for execution while parsing continues. This executor will be
     * passed to SubcommandHandlers so they can submit Runnables to it.
     */
    private final SerialExecutor executor = new SerialExecutor();

    /**
     * Constructor.
     *
     * @param in LineRawReader to read data from
     * @param map factory map representing the command mapping
     */
    public NumberedCommandHandler(
        final LineRawReader in,
        final Map<String, LineRawHandlerFactory> map) {
        super(in);
        factoryMap = Collections.unmodifiableMap(map);
    }

    /**
     * Completes any outstanding numbered command requests that were
     * successfully parsed but may not have reported results yet.
     */
    public final void shutdown() {
      executor.executeAll();
    }

    /**
     * Parses the next command and invokes the appropriate command
     * handler.
     *
     * This will resolve the next subcommand and its associated
     * parameters if it receives a valid set of tokens. It will then
     * invoke the appropriate subcommand handler's parseAndExecute() method
     * for further parsing of the data needed to execute the subcommand.
     *
     * @param args String with parsable arguments (in this case, should be a
     *             command ID integer)
     * @throws ProtocolException if any parsing errors occur
     * @throws IOException if any I/O errors occur
     */
    public final void parseAndExecute(final String args)
        throws ProtocolException, IOException {
        // Validate args.
        if (args == null || args.length() <= 0) {
          throw new ProtocolException("COMMAND token requires a command ID "
              + "argument.");
        }
        String[] argArray = args.split(" ");
        int commandId = -1;
        if (argArray.length != 1) {
            throw new ProtocolException(String.format("COMMAND token requres "
                + " a single command ID argument; received [%s].", args));
        } else {
            try {
                commandId = Integer.parseInt(argArray[0]);
            } catch (NumberFormatException e) {
                throw new ProtocolException(String.format(
                    "COMMAND token requires an integer command ID argument; "
                    + "received [%s].", argArray[0]));
            }
        }
        if (commandId < 0) {
            throw new ProtocolException(String.format("COMMAND token requires "
                + " a positive command ID argument; received [%d].",
                commandId));
        }
        // TODO(njhwang) create some type of safe guard so the same command ID
        // is not accepted twice
        // Read in the command string and parameters. Note that a
        // ProtocolException will be thrown if no valid tokens could be read.
        String[] tokens = readTokens(DESIRED_TOKEN_COUNT);
        // Check if a factory is mapped to the received subcommand string.
        if (!(factoryMap.containsKey(tokens[0]))) {
            throw new ProtocolException(String.format(
                "Unrecognized subcommand [%s].", tokens[0]));
        }
        // Instantiate the new subcommand handler.
        LineRawHandler handler = factoryMap.get(tokens[0]).getHandler();
        assert handler instanceof SubcommandHandler : "NumberedCommandHandler "
          + "can only launch SubcommandHandlers.";
        // Execute the subcommand handler.
        ((SubcommandHandler) handler).parseAndExecute(commandId, tokens[1],
                                                      executor);
    }
}
