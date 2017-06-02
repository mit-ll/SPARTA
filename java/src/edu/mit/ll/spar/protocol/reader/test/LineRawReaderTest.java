//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Tests LineRawReader.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120720       ni24039         Original Version; rewrite in response to
//                              review 21
// 120727       ni24039         Updates in response to review 21
// 120803       ni24039         Double checked that Random seeds for the
//                              randomized test that previously failed now pass
//                              Also some minor stylistic changes
//*****************************************************************************
package edu.mit.ll.spar.protocol.reader.test;

import static edu.mit.ll.spar.protocol.reader.test.LineRawReaderUtils.*;
import static org.junit.Assert.*;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import edu.mit.ll.spar.common.UnitTester;
import org.junit.Test;

import edu.mit.ll.spar.common.DelayedEOFByteArrayInputStream;
import java.io.ByteArrayInputStream;
import java.io.SequenceInputStream;
import java.io.InputStream;

import java.util.Enumeration;
import java.util.Random;
import java.util.Vector;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;
import java.io.UnsupportedEncodingException;

/**
 * Unut tests for LineRawReader.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see     LineRawReader
 * @see     UnitTester
 */
public class LineRawReaderTest extends UnitTester {
    /** Buffer size to used with LineRawReader. */
    private static final int BUFFER_SIZE = 1024;
    /** Enumeration of line raw modes. */
    private enum LineRawMode { LINE, RAW };
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(LineRawReaderTest.class);

