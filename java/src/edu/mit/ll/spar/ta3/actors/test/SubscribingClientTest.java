//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-16 14:25:52 -0400 (Tue, 16 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         SubscribingClient unit tests.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.actors.test;

import static edu.mit.ll.spar.ta3.actors.test.ActorTestUtils.*;
import edu.mit.ll.spar.common.UnitTester;
import static org.junit.Assert.*;
import org.junit.Before;
import org.junit.After;
import org.junit.Test;

import edu.mit.ll.spar.ta3.actors.SubscribingClient;
import edu.mit.ll.spar.ta3.actors.PublishingBroker;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.BufferedReader;
import java.io.PipedOutputStream;
import java.io.PipedInputStream;
import java.io.PipedWriter;
import java.io.PipedReader;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import javax.jms.JMSException;
import java.io.IOException;

// TODO(njhwang) while things generally work, there seem to be some race
// conditions that make this fail every once in awhile
public class SubscribingClientTest extends UnitTester {
    private static final Logger LOGGER = LoggerFactory.getLogger(
      SubscribingClientTest.class);
    private static int portNumber = 61620;
    private static int pubHistoryLength = 20;
    private PipedOutputStream pubInputFeeder;
    private PipedInputStream pubInput;
    private PipedWriter pubOutput;
    private BufferedReader pubOutputReader;
    private PipedOutputStream subInputFeeder;
    private PipedInputStream subInput;
    private PipedWriter subOutput;
    private BufferedReader subOutputReader;
    private ExecutorService executor;
    private PublishingBroker pub;
    private SubscribingClient sub;
    private Future<?> pubStatus;
    private Future<?> subStatus;
    private int pubCommandId;
    private int subCommandId;

    /** Executed before every @Test method. */
    @Before
    public synchronized final void setup() throws Exception {
      LOGGER.info("\n\n\nSETTING UP WITH PORT " + portNumber);
      pubInputFeeder = new PipedOutputStream();
      pubInput = new PipedInputStream(pubInputFeeder);
      pubOutput = new PipedWriter();
      pubOutputReader = new BufferedReader(new PipedReader(pubOutput));
      subInputFeeder = new PipedOutputStream();
      subInput = new PipedInputStream(subInputFeeder);
      subOutput = new PipedWriter();
      subOutputReader = new BufferedReader(new PipedReader(subOutput));
      executor = Executors.newCachedThreadPool();
      pub = new PublishingBroker(
          new LineRawReader(pubInput, DEFAULT_BUFFER_SIZE),
          pubOutput, "localhost", portNumber,
          "scripts-config/ta3/config/metadata_schema.csv", false, null, null);
      sub = new SubscribingClient(
          new LineRawReader(subInput, DEFAULT_BUFFER_SIZE),
          subOutput, "localhost", portNumber++, pubHistoryLength, false, null,
          null);
      LOGGER.info("INCREMENTED PORT TO " + portNumber);
      final PublishingBroker finalPub = pub;
      final SubscribingClient finalSub = sub;
      pubStatus = executor.submit(new Runnable() {
        public void run() {
          try {
            finalPub.run();
          } catch (JMSException e) {
            LOGGER.error("JMSException occurred when running publisher.");
            System.exit(1);
          }
        }
      });
      subStatus = executor.submit(new Runnable() {
        public void run() {
          try {
            finalSub.run();
          } catch (JMSException e) {
            LOGGER.error("JMSException occurred when running publisher.");
            System.exit(1);
          }
        }
      });
      pubCommandId = 0;
      subCommandId = 0;
    }

