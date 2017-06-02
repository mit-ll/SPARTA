//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-16 14:25:52 -0400 (Tue, 16 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         PublishingBroker unit tests.
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

import edu.mit.ll.spar.ta3.actors.PublishingBroker;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.PipedOutputStream;
import java.io.PipedInputStream;
import java.io.BufferedReader;
import java.io.PipedWriter;
import java.io.PipedReader;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import javax.jms.JMSException;

/**
 * Unit tests for PublishingBroker.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2985 $
 */
public class PublishingBrokerTest extends UnitTester {
    private static final Logger LOGGER = LoggerFactory.getLogger(
      PublishingBrokerTest.class);
    private int portNumber = 61610;
    private PipedOutputStream inputFeeder;
    private PipedInputStream input;
    private PipedWriter output;
    private ExecutorService executor;
    private BufferedReader outputReader;
    private PublishingBroker pub;
    private Future<?> pubStatus;

    /** Gets executed before every @Test method. */
    @Before
    public final void setup() throws Exception {
      inputFeeder = new PipedOutputStream();
      input = new PipedInputStream(inputFeeder);
      output = new PipedWriter();
      executor = Executors.newSingleThreadExecutor();
      outputReader = new BufferedReader(new PipedReader(output));
      pub = new PublishingBroker(new LineRawReader(input, DEFAULT_BUFFER_SIZE),
          output, "localhost", portNumber++,
          "scripts-config/ta3/config/metadata_schema.csv", false, null, null);
      final PublishingBroker finalPub = pub;
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
    }

    /** Gets executed after every @Test method. */
    @After
    public final void teardown() throws Exception {
      assertEquals(outputReader.readLine(), "READY");
      inputFeeder.write("SHUTDOWN\n".getBytes(), 0, "SHUTDOWN\n".length());
      inputFeeder.flush();
      assertEquals(pubStatus.get(), null);
      pub.shutdown();
      executor.shutdown();
    }

    /**
     * Doesn't execute any commands besides SHUTDOWN; just makes sure things
     * work.
     */
    @Test
    public final void basicOperation() throws Exception {
    }

    /** Makes sure standard PUBLISH commands work. */
    @Test
    public final void publishOperation() throws Exception {
      assertEquals(outputReader.readLine(), "READY");
      StringBuilder publishString =
        generatePublishCommand1(pub.getSchemaHandler());
      StringBuilder commandString = new StringBuilder();
      commandString.append("COMMAND 0\n");
      commandString.append(publishString);
      commandString.append("PAYLOAD\nRAW\n1024\n");
      for (int i = 0; i < 1024; i++) {
        commandString.append((char) (i % 128));
      }
      commandString.append("ENDRAW\nENDPAYLOAD\nENDPUBLISH\n");
      commandString.append("ENDCOMMAND\n");
      inputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      inputFeeder.flush();
      assertEquals(outputReader.readLine(), "RESULTS 0");
      assertEquals(outputReader.readLine(), "DONE");
      assertEquals(outputReader.readLine(), "ENDRESULTS");
    }

    /** Makes sure errors are caught if incomplete metadata is sent. */
    @Test
    public final void partialMetadata() throws Exception {
      assertEquals(outputReader.readLine(), "READY");
      StringBuilder commandString = new StringBuilder();
      commandString.append("COMMAND 0\n");
      commandString.append("PUBLISH\nMETADATA\n");
      commandString.append("this,wont,be,enough\n");
      commandString.append("PAYLOAD\nnope, definitely not enough\n");
      commandString.append("ENDPAYLOAD\nENDPUBLISH\n");
      commandString.append("ENDCOMMAND\n");
      inputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      inputFeeder.flush();
      assertEquals(outputReader.readLine(), "RESULTS 0");
      assertEquals(outputReader.readLine(), "FAILED");
      String resultLine = outputReader.readLine();
      while (!resultLine.equals("ENDFAILED")) {
        LOGGER.debug("Received failure message: {}", resultLine);
        resultLine = outputReader.readLine();
      }
      assertEquals(outputReader.readLine(), "ENDRESULTS");
    }

    /** Makes sure errors are caught if invalid types are sent in metadata. */
    @Test
    public final void badMetadata() throws Exception {
      assertEquals(outputReader.readLine(), "READY");
      StringBuilder commandString = new StringBuilder();
      commandString.append("COMMAND 0\n");
      commandString.append("PUBLISH\nMETADATA\n");
      commandString.append("fname,lname,ssn,dob,address,city,state,zip,sex,");
      commandString.append("race,marital_status,school_enrolled,citizenship,");
      commandString.append("NOTANINTEGER,military_service,language,0,0\n");
      commandString.append("PAYLOAD\nnope, definitely not enough\n");
      commandString.append("ENDPAYLOAD\nENDPUBLISH\n");
      commandString.append("ENDCOMMAND\n");
      inputFeeder.write(commandString.toString().getBytes(),
          0, commandString.length());
      inputFeeder.flush();
      assertEquals(outputReader.readLine(), "RESULTS 0");
      assertEquals(outputReader.readLine(), "FAILED");
      String resultLine = outputReader.readLine();
      while (!resultLine.equals("ENDFAILED")) {
        LOGGER.debug("Received failure message: {}", resultLine);
        resultLine = outputReader.readLine();
      }
      assertEquals(outputReader.readLine(), "ENDRESULTS");
    }

    /** Makes sure all root mode commands function properly. */
    @Test
    public final void rootModeOperations() throws Exception {
      assertEquals(outputReader.readLine(), "READY");
      String commandString = "CLEARCACHE\n";
      inputFeeder.write(commandString.getBytes(),
          0, commandString.length());
      inputFeeder.flush();
      assertEquals(outputReader.readLine(), "DONE");
    }
}
