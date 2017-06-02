//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Facilitates reading of line raw data.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120720       ni24039         Original version; rewrite in response to
//                              review 21
// 120727       ni24039         Changes in response to review 21
// 120803       ni24039         Minor stylistic changes
//*****************************************************************************
package edu.mit.ll.spar.protocol.reader;

import static edu.mit.ll.spar.common.PrimitiveUtils.concatArrays;

import java.nio.channels.ReadableByteChannel;
import java.nio.channels.Channels;
import java.io.FileInputStream;
import java.io.FileDescriptor;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.InputStream;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import java.nio.channels.AsynchronousCloseException;
import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.UnsupportedEncodingException;
import java.io.IOException;

/**
 * Facilitates parsing of data from an InputStream that uses a "line raw"
 * protocol; a line raw protocol interprets data in either "line" or "raw"
 * mode.
 *
 * LineRawReader begins in line mode by default.
 *
 * In line mode, data is delimited by a line feed ('\n') or carriage return
 * ('\r') or a carriage return immediately followed by a line feed. The data
 * returned will be all characters up to but not including the delimiting
 * string.
 *
 * In raw mode, data must first be declared as raw by sending RAW\n when
 * in line mode (\n being any valid EOL sequence as explained above).
 * Then, a positive integer must be sent, followed by another EOL sequence.
 * This integer specifies the number of data bytes to be read. After
 * sending the appropriate number of bytes, the sender can either continue
 * in raw mode, or return to line mode by sending ENDRAW\n. The data
 * returned will be all the relevant data bytes sent between RAW and ENDRAW
 * (i.e., if RAW\n4\nabcd2\nefENDRAW\n is sent, only abcdef will be
 * returned).
 *
 * At construction, a valid InputStream (i.e. System.in) must be passed
 * to the constructor. LineRawReader can then be accessed via the read()
 * method, which will block until a valid String of data can be returned.
 * 
 * TODO(njhwang) make it such that line/raw data are processed differently such
 * that raw data is never parsed for command tokens in the handlers.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public class LineRawReader {
    /*
     * This does not extend java.io.Reader since that requires implementing
     * read(char[], int, int), which isn't convenient for our purposes
     * and would likely lead to confusion. Instead, a custom Reader-esque
     * class has been designed that is accessible via a single read method.
     */
    /** Logger for an instance of this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(LineRawReader.class);
    /**
     * String encoding used to process incoming data. Note that the character
     * encoding is hardcoded here; change it if your application requires a
     * different encoding.
     */
    private static final String STRING_ENCODING = "UTF-8";

    /** Reader where line raw data will be taken from. */
    private BufferedReader reader;
    private ReadableByteChannel byteChannel;

    /**
     * Constructor.
     *
     * @param inputStream an InputStream where line raw data will be taken from
     * @param size size of buffer to use with BufferedReader
     */
    public LineRawReader(final InputStream inputStream, final int size) {
        try {
            reader = new BufferedReader(
                new InputStreamReader(inputStream, STRING_ENCODING), size);
        } catch (UnsupportedEncodingException e) {
            LOGGER.error("Encountered unsupported encoding specifier.", e);
            System.exit(1);
        }
        byteChannel = null;
    }

    public LineRawReader(final FileDescriptor fd, final int size) {
        try {
            byteChannel = (new FileInputStream(fd)).getChannel();
            reader = new BufferedReader(
                new InputStreamReader(Channels.newInputStream(byteChannel), 
                                      STRING_ENCODING), 
                size);
        } catch (UnsupportedEncodingException e) {
            LOGGER.error("Encountered unsupported encoding specifier.", e);
            System.exit(1);
        }
    }

    /**
     * Closes reader and any associated streams/readers.
     *
     * @throws IOException if BufferedReader encounters any errors with the
     *                     underlying stream
     */
    public final void close() throws IOException {
        if (byteChannel != null) {
          byteChannel.close();
        }
        reader.close();
    }

    /**
     * Reads a line from BufferedReader, and throws an exception if EOF is
     * encountered.
     *
     * @return Line from input stream, without the EOL character.
     * @throws IOException if BufferedReader encounters any errors with the
     *                     underlying stream, or if EOF is reached on the
     *                     InputStream
     */
    private String guaranteedReadLine() throws IOException {
        /*
         * Note that BufferedReader.readLine() returns null when EOF is
         * reached and there is nothing in the buffer to read; if EOF is
         * encountered and there are bytes left in BufferedReader's buffer,
         * those remaining bytes will be interpreted as a valid line.
         * There is no way to avoid this behavior without writing a custom
         * BufferedReader, or repeatedly peeking ahead in the buffer to see if
         * EOF would be read before an EOL character.
         */
        String data = null;
        try {
          data = reader.readLine();
        } catch (AsynchronousCloseException e) {
          // TODO(njhwang) just convert to IOException? pass it on?? what to do
        }
        if (data == null) {
            throw new IOException("InputStream reached end of file.");
        }
        return data;
    }

    /**
     * Reads valid line raw data from the InputStream, and returns it as a
     * string.
     *
     * @return Line raw data read from InputStream.
     * @throws IOException if BufferedReader encounters any errors with the
     *                        underlying stream
     * @throws ProtocolException if protocol parsing errors occur
     */
    public final String read() throws IOException, ProtocolException {
        // TODO(njhwang) Benchmark using StringBuilder instead.
        String command;
        char[] rawData = null;

        // See class documentation for what qualifies as valid EOL sequences.
        command = guaranteedReadLine();
        // If RAW mode is not immediately entered, return command.
        if (!(command.equals("RAW"))) {
            return command;
        }
        // Otherwise, attempt to read in raw byte count.
        command = guaranteedReadLine();
        // Read raw chunks until ENDRAW is encountered.
        while (!(command.equals("ENDRAW"))) {
            char[] rawChunk;
            int rawCount;
            int charsRead;
            int charsSaved = 0;
            /*
             * Parse out and validate raw byte count. If input is not an
             * integer, Integer.parseInt() will throw an exception.
             */
            try {
              rawCount = Integer.parseInt(command);
            } catch (NumberFormatException e) {
              throw new ProtocolException(String.format("Raw mode requires an"
                    + " integer byte count; received [%s].", command));
            }
            if (rawCount <= 0) {
                throw new ProtocolException(String.format("Raw mode requires a"
                      + " positive byte count; received %d.", rawCount));
            }
            // Read until raw chunk is filled with correct number of bytes.
            rawChunk = new char[rawCount];
            while (charsSaved < rawCount) {
                charsRead = reader.read(rawChunk, charsSaved,
                                        rawCount - charsSaved);
                if (charsRead < 0) {
                    throw new IOException("InputStream reached end of file.");
                }
                charsSaved += charsRead;
            }
            /*
             * Concatenate the already read bytes (rawData) with the newly
             * read bytes (rawChunk).
             */
            if (rawData == null) {
                rawData = rawChunk;
            } else {
                rawData = concatArrays(rawData, rawChunk);
            }
            // Read in the next command.
            command = guaranteedReadLine();
        }
        /*
         * If rawData is null at this point, then raw chunks were never read
         * and no valid integer/byte stream pairs were encountered prior to
         * receiving ENDRAW.
         */
        if (rawData == null) {
            throw new ProtocolException("ENDRAW received directly after RAW.");
        }
        // Return raw data.
        return new String(rawData);
    }
}