    /** Executed after every @Test method. */
    @After
    public synchronized final void teardown() throws Exception {
      LOGGER.info("SHUTTING DOWN");
      assertEquals(subOutputReader.readLine(), "READY");
      subInputFeeder.write("SHUTDOWN\n".getBytes(), 0, "SHUTDOWN\n".length());
      subInputFeeder.flush();
      assertEquals(pubOutputReader.readLine(), "READY");
      pubInputFeeder.write("SHUTDOWN\n".getBytes(), 0, "SHUTDOWN\n".length());
      pubInputFeeder.flush();
      assertEquals(pubStatus.get(), null);
      assertEquals(subStatus.get(), null);
      final SubscribingClient finalSub = sub;
      subStatus = executor.submit(new Runnable() {
        public void run() {
          try {
            finalSub.shutdown();
          } catch (JMSException e) {
            LOGGER.error("JMSException occurred when shutting down sub.", e);
          } catch (IOException e) {
            LOGGER.error("IOException occurred when shutting down sub.", e);
          }
        }
      });
      final PublishingBroker finalPub = pub;
      pubStatus = executor.submit(new Runnable() {
        public void run() {
          try {
            finalPub.shutdown();
          } catch (Exception e) {
            LOGGER.error("Exception occurred when shutting down pub.", e);
          }
        }
      });
      assertEquals(subStatus.get(), null);
      assertEquals(pubStatus.get(), null);
      executor.shutdown();
      LOGGER.info("TEST COMPLETE\n\n\n");
    }

    /**
     * Doesn't actually do anything except make sure nothing crashes.
     *
     * @throws Exception if anything goes wrong.
     */
    @Test
    public final void basicOperation() throws Exception {
    }

    /** Test standard SUBSCRIBE and UNSUBSCRIBE operations. */
    @Test
    public final void nominalOperations() throws Exception {
      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'Chalupa Batman'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      unsubscribe(true);
    }

    /** Tests subscribing to an ID that was already subscribed to. */
    @Test
    public final void badSubscribe() throws Exception {
      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'Chalupa Batman'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("lname = 'McAllister'", false);
    }

    /** Tests unsubscribing an ID that doesn't exist yet. */
    @Test
    public final void badUnsubscribe() throws Exception {
      assertEquals(subOutputReader.readLine(), "READY");
      unsubscribe(false);
    }

    /** Performs a SUBSCRIBE command and verifies results. */
    private void subscribe(final String subscription, final boolean pass)
      throws IOException {
      StringBuilder commandString = new StringBuilder();
      commandString.append(String.format("COMMAND %d\n", subCommandId));
      commandString.append("SUBSCRIBE 0\n");
      commandString.append(subscription + "\n");
      commandString.append("ENDCOMMAND\n");
      subInputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      subInputFeeder.flush();
      assertEquals(subOutputReader.readLine(),
                   String.format("RESULTS %d", subCommandId++));
      if (!pass) {
        assertEquals(subOutputReader.readLine(), "FAILED");
        String resultLine = subOutputReader.readLine();
        while (!resultLine.equals("ENDFAILED")) {
          LOGGER.debug("Received failure message: {}", resultLine);
          resultLine = subOutputReader.readLine();
        }
      } else {
        String resultLine = subOutputReader.readLine();
        if (!resultLine.equals("DONE")) {
          LOGGER.info("ERROR: did not receive positive results.");
          LOGGER.info(resultLine);
          while (!resultLine.equals("ENDFAILED")) {
            LOGGER.info(resultLine);
            resultLine = subOutputReader.readLine();
          }
          assertEquals(resultLine, "Fail this test.");
        }
      }
      assertEquals(subOutputReader.readLine(), "ENDRESULTS");
    }

    /** Performs a UNSUBSCRIBE command and verifies results. */
    private void unsubscribe(final boolean pass) throws IOException {
      StringBuilder commandString = new StringBuilder();
      commandString.append(String.format("COMMAND %d\n", subCommandId));
      commandString.append("UNSUBSCRIBE 0\n");
      commandString.append("ENDCOMMAND\n");
      subInputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      subInputFeeder.flush();
      assertEquals(subOutputReader.readLine(),
                   String.format("RESULTS %d", subCommandId++));
      if (!pass) {
        assertEquals(subOutputReader.readLine(), "FAILED");
        String resultLine = subOutputReader.readLine();
        while (!resultLine.equals("ENDFAILED")) {
          LOGGER.debug("Received failure message: {}", resultLine);
          resultLine = subOutputReader.readLine();
        }
      } else {
        assertEquals(subOutputReader.readLine(), "DONE");
      }
      assertEquals(subOutputReader.readLine(), "ENDRESULTS");
    }