    /**
     * Tests processing of a single line in line mode.
     *
     * @throws Exception
     */
    @Test public final void singleLineTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString = "Good evening, gentlemen.\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString.trim(), readString);
    }

    /**
     * Tests processing of a single line in raw mode.
     *
     * @throws Exception
     */
    @Test public final void singleRawTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString = "GET TO THE CHOPPER!!\n";
        String fullString = rawModeWrapper(rawSequence(writeString));
        byte[] fullBytes = fullString.getBytes("UTF-8");
        ByteArrayInputStream input =  new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString, readString);
    }

    /**
     * Tests processing of a single line in raw mode with non-ASCII bytes;
     * includes testing of byte streams with nulls and line feeds.
     *
     * @throws Exception
     */
    @Test public final void singleRawNonASCIITest() throws Exception {
        LineRawReader r;
        String readString;
        char[] writeChars = new char[]{255, 127, 254, 0, 53, 128, 32, 10, 124};
        String writeString = new String(writeChars);
        assertEquals(writeChars.length, writeString.length());
        String fullString = rawModeWrapper(rawSequence(writeString));
        byte[] fullBytes = fullString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeChars.length, readString.length());
        assertEquals(writeString, readString);
    }

    /**
     * Tests processing of multiple lines in line mode.
     *
     * @throws Exception
     */
    @Test public final void multiLineTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "You either die a hero...\n";
        String writeString2 =
            "Or live long enough to see yourself become the villain.\n";
        byte[] fullBytes = (writeString1 + writeString2).getBytes();
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1.trim(), readString);
        readString = r.read();
        assertEquals(writeString2.trim(), readString);
    }

    /**
     * Tests processing of non-line-feed EOL delimiters.
     *
     * @throws Exception
     */
    @Test public final void otherEOLTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 =
            "I was wondering what part of you would break first.\r";
        String writeString2 =
            "Your soul...\r\n";
        String writeString3 =
            "Or your body.\n";
        byte[] fullBytes =
            (writeString1 + writeString2 + writeString3).getBytes();
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1.trim(), readString);
        readString = r.read();
        assertEquals(writeString2.trim(), readString);
        readString = r.read();
        assertEquals(writeString3.trim(), readString);
    }

    /**
     * Tests processing of multiple lines in raw mode.
     *
     * @throws Exception
     */
    @Test public final void multiRawTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "Cover me, Porkins!\n";
        String writeString2 = "I think I've got a problem!\n";
        String fullString = rawModeWrapper(
            rawSequence(writeString1) + rawSequence(writeString2));
        byte[] fullBytes = fullString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1 + writeString2, readString);
    }

    /**
     * Tests processing of a multiple lines in raw mode with non-ASCII bytes;
     * includes testing of byte streams with nulls and line feeds.
     *
     * @throws Exception
     */
    @Test public final void multiRawNonASCIITest() throws Exception {
        LineRawReader r;
        String readString;
        char[] writeChars1 =  new char[]{255, 127, 0, 10, 3, 6, 128,  0, 1,  2,
                                           3,   4, 5,  6, 7, 8,   9, 10, 0, 13};
        char[] writeChars2 = new char[]{13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3,
                                         2,  1,  0,  1, 2, 3, 4, 5, 6};
        String writeString1 = new String(writeChars1);
        String writeString2 = new String(writeChars2);
        String fullString = rawModeWrapper(
            rawSequence(writeString1) + rawSequence(writeString2));
        byte[] fullBytes = fullString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1 + writeString2, readString);
    }

    /**
     * Tests processing of negative byte counts in raw mode.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void negativeByteCountTest() throws Exception {
        LineRawReader r;
        String writeString = "RAW\n-24\n";
        byte[] fullBytes = writeString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        r.read();
    }

    /**
     * Tests processing of non-integer byte counts in raw mode.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void nonIntByteCountTest() throws Exception {
        LineRawReader r;
        String writeString = "RAW\nabcd\n";
        byte[] fullBytes = writeString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        r.read();
    }

    /**
     * Tests processing of a RAW/ENDRAW sequence with no data.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void emptyRawTest() throws Exception {
        LineRawReader r;
        String writeString = "RAW\nENDRAW\n";
        byte[] fullBytes = writeString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        r.read();
    }

    /**
     * Tests processing of an empty line in LINE mode.
     *
     * @throws Exception
     */
    @Test public final void emptyLineTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString = "Yes, this is dog.\n\n";
        byte[] fullBytes = writeString.getBytes("UTF-8");
        ByteArrayInputStream input = new ByteArrayInputStream(fullBytes);
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString.trim(), readString);
        readString = r.read();
        assertEquals("", readString);
    }

    /**
     * Tests multiple complete lines with delays in between.
     *
     * @throws Exception
     */
    @Test public final void multiLineDelayTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "That's no moon...\n";
        String writeString2 = "It's a space station.\n";
        r = new LineRawReader(new SequenceInputStream(
            new DelayedEOFByteArrayInputStream(
                writeString1.getBytes("UTF-8"), 500),
            new ByteArrayInputStream(writeString2.getBytes("UTF-8"))),
            BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1.trim(), readString);
        readString = r.read();
        assertEquals(writeString2.trim(), readString);
    }

    /**
     * Tests multiple complete raw lines with delays in between.
     *
     * @throws Exception
     */
    @Test public final void multiRawDelayTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "And you know the thing about chaos?\n";
        String writeString2 = "It's fair.\n";
        String fullString1 = "RAW\n" + rawSequence(writeString1);
        String fullString2 = rawSequence(writeString2) + "ENDRAW\n";
        r = new LineRawReader(new SequenceInputStream(
            new DelayedEOFByteArrayInputStream(
                fullString1.getBytes("UTF-8"), 500),
            new ByteArrayInputStream(fullString2.getBytes("UTF-8"))),
            BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString1 + writeString2,
                     readString);
    }

    /**
     * Tests a line that has a delay before an EOL delimiter is sent.
     *
     * @throws Exception
     */
    @Test public final void singleLineDelayTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "I want to take his face...";
        String writeString2 = "off.\n";
        r = new LineRawReader(new SequenceInputStream(
            new DelayedEOFByteArrayInputStream(
                writeString1.getBytes("UTF-8"), 500),
            new ByteArrayInputStream(writeString2.getBytes("UTF-8"))),
            BUFFER_SIZE);
        readString = r.read();
        assertEquals((writeString1 + writeString2).trim(),
                     readString);
    }

    /**
     * Tests a raw line that has a delay before all bytes are sent.
     *
     * @throws Exception
     */
    @Test public final void singleRawDelayTest() throws Exception {
        LineRawReader r;
        String readString;
        String writeString1 = "RAW\n10\nabcde";
        String writeString2 = "fghijENDRAW\n";
        r = new LineRawReader(new SequenceInputStream(
            new DelayedEOFByteArrayInputStream(
                writeString1.getBytes("UTF-8"), 500),
            new ByteArrayInputStream(writeString2.getBytes("UTF-8"))),
            BUFFER_SIZE);
        readString = r.read();
        assertEquals("abcdefghij",
                     readString);
    }

    /**
     * Tests lines that equal or exceed BUFFER_SIZE in length.
     *
     * @throws Exception
     */
    @Test public final void largeLineTest() throws Exception {
        LOGGER.info("Starting largeLineTest().");
        LineRawReader r;
        String readString;
        String writeString;
        Random rand = newRandGen();
        char[] writeChars = randomLineChars(rand, BUFFER_SIZE);

        writeString = new String(writeChars);
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString.substring(0, BUFFER_SIZE - 1), readString);

        writeChars = randomLineChars(rand, BUFFER_SIZE + 1);
        writeString = new String(writeChars);
        input = new ByteArrayInputStream(writeString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString.substring(0, BUFFER_SIZE + 1 - 1),
                     readString);
    }

    /**
     * Tests raw lines that equal or exceed BUFFER_SIZE in length.
     *
     * @throws Exception
     */
    @Test public final void largeRawTest() throws Exception {
        LOGGER.info("Starting largeRawTest().");
        LineRawReader r;
        String readString;
        String writeString;
        String fullString;
        ByteArrayInputStream input;
        Random rand = newRandGen();
        char[] writeChars = randomRawChars(rand, BUFFER_SIZE);

        writeString = new String(writeChars);
        fullString = rawModeWrapper(rawSequence(writeString));
        input =  new ByteArrayInputStream(fullString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString, readString);

        writeChars = randomRawChars(rand, BUFFER_SIZE + 1);
        writeString = new String(writeChars);
        fullString = rawModeWrapper(rawSequence(writeString));
        input =  new ByteArrayInputStream(fullString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString, readString);
    }

    /**
     * Tests a very large line.
     *
     * @throws Exception
     */
    @Test public final void megaLineTest() throws Exception {
        LOGGER.info("Starting megaLineTest().");
        LineRawReader r;
        String readString;
        int megaLength = 20000 * 1024;
        String writeString;
        Random rand = newRandGen();
        char[] writeChars = randomLineChars(rand, megaLength);

        writeString = new String(writeChars);
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString.substring(0, megaLength - 1), readString);
    }

    /**
     * Tests a very large raw line.
     *
     * @throws Exception
     */
    @Test public final void megaRawTest() throws Exception {
        LOGGER.info("Starting megaRawTest().");
        LineRawReader r;
        String readString;
        int megaLength = 20000 * 1024;
        String fullString;
        String writeString;
        byte[] fullBytes;
        ByteArrayInputStream input;
        Random rand = newRandGen();
        char[] writeChars = randomRawChars(rand, megaLength);

        writeString = new String(writeChars);
        fullString = rawModeWrapper(rawSequence(writeString));
        input =  new ByteArrayInputStream(fullString.getBytes("UTF-8"));
        r = new LineRawReader(input, BUFFER_SIZE);
        readString = r.read();
        assertEquals(writeString, readString);
    }

    /**
     * Extensive test that reads randomized data.
     *
     * Each iteration randomly goes into LINE or RAW mode with an appropriately
     * formatted line of random length. Each write is separated by a randomized
     * delay as well. Each write is additionaly split at some random index to
     * simulate the output of partial data. Each write is performed by
     * instantiating a DelayedLineRawInputThread that will reset the context's
     * InputStream.
     *
     * Note that this test can take a long time if maxIterations or
     * maxDelay is large, and could be ignored to speed up unit testing.
     *
     * @throws Exception
     */
    @Test public final void randomizedSequenceTest() throws Exception {
        LOGGER.info("Starting randomizedSequenceTest().");
        // TODO(njhwang) look into Paramterized from JUnit API
        // Set the variables below to parameterize the test
        int maxIterations = 10;
        int maxDelay = 20;

        LineRawReader r;
        int dataLength;
        LineRawMode mode;
        LineRawMode prevMode = LineRawMode.LINE;
        int dataSplit;
        char[] writeChars;
        String writeString;
        String readString;
        StringBuilder expectedString = new StringBuilder();
        Vector<InputStream> inputVector =
            new Vector<InputStream>(maxIterations);
        Vector<String> verifyVector =
            new Vector<String>(maxIterations);
        Random rand = newRandGen();

        for (int i = 0; i < maxIterations; i++) {
            // Randomize length of line to write.
            dataLength = rand.nextInt(2 * BUFFER_SIZE - 1) + 1;
            // Randomize mode to write in.
            if (rand.nextBoolean()) {
                mode = LineRawMode.LINE;
            } else {
                mode = LineRawMode.RAW;
            }
            if (mode == LineRawMode.LINE) {
                // If coming into LINE from RAW, send ENDRAW.
                if (prevMode == LineRawMode.RAW) {
                    byte[] writeBytes = "ENDRAW\n".getBytes("UTF-8");
                    int millisDelay = rand.nextInt(maxDelay);
                    // Add byte stream to input vector.
                    inputVector.addElement(
                        new DelayedEOFByteArrayInputStream(writeBytes,
                                                           millisDelay));
                    // Add expected raw string to verify vector.
                    verifyVector.addElement(expectedString.toString());
                }
                // Randomize line data.
                writeChars = randomLineChars(rand, dataLength);
                // Add expected line string to verify vector (exclude '\n')
                writeString = new String(writeChars);
                verifyVector.addElement(
                    writeString.substring(0, writeChars.length - 1));
                addSplitDelayedStreams(rand, new String(writeChars),
                                       inputVector, maxDelay);
                prevMode = LineRawMode.LINE;
            } else if (mode == LineRawMode.RAW) {
                if (prevMode == LineRawMode.LINE) {
                    expectedString.delete(0, expectedString.length());
                }
                // Randomize raw data.
                writeChars = randomRawChars(rand, dataLength);
                // Update expectedString before raw mode syntax applied.
                writeString = new String(writeChars);
                expectedString.append(writeString);
                writeString = rawSequence(writeString);
                // If coming into RAW mode from LINE mode, send RAW\n as well.
                if (prevMode == LineRawMode.LINE) {
                    writeString = "RAW\n" + writeString;
                }
                addSplitDelayedStreams(rand, writeString,
                                       inputVector, maxDelay);
                prevMode = LineRawMode.RAW;
            }
        }
        // Read out contents and verify that they match the saved Strings.
        r = new LineRawReader(new SequenceInputStream(inputVector.elements()),
            BUFFER_SIZE);
        int j = 1;
        for (Enumeration<String> e = verifyVector.elements();
             e.hasMoreElements();) {
            readString = r.read();
            assertEquals(e.nextElement(), readString);
            j++;
        }
    }

    /**
     * Helper function that takes a String, splits it into two randomly sized
     * Strings, creates a DelayedEOFByteArrayInputStream for each one, and then
     * appends the created streams to the vector of InputStreams.
     *
     * Designed to be used only by randomizedSequenceTest()
     *
     * @param rand random number generator
     * @param writeString String to place into InputStreams
     * @param inputVector vector of InputStreams to append to
     */
    private void addSplitDelayedStreams(
        final Random rand,
        final String writeString,
        final Vector<InputStream> inputVector,
        final int maxDelay) {

        int dataSplit;
        int millisDelay;
        byte[] writeBytes = null;

        // Randomize data split.
        if (writeString.length() != 1) {
            dataSplit = rand.nextInt(writeString.length() - 1);
        } else {
            dataSplit = 0;
        }
        // Set up the first byte stream.
        if (dataSplit > 0) {
            try {
                writeBytes = writeString.substring(0,
                    dataSplit).getBytes("UTF-8");
            } catch (UnsupportedEncodingException e) {
                // Die on UnsupportedEncodingException.
                e.printStackTrace();
                System.exit(1);
            }
            millisDelay = rand.nextInt(maxDelay);
            inputVector.addElement(
                new DelayedEOFByteArrayInputStream(writeBytes,
                                                   millisDelay));
        }
        // Set up the second byte stream.
        if (dataSplit < (writeString.length() - 1)) {
            try {
                writeBytes =
                    writeString.substring(dataSplit,
                        writeString.length()).getBytes("UTF-8");
            } catch (UnsupportedEncodingException e) {
                // Die on UnsupportedEncodingException.
                e.printStackTrace();
                System.exit(1);
            }
            millisDelay = rand.nextInt(maxDelay);
            inputVector.addElement(
                new DelayedEOFByteArrayInputStream(writeBytes,
                                                   millisDelay));
        }
    }
}
