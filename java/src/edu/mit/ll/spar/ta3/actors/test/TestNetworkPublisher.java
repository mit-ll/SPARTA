package edu.mit.ll.spar.ta3.actors.test;

// CHECKSTYLE:OFF
import static edu.mit.ll.spar.ta3.actors.test.ActorTestUtils.*;
// CHECKSTYLE:ON

import edu.mit.ll.spar.ta3.actors.PublishingBroker;
import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.PipedOutputStream;
import java.io.PipedInputStream;
import java.io.PipedWriter;
import java.io.PipedReader;
import java.io.BufferedReader;

import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

import javax.jms.JMSException;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import uk.co.flamingpenguin.jewel.cli.ArgumentValidationException;
import uk.co.flamingpenguin.jewel.cli.CliFactory;
import uk.co.flamingpenguin.jewel.cli.Option;

/**
 * This is just a main method that sends messages as fast as it can for
 * testDurationMillis millseconds.  All messages have a "type" property that is
 * set to either "A", "B", etc. The --num_types flag determines how many
 * different types of messages are sent.  For each message type the message is
 * simple text containing a integer. The first message of type X is "1", the
 * second of type X is "2", etc. so that any client subscribing to a single type
 * of message should see monotonically increasing integer values without any
 * "gaps". There is also a property indicating the timestamp in milliseconds
 * from epoch at which the message was sent. This allows crude (crude due to
 * clock skew) tracking of latency. This keeps track of how many
 * messages of each type have been sent so we can make sure all sent messages
 * were received by the subscribers.
 */
public final class TestNetworkPublisher {
    /** Publisher wait period (ms). */
   private static final int PUBLISHER_WAIT = 5000;
    /** Executor wait period (s). */
   private static final int EXECUTOR_WAIT = 10;
    /** For log messages. */
   private static final Logger LOGGER = LoggerFactory.getLogger(
           TestNetworkPublisher.class);
   private static final int DEFAULT_BUFFER_SIZE = 1024;
   /**
    * This class is just a main. Making a private constructor so users can't
    * construct an instance of the class.
    */
   private TestNetworkPublisher() {
   }

   // CHECKSTYLE:OFF
   /**
    * Defines command line options using JewelCLI.
    */
   public interface CmdOptions {
      /*@Option(shortName = "w", longName = "wait", defaultValue = "0",
            description = "Don't start publishing until "
            + "this many clients have connected")
      int getWaitForNumClients();*/

      /*@Option(shortName = "n", longName = "num_types",
              description = "Send this many types of messages.")
      int getNumMessageTypes();*/

      @Option(shortName = "h", defaultValue = "localhost",
              description = "Connection address to set up for subscribers")
      String getHost();

      @Option(shortName = "f", defaultValue = "metadata_schema.csv",
              description = "Metadata schema configuration file name")
      String getFilename();

      @Option(shortName = "p", defaultValue = "61619",
              description = "Port to set up for subscribers")
      int getPort();

      @Option(shortName = "d", defaultValue = "30",
              description = "Number of seconds to test for")
      int getDuration();

      @Option(helpRequest = true, description = "Print this help message")
      boolean getHelp();
   }
   // CHECKSTYLE:ON

