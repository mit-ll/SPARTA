//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Used to benchmark LineRawReader performance.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120727       ni24039         Original Version
// 120803       ni24039         Minor stylistic changes
//*****************************************************************************
package edu.mit.ll.spar.protocol.reader.test;

import static org.junit.Assert.*;
import static edu.mit.ll.spar.protocol.reader.test.LineRawReaderUtils.*;

import edu.mit.ll.spar.protocol.reader.LineRawReader;

import edu.mit.ll.spar.common.UnitTester;
import org.junit.Ignore;
import org.junit.Test;

import java.io.ByteArrayInputStream;

import java.util.Random;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

public class LineRawReaderBenchmarkTest extends UnitTester {
    /** Buffer size to use with LineRawReader. */
    private static final int BUFFER_SIZE = 1024;
    /**
     * Change the variables below to parameterize the test.
     * TODO(njhwang) Use JUnit's Parameterized
     */
    private static final int ITERATIONS = 100000;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(LineRawReaderBenchmarkTest.class);

    // TODO(njhwang) Make this just an executable, not a unit test
    /**
     * Characterizes the average time to process line data of varying size.
     *
     * @throws Exception
     */
    @Test @Ignore
    public final void characterizeLineReadsTest() throws Exception {
    // TODO(njhwang) Benchmarking incomplete, update and incorporate later when
    // benchmarking is more robust, and do something nicer than @Ignore.
        LOGGER.info("Characterizing line reads with buffer size {}B.",
                    BUFFER_SIZE);
        int[] testLengths = new int[]{10, 50, 100, 500, 1000, 5000, 10000,
                                      50000, 100000, 500000, 1000000};

        LineRawReader r;
        ByteArrayInputStream input;
        String readString;
        String writeString;
        long startTime;
        long[] results = new long[ITERATIONS];
        double meanTime;
        double stdTime;
        char[] writeChars;
        Random rand = newRandGen();

        for (int i = 0; i < testLengths.length; i++) {
            for (int j = 0; j < ITERATIONS; j++) {
                writeChars = randomLineChars(rand, testLengths[i]);
                writeString = new String(writeChars);
                input = new ByteArrayInputStream(writeString.getBytes("UTF-8"));
                r = new LineRawReader(input, BUFFER_SIZE);
                startTime = System.nanoTime();
                readString = r.read();
                results[j] = System.nanoTime() - startTime;
                assertEquals(writeString.substring(0, testLengths[i] - 1),
                             readString);
            }
            LOGGER.info("Completed {} reads of {}B.",
                        ITERATIONS, testLengths[i]);
            meanTime = mean(results) / 1000.0d;
            stdTime = std(results, meanTime) / 1000.0d;
            LOGGER.info("Mean read time (us): {} +/- {}", meanTime, stdTime);
        }
    }

    /**
     * Characterizes the average time to process raw data of varying size.
     *
     * @throws Exception
     */
    @Test @Ignore
    public final void characterizeRawReadsTest() throws Exception {
        LOGGER.info("Characterizing line reads with buffer size {}B.",
                    BUFFER_SIZE);
        int[] testLengths = new int[]{10, 50, 100, 500, 1000, 5000, 10000,
                                      50000, 100000, 500000, 1000000};

        LineRawReader r;
        ByteArrayInputStream input;
        String readString;
        String writeString;
        String fullString;
        long startTime;
        long[] results = new long[ITERATIONS];
        double meanTime;
        double stdTime;
        char[] writeChars;
        Random rand = newRandGen();

        for (int i = 0; i < testLengths.length; i++) {
            for (int j = 0; j < ITERATIONS; j++) {
                writeChars = randomRawChars(rand, testLengths[i]);
                writeString = new String(writeChars);
                fullString = rawModeWrapper(rawSequence(writeString));
                input = new ByteArrayInputStream(fullString.getBytes("UTF-8"));
                r = new LineRawReader(input, BUFFER_SIZE);
                startTime = System.nanoTime();
                readString = r.read();
                results[j] = (System.nanoTime() - startTime);
                assertEquals(writeString, readString);
            }
            LOGGER.info("Completed {} reads of {}B.",
                        ITERATIONS, testLengths[i]);
            meanTime = mean(results) / 1000.0d;
            stdTime = std(results, meanTime) / 1000.0d;
            LOGGER.info("Mean read time (us): {} +/- {}", meanTime, stdTime);
        }
    }

    // TODO(njhwang) Write unit tests for these stats functions.
    /**
     * Calculate mean of an array of longs.
     * NOTE: this is not a numerically stable method for very large arrays. This
     * should not be refactored and used elsewhere; for large scale statistical
     * functions, consider using the Apache Commons library (but note that the
     * library may not be particularly well-coded or maintained).
     *
     * @param data array of longs (cannot be null, and must have at least one
     *             item)
     * @return mean of array
     */
    private double mean(final long[] data) {
        assert data != null : "Cannot calculate mean for null array.";
        assert data.length > 0 : "Cannot calculate mean for empty array.";
        double result = 0.0d;
        for (int i = 0; i < data.length; i++) {
            result += (double) data[i];
        }
        return result / (double) data.length;
    }

    /**
     * Calculate standard deviation of an array of longs.
     * See comments in mean().
     *
     * @param data array of longs (cannot be null, and must have at least one
     *             item)
     * @return standard deviation of array
     */
    private double std(final long[] data) {
        assert data != null : "Cannot calculate std for null array.";
        assert data.length > 0 : "Cannot calculate std for empty array.";
        return std(data, mean(data));
    }

    /**
     * Calculate standard deviation of an array of longs.
     * See comments in mean().
     *
     * @param data array of longs (cannot be null, and must have at least one
     *             item)
     * @param dataMean mean of array
     * @return standard deviation of array
     */
    private double std(final long[] data, final double dataMean) {
        assert data != null : "Cannot calculate std for null array.";
        assert data.length > 0 : "Cannot calculate std for empty array.";
        double result = 0.0d;
        for (int i = 0; i < data.length; i++) {
            result += Math.pow(
                (double) data[i] - dataMean, 2.0d);
        }
        result /= (double) (data.length - 1);
        return Math.sqrt(result);
    }
}
