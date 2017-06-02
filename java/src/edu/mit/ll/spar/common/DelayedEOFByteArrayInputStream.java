//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2012-12-21 16:15:00 -0500 (Fri, 21 Dec 2012) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Extends ByteArrayInputStream to delay for a set amount
//                      of time whenever EOF is detected.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120723       ni24039         Original Version
// 120803       ni24039         Minor stylistic changes
//*****************************************************************************
package edu.mit.ll.spar.common;

import java.io.ByteArrayInputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Extends ByteArrayInputStream to delay for a set amount of time whenever EOF
 * is detected.
 *
 * Generally used for testing applications that rely on BufferedReaders to read
 * dynamic information from InputStreams. It is recommended to make a Vector of
 * several DelayedEOFByteArrayInputStreams and pass the elements of the Vector
 * to a SequenceInputStream to simulate a continuous InputStream with delays
 * in between byte chunks.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2118 $
 */
public class DelayedEOFByteArrayInputStream extends ByteArrayInputStream {
    /*
     * Some notes on the design decisions here:
     *
     * To simulate dynamic InputStreams, ByteArrayInputStreams are difficult to
     * use by themselves, since 1) when EOF is detected,
     * BufferedReader.readLine() will return everything left in the stream,
     * which is undesirable if attempting to simulate processing of partial
     * lines, and 2) it is cumbersome to simulate delays in the InputStream
     * using ByteArrayInputStreams by themselves, as it tends to require a lot
     * of synchronization in client classes to prevent concurrency issues when
     * switching to new ByteArrayInputStreams for fresh data. Using the Robot
     * class was also considered for this purpose, but was deemed inappropriate
     * due to the amount of control of the workstation the developer needs to
     * yield to the Robot during unit testing.
     */

    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(DelayedEOFByteArrayInputStream.class);
    /** Delay that will be incurred whenever EOF is reached. */
    private final int delay;

    /**
     * Constructor that loads a byte array buffer.
     *
     * @param desiredBuf byte array to use as the byte buffer
     * @param desiredDelay number of milliseconds to delay at EOF
     */
    public DelayedEOFByteArrayInputStream(
        final byte[] desiredBuf, final int desiredDelay) {
        super(desiredBuf);
        delay = desiredDelay;
    }

    /**
     * Constructor that loads a byte array buffer with a length and offset.
     *
     * @param desiredBuf byte array to use as the byte buffer
     * @param desiredOffset offset at which to start reading from the buffer
     * @param desiredLength maximum number of bytes to read from the buffer
     * @param desiredDelay number of milliseconds to delay at EOF
     */
    public DelayedEOFByteArrayInputStream(
        final byte[] desiredBuf, final int desiredOffset,
        final int desiredLength, final int desiredDelay) {
        super(desiredBuf, desiredOffset, desiredLength);
        delay = desiredDelay;
    }

    /**
     * Reads the next byte of data, and delays when EOF is encountered.
     *
     * @return The next byte of data, or -1 if EOF has been reached and the
     *         delay has completed.
     */
    @Override
    public final int read() {
        int result = super.read();
        if (result == -1) {
            try {
                Thread.currentThread().sleep(delay);
            } catch (InterruptedException e) {
                LOGGER.error(
                    "Encountered InterruptedException during delay.", e);
            }
        }
        return result;
    }

    /**
     * Reads up to len bytes of data into an array of bytes, and delays when
     * EOF is reached.
     *
     * @param b the buffer into which data is read
     * @param off the start offset of the data
     * @param len the maximum number of bytes to read
     * @return The next byte of data, or -1 if EOF has been reached and the
     *         delay has completed.
     */
    @Override
    public final int read(final byte[] b, final int off, final int len) {
        int result = super.read(b, off, len);
        if (result == -1) {
            try {
                Thread.currentThread().sleep(delay);
            } catch (InterruptedException e) {
                LOGGER.error(
                    "Encountered InterruptedException during delay.", e);
            }
        }
        return result;
    }
}
