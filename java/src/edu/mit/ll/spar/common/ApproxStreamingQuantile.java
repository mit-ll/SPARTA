package edu.mit.ll.spar.common;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * A lame (but quick to implement) class for tracking approximate quantiles.
 * There are much better algorithms for this but I coudln't find a good, free
 * library that implements them and it'd take a lot of effort to do it "right".
 * Instead this buffers up the first N examples it sees to determine the range
 * of values. It then computes 100 exact quantiles from that buffer and uses
 * these to define bucket boundaries. All futher observations are simply thrown
 * into the relevant bucket and approximate quantiles are computed from that.
 * This should work well as long as the distribution doesn't change dramatically
 * after the buffer period.
 *
 * Note that this container is thread safe.
 *
 * TODO(odain): I tried to make this generic so it took any <T extends Number>
 * but ran into issues (e.g. you can't call T.MAX_VALUE because Number
 * doesn't have that member even though all its sub-types do). Might be worth
 * genericizing if I can figure out a sane way to do it.
 */
public class ApproxStreamingQuantile {
    /** The number of items we'll buffer before constructing buckets. */
    private static final int INIT_BUFFER_SIZE = 1000;
    /** The number of buckets we'll create. */
    private static final int NUM_BUCKETS = 100;

    /** Total number of items added so far. */
    private int totalAdded = 0;
    /** Buffer which holds the 1st INIT_BUFFER_SIZE items observerd. Once that
     * many items have arrived this will be used to construct bucket boundaries
     * and then freed. */
    private List<Long> initBuffer;
    /**
     * An array such that bucket[i] contains the number of times values in the
     * range [bucketBoundaries[i], bucketBoundaries[i+1]) (note inclusive left
     * end and exclusive right end) have been observed. Thus bucketBoundaries[0]
     * == Long.MIN_VALUE. Notionally bucketBoundaries[NUM_BUCKETS + 1] =
     * Long.MAX_VALUE but we don't explicitly store that.
     */
    private List<Long> bucketBoundaries;
    /**
     * The buckets. This is constructed only after INIT_BUFFER_SIZE values have
     * been observed. From that point on this tracks how many times values in a
     * given range were observed. See bucketBoundaries for details.
     */
    private List<Long> buckets;
    /** The largest single value observed. */
    private long minValue = Long.MAX_VALUE;
    /** The smallest value observed. */
    private long maxValue = Long.MIN_VALUE;

    /** Constructor. */
    public ApproxStreamingQuantile() {
        initBuffer = new ArrayList<Long>(INIT_BUFFER_SIZE);
    }

    /**
     * Add item to set of values over which the quantiles are computed.
     * @param item the item to add
     */
    public final synchronized void add(final long item) {
        maxValue = Math.max(maxValue, item);
        minValue = Math.min(minValue, item);

        if (totalAdded < INIT_BUFFER_SIZE) {
            initBuffer.add(item);
        } else if (totalAdded == INIT_BUFFER_SIZE) {
            constructBuckets();
        } else {
            addToBucket(item);
        }
        ++totalAdded;
    }

    /**
     * Called once INIT_BUFFER_SIZE items have been seen. When called bucket
     * boundaries are computed so as to give an accurate estimate for the
     * quantiles. The data from initBuffer is then copied into these buckets and
     * initBuffer is freed.
     */
    private synchronized void constructBuckets() {
        assert (INIT_BUFFER_SIZE % NUM_BUCKETS) == 0;
        // We know (see above assert) that the initial buffer is an integer
        // multiple of the number of number of buckets we want to create. We can
        // therefore simply sort the initial list and then look at the value at
        // each of these multiples.
        Collections.sort(initBuffer);
        int stride = INIT_BUFFER_SIZE / NUM_BUCKETS;
        bucketBoundaries = new ArrayList<Long>(NUM_BUCKETS);
        // All buckets initially contain the same number of items ==
        // INIT_BUFFER_SIZE / NUM_BUCKES == stride.
        buckets = new ArrayList<Long>(
                Collections.nCopies(NUM_BUCKETS, new Long(stride)));
        bucketBoundaries.add(Long.MIN_VALUE);
        for (int i = stride; i < INIT_BUFFER_SIZE; i += stride) {
            bucketBoundaries.add(initBuffer.get(i));
        }
        assert bucketBoundaries.size() == NUM_BUCKETS;
        initBuffer = null;
    }

    /**
     * Add a new data item to the buckets.
     * @param item the item to add
     */
    private synchronized void addToBucket(final long item) {
        assert initBuffer == null;
        assert bucketBoundaries != null;
        assert buckets != null;

        // Find the index into the buckets array where this value belongs.
        int idx = Collections.binarySearch(bucketBoundaries, item);
        if (idx < 0) {
            // Due to weird way binarySearch is defined...
            idx = -1 * idx - 2;
            assert idx >= 0;
        }
        buckets.set(idx, buckets.get(idx) + 1);
    }

    /**
     * @param quantile the desired quantile expressed as a percentage (e.g.
     * between 0 and 100) rather than a fraction.
     * @return the smallest (approximate) value such that quantile% of the data
     * is &lt;= the returned value.
     */
    public final synchronized long getQuantile(final int quantile) {
        final int MAX_QUANTILE = 100;
        final int MIN_QUANTILE = 0;
        assert quantile >= MIN_QUANTILE;
        assert quantile <= MAX_QUANTILE;

        if (quantile == MIN_QUANTILE) {
            return minValue;
        }

        if (quantile == MAX_QUANTILE) {
            return maxValue;
        }

        // Note that we're not interpolating between adjacent values to get an
        // absolutely correct answer. For example, given {1, 2, 3, 4} the medain
        // (quantile == 50) should be 2.5 but this will instead return 3.
        int dataCount = Math.round(
          ((float) ((totalAdded - 1) * quantile)) / ((float) MAX_QUANTILE));
        assert dataCount >= 0;
        assert dataCount < totalAdded;
        if (totalAdded <= INIT_BUFFER_SIZE) {
            assert initBuffer != null;
            assert buckets == null;
            Collections.sort(initBuffer);
            return initBuffer.get(dataCount);
        } else {
            // This could be optimized so it's not linear time but this is
            // linear in NUM_BUCKETS which is fairly small so its not clear if
            // its worth it.
            int soFar = 0;
            for (int i = 0; i < NUM_BUCKETS; ++i) {
                soFar += buckets.get(i);
                if (soFar >= dataCount) {
                    return bucketBoundaries.get(i);
                }
            }
        }
        // We should never get here!!
        throw new RuntimeException("This should be impossible!");
    }
}