   /**
    * main. See comments on the class.
    * @param args The command line arguments
    * @throws Exception if anything goes wrong
    */
   public static void main(final String[] args) throws Exception {
      CmdOptions options = null;
      try {
         options = CliFactory.parseArguments(CmdOptions.class, args);
      } catch (ArgumentValidationException e) {
         System.out.println(e);
         System.exit(1);
      }
      /*final int numCharsInAlphabet = 26;
      if (options.getNumMessageTypes() < 1
              || options.getNumMessageTypes() > numCharsInAlphabet) {
          System.out.print("--num_types must be in the range [1, 26]");
          System.exit(1);
      }*/

      // Run test for for this long.
      //final long testDurationMillis = 24 * 60 * 60 * 1000;
      final long testDurationMillis = options.getDuration() * 1000;
      // Log an update message this frequently.
      //final long logFrequencyMillis = 30 * 1000;
      final long logFrequencyMillis = 10 * 1000;
      PipedOutputStream inputFeeder = new PipedOutputStream();
      PipedInputStream input = new PipedInputStream(inputFeeder);
      PipedWriter output = new PipedWriter();
      final BufferedReader outputReader =
        new BufferedReader(new PipedReader(output));
      final PublishingBroker pub = new PublishingBroker(
              new LineRawReader(input, DEFAULT_BUFFER_SIZE), output,
              options.getHost(), options.getPort(), options.getFilename(),
              false, null, null);


      StringBuilder publishString =
        generatePublishCommand1(pub.getSchemaHandler());
      /*publishString.append("\nPAYLOAD\n");
      for (int i = 0; i < 1024; i++) {
        publishString.append("a");
      }
      publishString.append("\nENDPAYLOAD\nENDPUBLISH\n");*/
      ExecutorService executor = Executors.newCachedThreadPool();
      executor.execute(new Runnable() {
        public void run() {
          try {
            pub.run();
          } catch (JMSException e) {
            LOGGER.error("JMSException occurred when running publisher.");
            System.exit(1);
          }
        }
      });

      /*final Map<Character, Integer> messageTypesSent =
          new TreeMap<Character, Integer>();
      for (char type = 'A'; type - 'A' < options.getNumMessageTypes(); ++type) {
          messageTypesSent.put(type, 0);
      }*/

      //final Random rng = newRandGen();

      // Wait a bit for a subscriber to get set up its subscription so no
      // messages will be missed
      Thread.sleep(PUBLISHER_WAIT);
      final long startTime = System.currentTimeMillis();
      long curTime = startTime;
      long nextLogTime = startTime + logFrequencyMillis;
      int numMessages = 0;
      LOGGER.info("Beginning test...");
      while ((curTime - startTime) < testDurationMillis) {
         /*char typeToGenerate =
             (char) ('A' + rng.nextInt(options.getNumMessageTypes()));
         int numSent = messageTypesSent.get(typeToGenerate);
         ++numSent;
         messageTypesSent.put(typeToGenerate, numSent);
         TextMessage msg = pubBroker.getTextMessage(String.valueOf(numSent));
         msg.setStringProperty("type", String.valueOf(typeToGenerate));*/
         //LOGGER.info("Waiting for READY...");
         String received = outputReader.readLine();
         assert received.equals("READY") : String.format(
               "Expected READY; received [%s]", received);
         StringBuilder commandString = new StringBuilder();
         commandString.append("COMMAND ");
         commandString.append(numMessages);
         commandString.append("\n");
         commandString.append(publishString);
         commandString.append("PAYLOAD\n");
         /*for (int i = 0; i < 1024; i++) {
           publishString.append("a");
         }*/
         commandString.append(numMessages);
         commandString.append("\nENDPAYLOAD\nENDPUBLISH\n");
         commandString.append("ENDCOMMAND\n");
         //LOGGER.info("Writing command...");
         //LOGGER.info("Publisher input has {} bytes available for reading",
         //    input.available());
         inputFeeder.write(commandString.toString().getBytes(),
             0, commandString.length());
         inputFeeder.flush();
         //LOGGER.info("Wrote command {}", numMessages);
         curTime = System.currentTimeMillis();
         // Messages don't have a long property and this won't fit in an int so
         // we use a double.
         //msg.setDoubleProperty("time command sent", curTime);
         //pubBroker.produce(msg);

         if (curTime >= nextLogTime) {
            nextLogTime = curTime + logFrequencyMillis;
            logMessageCounts(numMessages, curTime - startTime);
         }
         String expectedString = "RESULTS " + numMessages;
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

         numMessages++;
      }
      LOGGER.info("Test complete!");
      curTime = System.currentTimeMillis();
      logMessageCounts(numMessages, curTime - startTime);

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
    * Writes log message about the number of messages of each type sent.
    *
    * @param numMessages int
    * @param elapsedMillis long
    */
   private static void logMessageCounts(
           final int numMessages, final long elapsedMillis) {
        LOGGER.info("{} messages sent in {} milliseconds",
                    numMessages, elapsedMillis);
        final double MILLIS_PER_SECOND = 1000;
        LOGGER.info("{} messages/second",
                ((double) numMessages) / ((double) elapsedMillis)
                * MILLIS_PER_SECOND);
   }
}

