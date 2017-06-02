//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Abstract class for all actors in TA3.1 baseline
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.actors;

import edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler;
import edu.mit.ll.spar.protocol.handlers.RootModeHandler;

import java.util.Scanner;
import java.io.File;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import java.io.IOException;

/**
 * Abstract class for all actors in TA3.1 baseline.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public abstract class PubSubActor {
    // TODO(njhwang) Put these in a config file
    /** Messages intended for users are sent on this topic. */
    protected static final String TOPIC_NAME = "SPAR_TOPIC";
    /** Broker name. */
    protected static final String BROKER_NAME = "SPAR_BROKER";
    /** Default buffer size for I/O. */
    protected static final int DEFAULT_BUFFER_SIZE = 1024;
    /**
     * There is also a control connection that allows the publisher to indicate
     * that it's sent all messages and it is thus safe for the clients to shut
     * down, etc. This is the topic for control connections.
     */
    protected static final String CONTROL_TOPIC_NAME = "SPAR_CONTROL";
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(PubSubActor.class);

    /** RootModeHandler for this actor. */
    private RootModeHandler rootModeHandler;
    /**
     * NumberedCommandHandler for this actor. Should have shutdown() called on
     * it when processing is complete.
     */
    private NumberedCommandHandler numberedCommandHandler;

    /**
     * Getter for rootModeHandler.
     *
     * @return RootModeHandler
     */
    protected final RootModeHandler getRootModeHandler() {
      return rootModeHandler;
    }

    /**
     * Setter for rootModeHandler.
     *
     * @param rmh RootModeHandler
     */
    protected final void setRootModeHandler(final RootModeHandler rmh) {
      rootModeHandler = rmh;
    }

    /**
     * Getter for numberedCommandHandler.
     *
     * @return NumberedCommandHandler
     */
    protected final NumberedCommandHandler getNumberedCommandHandler() {
      return numberedCommandHandler;
    }

    /**
     * Setter for numberedCommandHandler.
     *
     * @param nch NumberedCommandHandler
     */
    protected final void setNumberedCommandHandler(
        final NumberedCommandHandler nch) {
      numberedCommandHandler = nch;
    }

    /**
     * Abstract method used to shutdown actors. Generic Exception is expected to
     * cater to any implementation of shutdown().
     *
     * @throws Exception if anything goes wrong
     */
    public abstract void shutdown() throws Exception;

    /**
     * Abstract method used to clear actor caches. Generic Exception is expected
     * to cater to any implementation of clearcache().
     *
     * @throws Exception if anything goes wrong
     */
    public abstract void clearcache() throws Exception;
}
