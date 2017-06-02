//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         SubcommandHandlerTest; tests SubcommandHandler
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120811       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers.test;

import static org.junit.Assert.*;

import edu.mit.ll.spar.common.UnitTester;
import org.junit.Test;

import edu.mit.ll.spar.protocol.handlers.LineRawHandlerFactory;
import edu.mit.ll.spar.protocol.handlers.SubcommandHandler;

import edu.mit.ll.spar.common.SerialExecutor;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import edu.mit.ll.spar.common.UnitTester;
import java.io.ByteArrayInputStream;
import java.io.CharArrayWriter;
import java.io.Writer;

import java.util.HashMap;
import java.util.Random;
import java.util.Map;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Defines JUnit unit tests for SubcommandHandler.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see     SubcommandHandler
 * @see     UnitTester
 */
public class SubcommandHandlerTest extends UnitTester {
    /** Number of iterations to repeat commands. */
    private static final int ITERATIONS = 10;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(SubcommandHandlerTest.class);

    /**
     * Tests nominal use of SubcommandHandler.
     * Test creation of handler on first call, as well as factory's
     * ability to reuse an instance upon a subsequent calls.
     *
     * Tests nominal use of:
     * - SerialExecutor
     * - verifyExpectedInput()
     * - handler that takes no parsed arguments
     * - writeResults()
     *
     * @throws Exception
     */
    @Test public final void singleFactoryTest() throws Exception {
        SerialExecutor executor = new SerialExecutor();
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input and expected output data.
        StringBuilder writeString = new StringBuilder();
        StringBuilder expectedString = new StringBuilder();
        for (int i = 0; i < ITERATIONS; i++) {
            writeString.append(CountdownHandler.countdownString(i));
            // Note that normally this would have already parsed COMMAND and
            // COUNTDOWN tokens, so they are therefore not written here.
            writeString.append("ENDCOUNTDOWN\nENDCOMMAND\n");
            expectedString.append(
                String.format("RESULTS %d\nDONE\nENDRESULTS\n", i));
        }
        // Setting up input.
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.toString().getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory.
        LineRawHandlerFactory factory =
          new LineRawHandlerFactory(new CountdownHandler(r, w));
        // Setting up and executing handler.
        SubcommandHandler h = null;
        for (int i = 0; i < ITERATIONS; i++) {
            h = (SubcommandHandler) factory.getHandler();
            h.parseAndExecute(i, null, executor);
        }
        // Verify output.
        assertEquals(expectedString.toString(), w.toString());
    }

    /**
     * Tests that verifyExpectedInput throws ProtocolException and that
     * writeResults() properly processes negative results. Note that the
     * ProtocolException is caught within CountdownHandler.
     *
     * @throws Exception
     */
    @Test public final void failureMessageTest() throws Exception {
        SerialExecutor executor = new SerialExecutor();
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up an incomplete count down sequence as the input.
        String writeString = "10\n9\n7\n6\nENDCOUNTDOWN\nENDCOMMAND\n";
        String expectedString = "RESULTS 10\nFAILED\nDid not receive a valid "
          + "countdown sequence.\nENDFAILED\nENDRESULTS\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory.
        LineRawHandlerFactory factory =
          new LineRawHandlerFactory(new CountdownHandler(r, w));
        // Setting up and executing handler.
        SubcommandHandler h = (SubcommandHandler) factory.getHandler();
        h.parseAndExecute(10, null, executor);
        // Verify output.
        assertEquals(expectedString, w.toString());
    }

    /**
     * Tests using a Map with multiple caching handler factories.
     *
     * @throws Exception
     */
    @Test public final void multiFactoryTest() throws Exception {
        SerialExecutor executor = new SerialExecutor();
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input of randomly alternating COUNTDOWN and COUNTUP
        // commands.
        Random rand = newRandGen();
        StringBuilder writeString = new StringBuilder();
        for (int i = 0; i < ITERATIONS; i++) {
            if (rand.nextBoolean()) {
                writeString.append("COUNTDOWN\n");
                writeString.append(CountdownHandler.countdownString(i));
                writeString.append("ENDCOUNTDOWN\nENDCOMMAND\n");
            } else {
                writeString.append(String.format("COUNTUP 0 %d\n",
                    rand.nextInt(CountupHandler.MAX_MILLIS_DELAY)));
                writeString.append(CountupHandler.countupString(0, i));
                writeString.append("ENDCOUNTUP\nENDCOMMAND\n");
            }
        }
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.toString().getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Reading tokens, locating proper factory, and executing handlers.
        String inputData;
        String[] commandTokens;
        LineRawHandlerFactory f;
        SubcommandHandler h;
        for (int i = 0; i < ITERATIONS; i++) {
            inputData = r.read();
            String args = null;
            commandTokens = inputData.split(" ", 2);
            String baseCommand = commandTokens[0];
            if (commandTokens.length > 1) {
                args = commandTokens[1];
            }
            f = factoryMap.get(baseCommand);
            h = (SubcommandHandler) f.getHandler();
            h.parseAndExecute(i, args, executor);
        }
        // Parse and verify output.
        String readString = w.toString();
        StringBuilder expectedString = new StringBuilder();
        for (int i = 0; i < ITERATIONS; i++) {
          expectedString.append("RESULTS ");
          expectedString.append(i);
          expectedString.append("\nDONE\nENDRESULTS\n");
        }
        assertEquals(expectedString.toString(), readString);
    }

    /**
     * Builds a factory map for this test suite.
     *
     * @param in LineRawReader for input
     * @param out Writer for output
     * @return Map<String, LineRawHandlerFactory> representing command mapping
     */
    private Map<String, LineRawHandlerFactory> buildFactoryMap(
        final LineRawReader in, final Writer out) {
        Map<String, LineRawHandlerFactory> factoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        factoryMap.put("COUNTDOWN",
            new LineRawHandlerFactory(
                new CountdownHandler(in, out)));
        factoryMap.put("COUNTUP",
            new LineRawHandlerFactory(
                new CountupHandler(in, out)));
        return factoryMap;
    }
}
