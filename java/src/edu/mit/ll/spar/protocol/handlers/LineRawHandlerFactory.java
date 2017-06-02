//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Class that acts as a closure that can produce
//                      LineRawHandlers instances.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120811       ni24039         Original version
// 120815       ni24039         Changed from interface to a class
// 120817       ni24039         Simplified and made concrete to apply to all
//                              LineRawHandler subclasses
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Class that acts as a closure that can produce LineRawHandler instances.
 * getHandler() returns an instance of the handler of interest.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see LineRawHandler
 */
public class LineRawHandlerFactory {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(LineRawHandlerFactory.class);
    /** Private handler instance. */
    private LineRawHandler handlerInstance;

    /**
     * Constructor.
     *
     * @param inst LineRawHandler instance to use
     */
    public LineRawHandlerFactory(final LineRawHandler inst) {
        handlerInstance = inst;
    }

    /**
     * Return the LineRawHandler instance.
     *
     * @return LineRawHandler instance
     */
    public final LineRawHandler getHandler() {
        return handlerInstance;
    }
}
