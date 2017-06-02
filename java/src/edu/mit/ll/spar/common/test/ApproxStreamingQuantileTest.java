package edu.mit.ll.spar.common.test;

import edu.mit.ll.spar.common.ApproxStreamingQuantile;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

import static org.junit.Assert.*;
import org.junit.Test;

// TODO(njhwang) investigate intermittend unit test failure...in testBig, 47 not
// within 2 of 49?
public class ApproxStreamingQuantileTest {
    /**
     * Test over a small enough # of values that we know that everything is
     * coming from the in-memory buffer.
     */
    @Test
    public final void testSmall() {
        ApproxStreamingQuantile aq = new ApproxStreamingQuantile();
        aq.add(10);
        aq.add(1);
        aq.add(5);
        assertEquals(1, aq.getQuantile(0));
        assertEquals(5, aq.getQuantile(50));
        assertEquals(10, aq.getQuantile(100));

        aq.add(7);
        assertEquals(1, aq.getQuantile(0));
        assertEquals(5, aq.getQuantile(25));
        assertEquals(7, aq.getQuantile(75));
        assertEquals(10, aq.getQuantile(100));

        aq.add(20);
        assertEquals(1, aq.getQuantile(0));
        assertEquals(20, aq.getQuantile(100));
        assertEquals(7, aq.getQuantile(50));

        aq.add(-1);
        aq.add(-2);
        assertEquals(-2, aq.getQuantile(0));
        assertEquals(5, aq.getQuantile(50));
        assertEquals(20, aq.getQuantile(100));

        aq.add(100);
        assertEquals(1, aq.getQuantile(25));
        assertEquals(10, aq.getQuantile(75));
    }

    @Test
    public final void testBig() {
        List<Long> allValues = new ArrayList<Long>();
        ApproxStreamingQuantile aq = new ApproxStreamingQuantile();
        // Generate 10000 random values uniformly distributed in [0, 100].
        // The resulting quantiles should be roughly as expected.
        Random rng = new Random();
        final int TEST_SIZE = 40000;
        for (int i = 0; i < TEST_SIZE; ++i) {
            // 101 here because nextInt a value in [0, n)
            long val = rng.nextInt(101);
            aq.add(val);
            allValues.add(val);
        }
        Collections.sort(allValues);
        assertEquals(allValues.get(0).longValue(), aq.getQuantile(0));
        assertEquals(allValues.get(TEST_SIZE - 1).longValue(),
                aq.getQuantile(100));
        assertClose(allValues.get(TEST_SIZE / 2).longValue(),
                aq.getQuantile(50), 2);
        assertClose(allValues.get(TEST_SIZE / 4).longValue(),
                aq.getQuantile(25), 2);
        assertClose(allValues.get(3 * TEST_SIZE / 4).longValue(),
                aq.getQuantile(75), 2);
        // 25th percentile should be around 50, and the median should be around
        // 62.5.
        for (int i = 0; i < TEST_SIZE; ++i) {
            // 101 here because nextInt a value in [0, n)
            long val = 50 + rng.nextInt(51);
            aq.add(val);
            allValues.add(val);
        }
        Collections.sort(allValues);
        assertClose(allValues.get(2 * TEST_SIZE / 4).longValue(),
                aq.getQuantile(25), 2);
        assertClose(allValues.get(TEST_SIZE).longValue(),
                aq.getQuantile(50), 2);
        assertClose(allValues.get(3 * 2 * TEST_SIZE / 4).longValue(),
                aq.getQuantile(75), 2);
    }

    private void assertClose(final float expected, final float actual,
            final float tolerance) {
        String msg = String.valueOf(actual) + " is not within " + tolerance
            + " units of expected value " + expected;
        assertTrue(msg, actual > expected - tolerance);
        assertTrue(msg, actual < expected + tolerance);
    }
}
