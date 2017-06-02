package edu.mit.ll.spar.ta3.actors.test;

import edu.mit.ll.spar.ta3.actors.SubscribingClient;
import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.util.ArrayList;
import java.util.List;
import java.io.IOException;
import java.io.PipedOutputStream;
import java.io.PipedInputStream;
import java.io.PipedWriter;
import java.io.PipedReader;
import java.io.BufferedReader;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutorService;

import javax.jms.JMSException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import uk.co.flamingpenguin.jewel.cli.ArgumentValidationException;
import uk.co.flamingpenguin.jewel.cli.CliFactory;
import uk.co.flamingpenguin.jewel.cli.Option;

/**
 * Compliment to TestNetworkPublisher. Subscribes to the the broker that sets up
 * and keeps track of how many messages it received. Also track some latency
 * statisitcs (though due to clock skew all we can easily track is the variation
 * in latency).
 */
public final class TestNetworkSubscriber {
    /** logger instance. */
    private static final Logger LOGGER = LoggerFactory.getLogger(
           TestNetworkSubscriber.class);
   private static final int DEFAULT_BUFFER_SIZE = 1024;
    /** Executor wait period (s). */
   private static final int EXECUTOR_WAIT = 10;
    /**
     * Each message of each type is assigned an increasing number. This tracks
     * the last one received so we can be sure we didn't miss any messages.
     */
    private int lastMessageNumberReceived = 0;
    /**
     * List of missing message numbers. Note that this will also contain
     * messages that were received out of order.
     */
    private final List<Integer> missingMessageNumbers =
        new ArrayList<Integer>();
    /** Keep track of stats about the latency of received messaged. */
    /*private ApproxStreamingQuantile latencyQuantiles =
        new ApproxStreamingQuantile();*/
    /** Number of messages received so far. */
    private int numMessagesReceived = 0;
    /** Log status messages with this frequency. */
    static final long LOG_FREQUENCY_MILLIS = 10 * 1000;
    /** The time, in milliseconds from epoch, at which we next need to write a
     * log message. */
    private long nextLogTime;
    private static int pubHistoryLength = 20;
   /**
    * Constructor. Private since this is just a main so the class shouldn't be
    * constructed.
    */
   private TestNetworkSubscriber() {
   }

   // CHECKSTYLE:OFF
   /**
    * Define command line options using JewelCLI.
    */
   public interface CmdOptions {
      /*@Option(shortName = "t", longName = "type",
            description = "Type of message to subscribe to",
            pattern = "[A-Z]")
      String getSubscriptionType();*/

      @Option(shortName = "h",
            description = "Connection address of the broker",
            defaultValue = "localhost")
      String getHost();

      @Option(shortName = "p", defaultValue = "61619",
              description = "Connection port of the broker")
      int getPort();

      @Option(helpRequest = true, description = "Print this message")
      boolean getHelp();
   }
   // CHECKSTYLE:ON

   /**
    * Basically the main method but its not static as we need an instance.
    * @param args the command line arguments.
    * @throws JMSException if anything goes wrong.
    * @throws IOException if anything goes wrong.
    */
   public void run(final String[] args) throws JMSException, IOException {
      CmdOptions options = null;
      try {
         options = CliFactory.parseArguments(CmdOptions.class, args);
      } catch (ArgumentValidationException e) {
         System.out.println(e);
         System.exit(1);
      }

      LOGGER.info("Starting test");
      nextLogTime = System.currentTimeMillis() + LOG_FREQUENCY_MILLIS;

      PipedOutputStream inputFeeder = new PipedOutputStream();
      PipedInputStream input = new PipedInputStream(inputFeeder);
      PipedWriter output = new PipedWriter();
      final BufferedReader outputReader =
        new BufferedReader(new PipedReader(output));
      LOGGER.info("Setting up client...");
      final SubscribingClient client = new SubscribingClient(
            new LineRawReader(input, DEFAULT_BUFFER_SIZE),
            output, options.getHost(), options.getPort(), pubHistoryLength,
            false, null, null);
      LOGGER.info("Client ready to connect...");

      StringBuilder subscribeString = new StringBuilder();
      subscribeString.append("COMMAND 0\nSUBSCRIBE 0\n");
      subscribeString.append("sex = 'Female'\n");
      subscribeString.append("ENDCOMMAND\n");

      ExecutorService executor = Executors.newCachedThreadPool();
      executor.execute(new Runnable() {
        public void run() {
          try {
            //LOGGER.info("Starting client...");
            client.run();
            //LOGGER.info("Started client...");
          } catch (JMSException e) {
            LOGGER.error("JMSException occurred when running subscriber.", e);
            System.exit(1);
          }
        }
      });

      String received = outputReader.readLine();
      assert received.equals("READY") : String.format(
            "Expected READY; received [%s]", received);

      inputFeeder.write(subscribeString.toString().getBytes(),
          0, subscribeString.length());
      inputFeeder.flush();

      String expectedString = "RESULTS 0";
      received = outputReader.readLine();
      assert received.equals(expectedString)
        : String.format("Expected [%s]; received [%s]",
                        expectedString, received);
      expectedString = "DONE";
      received = outputReader.readLine();
      assert received.equals(expectedString)
        : String.format("Expected [%s]; received [%s]",
                        expectedString, received);
      expectedString = "ENDRESULTS";
      received = outputReader.readLine();
      assert received.equals(expectedString)
        : String.format("Expected [%s]; received [%s]",
            expectedString, received);

      while (!client.getEOPStatus()) {
        try {
          LOGGER.info("Subscriber output: {}", outputReader.readLine());
          // TODO(njhwang) Record which #s are missing
          // TODO(njhwang) Figure out a way to sneak in some latency tests
        } catch (IOException e) {
          LOGGER.info("IOException occured when reading subscriber data; "
              + "probably hit EOF.");
          break;
        }
      }

      inputFeeder.write("SHUTDOWN\n".getBytes(), 0, "SHUTDOWN\n".length());
      inputFeeder.flush();
      boolean executorStatus = false;
      try {
        executorStatus =
          executor.awaitTermination(EXECUTOR_WAIT, TimeUnit.SECONDS);
      } catch (InterruptedException e) {
        LOGGER.info("Thread pool was interrupted before it could be"
            + " terminated.");
      }
      if (!executorStatus) {
        executor.shutdownNow();
      }
   }

   /**
    * Main.
    *
    * @param args the command line arguments.
    * @throws Exception if anything goes wrong.
    */
   public static void main(final String[] args) throws Exception {
      TestNetworkSubscriber sub = new TestNetworkSubscriber();
      sub.run(args);
   }
}
