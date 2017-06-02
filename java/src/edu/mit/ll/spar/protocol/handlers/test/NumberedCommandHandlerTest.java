//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2014-06-09 09:15:28 -0400 (Mon, 09 Jun 2014) $
// Project:             SPAR
// Authors:             ni24039
// Description:         NumberedCommandHandlerTest; tests
//                      NumberedCommandHandler
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120731       ni24039         Original version
// 120808       ni24039         Revisions in response to review 44
// 120811       ni24039         Revisions in response to review 44
//*****************************************************************************
package edu.mit.ll.spar.protocol.handlers.test;

import static org.junit.Assert.*;

import edu.mit.ll.spar.common.UnitTester;
import java.util.Random;
import org.junit.Test;

import edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler;
import edu.mit.ll.spar.protocol.handlers.LineRawHandlerFactory;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import edu.mit.ll.spar.protocol.ProtocolException;
import edu.mit.ll.spar.common.UnitTester;
import java.io.ByteArrayInputStream;
import java.io.CharArrayWriter;
import java.io.Writer;
import java.util.HashMap;
import java.util.Map;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.ProtocolException;

/**
 * Defines JUnit unit tests for NumberedCommandHandler.
 *
 * @author  ni24039 (last updated by $Author: mi24752 $)
 * @version $Revision: 4983 $
 * @see     edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler
 * @see     edu.mit.ll.spar.protocol.handlers.SubcommandHandler
 * @see     edu.mit.ll.spar.common.UnitTester
 */
public class NumberedCommandHandlerTest extends UnitTester {
    /** Number of sequential commands to test with. */
    private static final int ITERATIONS = 10;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(NumberedCommandHandlerTest.class);

    /**
     * Tests nominal use of NumberedCommandHandler.
     *
     * @throws Exception
     */
    @Test public final void nominalTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
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
        // Setting up numbered command handler factory.
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new NumberedCommandHandler(r, factoryMap));
        // Reading tokens, obtaining handler, and executing handlers.
        NumberedCommandHandler h;
        for (int i = 0; i < ITERATIONS; i++) {
            h = (NumberedCommandHandler) f.getHandler();
            h.parseAndExecute(Integer.toString(i));
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
     * Tests that a ProtocolException is thrown when an unrecognized subcommand
     * is used.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void exceptionTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
        String writeString = "FEEDME\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Setting up numbered command handler factory.
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new NumberedCommandHandler(r, factoryMap));
        // Obtain and execute handler.
        NumberedCommandHandler h = (NumberedCommandHandler) f.getHandler();
        h.parseAndExecute("0");
    }

    /**
     * Tests that a ProtocolException is thrown when an empty subcommand is
     * used.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void emptyCommandTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
        String writeString = "\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Setting up numbered command handler factory.
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new NumberedCommandHandler(r, factoryMap));
        // Obtain and execute handler.
        NumberedCommandHandler h = (NumberedCommandHandler) f.getHandler();
        h.parseAndExecute("0");
    }

    /**
     * Tests that a ProtocolException is thrown when an invalid command ID
     * is used.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void invalidCommandIdTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
        String writeString = "COUNTDOWN\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Setting up numbered command handler factory.
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new NumberedCommandHandler(r, factoryMap));
        // Obtain and execute handler.
        NumberedCommandHandler h = (NumberedCommandHandler) f.getHandler();
        h.parseAndExecute("a");
    }

    /**
     * Tests that an exception is thrown if the command ID is never set.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void noCommandIdTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
        String writeString = "COUNTDOWN\n";
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Execute handler.
        NumberedCommandHandler h = new NumberedCommandHandler(r, factoryMap);
        h.parseAndExecute(null);
    }

    /**
     * Tests that an exception is thrown if the command IDs are not properly
     * increasing.
     *
     * @throws Exception
     */
    @Test (expected = ProtocolException.class)
    public final void skippedCommandIdTest() throws Exception {
        // Setting up output.
        CharArrayWriter w = new CharArrayWriter();
        // Setting up input.
        StringBuilder writeString = new StringBuilder();
        writeString.append("COUNTDOWN 10\n");
        writeString.append(CountdownHandler.countdownString(10));
        writeString.append("ENDCOUNTDOWN\nENDCOMMAND\n");
        writeString.append("COUNTDOWN 10\n");
        writeString.append(CountdownHandler.countdownString(10));
        writeString.append("ENDCOUNTDOWN\nENDCOMMAND\n");
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.toString().getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildFactoryMap(r, w);
        // Execute handler.
        NumberedCommandHandler h = new NumberedCommandHandler(r, factoryMap);
        h.parseAndExecute("0");
        h.parseAndExecute("2");
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
