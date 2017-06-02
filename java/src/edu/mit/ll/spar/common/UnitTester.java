//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2012-12-21 16:15:00 -0500 (Fri, 21 Dec 2012) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Base class for all JUnit test classes
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120727       ni24039         Original Version
// 120803       ni24039         Minor stylistic changes
// 120811       ni24039         Added DEFAULT_BUFFER_SIZE
//*****************************************************************************
package edu.mit.ll.spar.common;

import java.util.Random;
import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Base class for all JUnit test classes.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2118 $
 */
public class UnitTester {
    // TODO(njhwang) Look into using @Before(Class)

    /** Default buffer size for readers and writers. */
    public static final int DEFAULT_BUFFER_SIZE = 1024;

    /** Unit test class logger. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(UnitTester.class);

    /**
     * Returns a new random number generator and logs the seed for debugging
     * purposes.
     *
     * @return random number generator
     */
    protected final Random newRandGen() {
        long randSeed = new Random().nextLong();
        LOGGER.info("Using random generator with seed {}.", randSeed);
        return new Random(randSeed);
    }
}