    /** Performs a PUBLISH command and verifies results. */
    private void publish(final boolean match, final boolean negated)
      throws IOException {
      StringBuilder commandString = new StringBuilder();
      commandString.append(String.format("COMMAND %d\n", pubCommandId));
      if (negated && match) {
        commandString.append(generatePublishCommand2(pub.getSchemaHandler()));
      } else if (!negated && match) {
        commandString.append(generatePublishCommand1(pub.getSchemaHandler()));
      } else if (negated && !match) {
        commandString.append(generatePublishCommand1(pub.getSchemaHandler()));
      } else {
        commandString.append(generatePublishCommand2(pub.getSchemaHandler()));
      }
      if (match) {
        commandString.append("PAYLOAD\nshould match\n");
      } else {
        commandString.append("PAYLOAD\nshouldn't match\n");
      }
      commandString.append("ENDPAYLOAD\nENDPUBLISH\n");
      commandString.append("ENDCOMMAND\n");
      pubInputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      pubInputFeeder.flush();
      assertEquals(pubOutputReader.readLine(),
                   String.format("RESULTS %d", pubCommandId++));
      assertEquals(pubOutputReader.readLine(), "DONE");
      assertEquals(pubOutputReader.readLine(), "ENDRESULTS");
      if (match) {
        // TODO(njhwang) careful here...do something more robust than this
        // magic number
        for (int i = 0; i < 3; i++) {
          assertEquals(subOutputReader.readLine(), "PUBLICATION");
          assertEquals(subOutputReader.readLine(), "PAYLOAD");
          assertEquals(subOutputReader.readLine(), "RAW");
          assertEquals(subOutputReader.readLine(), "12");
          assertEquals(subOutputReader.readLine(), "should matchENDRAW");
          assertEquals(subOutputReader.readLine(), "ENDPAYLOAD");
          assertEquals(subOutputReader.readLine(), "ENDPUBLICATION");
        }
      }
    }

    /** Tests subscription filters of all currently supported types. */
    @Test
    public final void normalSubscriptions() throws Exception {
      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'aaaaaaaaaaa'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("sex = 'Female'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("weeks_worked_last_year = 52", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("NOT (fname = 'aaaaaaaaaaa')", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("NOT (sex = 'Female')", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("NOT (weeks_worked_last_year = 52)", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname <> 'aaaaaaaaaaa'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("sex <> 'Female'", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("weeks_worked_last_year <> 52", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, true);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, true);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'aaaaaaaaaaa' AND sex = 'Female' AND "
          + "weeks_worked_last_year = 52", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'aaaaaaaaaaa' OR sex = 'Female' OR "
          + "weeks_worked_last_year = 52", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'aaaaaaaaaaa' OR (sex = 'Female' AND "
          + "NOT (weeks_worked_last_year = 52))", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);

      assertEquals(subOutputReader.readLine(), "READY");
      subscribe("fname = 'aaaaaaaaaaa' OR (sex = 'Female' AND "
          + "weeks_worked_last_year <> 52)", true);
      assertEquals(subOutputReader.readLine(), "READY");
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(false, false);
      assertEquals(pubOutputReader.readLine(), "READY");
      publish(true, false);
      unsubscribe(true);
    }

    /** Tests root mode command handling. */
    @Test
    public final void rootModeOperations() throws Exception {
      assertEquals(subOutputReader.readLine(), "READY");
      String commandString = "CLEARCACHE\n";
      subInputFeeder.write(commandString.getBytes(),
          0, commandString.length());
      subInputFeeder.flush();
      assertEquals(subOutputReader.readLine(), "DONE");
    }
}
