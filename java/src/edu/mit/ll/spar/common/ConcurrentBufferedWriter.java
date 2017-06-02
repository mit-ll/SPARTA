//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2012-12-21 16:15:00 -0500 (Fri, 21 Dec 2012) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Makes all writer operations synchronied and thread-safe
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120810       ni24039         Original version
// 120815       ni24039         Encapsulated private instance instead of
//                              inheriting from BufferedWriter
//*****************************************************************************
package edu.mit.ll.spar.common;

import java.io.BufferedWriter;
import java.io.Writer;

import java.io.IOException;

/**
 * Thread-safe version of BufferedWriter; only implements some constructors
 * and methods.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2118 $
 * @see BufferedWriter
 */
public class ConcurrentBufferedWriter extends Writer {
    /** Private instance of BufferedWriter. */
    private BufferedWriter writer;

    /**
     * See BufferedWriter docs.
     *
     * @param out Writer
     * @param size int
     * @throws IOException for I/O errors
     */
    public ConcurrentBufferedWriter(final Writer out, final int size)
        throws IOException {
        writer = new BufferedWriter(out, size);
    }

    /**
     * See BufferedWriter docs.
     *
     * @throws IOException for I/O errors
     */
    public final synchronized void close() throws IOException {
        writer.close();
    }

    /**
     * See BufferedWriter docs.
     *
     * @throws IOException for I/O errors
     */
    public final synchronized void flush() throws IOException {
        writer.flush();
    }

    /**
     * See BufferedWriter docs.
     *
     * @param str String
     * @throws IOException for I/O errors
     */
    public final synchronized void write(final String str) throws IOException {
        writer.write(str);
    }

    /**
     * See BufferedWriter docs.
     *
     * @param cbuf char[]
     * @param off int offset
     * @param len int length
     * @throws IOException for I/O errors
     */
    public final synchronized void write(
        final char[] cbuf, final int off, final int len) throws IOException {
        writer.write(cbuf, off, len);
    }

    /**
     * See BufferedWriter docs.
     *
     * @return String
     */
    public final synchronized String toString() {
      return writer.toString();
    }
}
