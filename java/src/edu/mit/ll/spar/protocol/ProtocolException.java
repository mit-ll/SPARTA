//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Thrown when protocol parsing errors are encountered.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120727       ni24039         Original Version; rewrite in response to
//                              review 21
//*****************************************************************************
package edu.mit.ll.spar.protocol;

/**
 * Exception to throw when protocl parsing errors occur.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public class ProtocolException extends Exception {

    /**
     * Constructor.
     *
     * @param message String to print when exception occurs
     */
    public ProtocolException(final String message) {
        super(message);
    }

}
