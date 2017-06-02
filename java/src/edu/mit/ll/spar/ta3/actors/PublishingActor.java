//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-16 14:25:52 -0400 (Tue, 16 Apr 2013) $
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

/**
 * Abstract class for all actors in TA3.1 baseline.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2985 $
 */
public abstract class PublishingActor extends PubSubActor {
    /**
     * Abstract method used to clear actor caches. Generic Exception is expected
     * to cater to any implementation of clearcache().
     *
     * @throws Exception if anything goes wrong
     */
    public abstract String publish(final String metadata, final String payload);
}
