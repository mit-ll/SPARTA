//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Tests implementations of TA3 handlers
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 121205       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.handlers.test;

import static org.junit.Assert.*;

import edu.mit.ll.spar.common.UnitTester;
import org.junit.Test;

import edu.mit.ll.spar.ta3.handlers.UnsubscribeSubcommandHandler;
import edu.mit.ll.spar.ta3.handlers.SubscribeSubcommandHandler;
import edu.mit.ll.spar.ta3.handlers.ClearcacheCommandHandler;
import edu.mit.ll.spar.ta3.handlers.PublishSubcommandHandler;
import edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler;
import edu.mit.ll.spar.protocol.handlers.ShutdownCommandHandler;
import edu.mit.ll.spar.protocol.handlers.LineRawHandlerFactory;
import edu.mit.ll.spar.protocol.handlers.RootModeHandler;

import edu.mit.ll.spar.ta3.actors.SubscribingClient;
import edu.mit.ll.spar.ta3.actors.PublishingBroker;

import edu.mit.ll.spar.common.ConcurrentBufferedWriter;
import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.ByteArrayInputStream;
import java.io.CharArrayWriter;

import java.util.HashMap;
import java.util.Map;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Defines JUnit unit tests for NumberedCommandHandler.
 * TODO(njhwang) Copy some of this into standalone RootModeHandler unit tests.
 * TODO(njhwang) Do negative testing for error handling.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see     RootModeHandler
 * @see     ClearcacheCommandHandler
 * @see     ShutdownCommandHandler
 * @see     NumberedCommandHandler
 * @see     PublishSubcommandHandler
 * @see     SubscribeSubcommandHandler
 * @see     UnsubscribeSubcommandHandler
 * @see     UnitTester
 */
public class TA3SubcommandHandlerTest extends UnitTester {
    /** Number of publishing actor commands to test. */
    private static final int NUM_PUB_COMMANDS = 1;
    /** Number of subscribing actor commands to test. */
    private static final int NUM_SUB_COMMANDS = 2;
    /** Number of non-COMMAND root mode commands to test (SHUTDOWN isn't
     * counted, since no results are expected for a SHUTDOWN command). */
    private static final int NUM_ROOT_COMMANDS = 1;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(TA3SubcommandHandlerTest.class);

    /**
     * Tests nominal use of all publishing actor commands.
     *
     * @throws Exception
     */
    @Test public final void pubTest() throws Exception {
        // Setting up output.
        CharArrayWriter cw = new CharArrayWriter();
        ConcurrentBufferedWriter w = new ConcurrentBufferedWriter(cw,
            DEFAULT_BUFFER_SIZE);
        // Setting up input.
        StringBuilder writeString = new StringBuilder();
        writeString.append("COMMAND 0\n");
        writeString.append("PUBLISH\nMETADATA\nsample,metadata\n");
        writeString.append("PAYLOAD\nsRAW\n14\nsample payload");
        writeString.append("ENDRAW\nENDPAYLOAD\nENDPUBLISH\nENDCOMMAND\n");
        writeString.append("CLEARCACHE\n");
        writeString.append("SHUTDOWN\n");
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.toString().getBytes());
        LineRawReader r = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        // Setting up publisher.
        StubbedPublishingBroker pub = new StubbedPublishingBroker(r, w);
        // Setting up handler factory and factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildPubFactoryMap(r, w, pub);
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new RootModeHandler(r, factoryMap));
        // Reading tokens, obtaining handler, and executing handlers.
        RootModeHandler h;
        for (int i = 0; i < NUM_PUB_COMMANDS + NUM_ROOT_COMMANDS; i++) {
            h = (RootModeHandler) f.getHandler();
            h.parseAndExecute();
        }
        // Parse and verify output.
        String readString = cw.toString();
        StringBuilder expectedString = new StringBuilder();
        for (int i = 0; i < NUM_PUB_COMMANDS; i++) {
          expectedString.append("RESULTS ");
          expectedString.append(i);
          expectedString.append("\nDONE\nENDRESULTS\n");
        }
        for (int i = 0; i < NUM_ROOT_COMMANDS; i++) {
          expectedString.append("DONE\n");
        }
        assertEquals(expectedString.toString(), readString);
    }

    @Test public final void subTest() throws Exception {
        // Setting up input.
        StringBuilder writeString = new StringBuilder();
        writeString.append("COMMAND 0\n");
        writeString.append("SUBSCRIBE 0\nsample = filter\n");
        writeString.append("ENDCOMMAND\n");
        writeString.append("COMMAND 1\n");
        writeString.append("UNSUBSCRIBE 0\n");
        writeString.append("ENDCOMMAND\n");
        writeString.append("CLEARCACHE\n");
        writeString.append("SHUTDOWN\n");
        ByteArrayInputStream input =
            new ByteArrayInputStream(writeString.toString().getBytes());
        // Setting up subscriber.
        LineRawReader subReader = new LineRawReader(input, DEFAULT_BUFFER_SIZE);
        CharArrayWriter subCharWriter = new CharArrayWriter();
        ConcurrentBufferedWriter subWriter = new
          ConcurrentBufferedWriter(subCharWriter, DEFAULT_BUFFER_SIZE);
        StubbedSubscribingClient sub = new StubbedSubscribingClient(
            subReader, subWriter);
        // Setting up factory and factory map.
        Map<String, LineRawHandlerFactory> factoryMap =
            buildSubFactoryMap(subReader, subWriter, sub);
        LineRawHandlerFactory f =
            new LineRawHandlerFactory(
                new RootModeHandler(subReader, factoryMap));
        // Reading tokens, obtaining handler, and executing handlers.
        RootModeHandler h;
        for (int i = 0; i < NUM_SUB_COMMANDS + NUM_ROOT_COMMANDS; i++) {
            h = (RootModeHandler) f.getHandler();
            h.parseAndExecute();
        }
        // Parse and verify output.
        String readString = subCharWriter.toString();
        StringBuilder expectedString = new StringBuilder();
        for (int i = 0; i < NUM_SUB_COMMANDS; i++) {
          expectedString.append("RESULTS ");
          expectedString.append(i);
          expectedString.append("\nDONE\nENDRESULTS\n");
        }
        for (int i = 0; i < NUM_ROOT_COMMANDS; i++) {
          expectedString.append("DONE\n");
        }
        assertEquals(expectedString.toString(), readString);
    }

    /**
     * Builds a factory map for the publisher.
     *
     * @param in LineRawReader for input
     * @param out ConcurrentBufferedWriter for output
     * @param pub PublishingBroker actor
     * @return Map<String, LineRawHandlerFactory> representing command mapping
     */
    private Map<String, LineRawHandlerFactory> buildPubFactoryMap(
        final LineRawReader in, final ConcurrentBufferedWriter out,
        final PublishingBroker pub) {
        Map<String, LineRawHandlerFactory> subFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        subFactoryMap.put("PUBLISH",
            new LineRawHandlerFactory(
                new PublishSubcommandHandler(in, out, pub)));
        Map<String, LineRawHandlerFactory> rootFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        rootFactoryMap.put("CLEARCACHE",
            new LineRawHandlerFactory(
                new ClearcacheCommandHandler(in, out, pub)));
        rootFactoryMap.put("SHUTDOWN",
            new LineRawHandlerFactory(
                new ShutdownCommandHandler(in, out)));
        rootFactoryMap.put("COMMAND",
            new LineRawHandlerFactory(
                new NumberedCommandHandler(in, subFactoryMap)));
        return rootFactoryMap;
    }

    /**
     * Builds a factory map for the subscriber.
     *
     * @param in LineRawReader for input
     * @param out ConcurrentBufferedWriter for output
     * @param sub SubscribingClient actor
     * @return Map<String, LineRawHandlerFactory> representing command mapping
     */
    private Map<String, LineRawHandlerFactory> buildSubFactoryMap(
        final LineRawReader in, final ConcurrentBufferedWriter out,
        final SubscribingClient sub) {
        Map<String, LineRawHandlerFactory> subFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        subFactoryMap.put("SUBSCRIBE",
            new LineRawHandlerFactory(
                new SubscribeSubcommandHandler(in, out, sub)));
        subFactoryMap.put("UNSUBSCRIBE",
            new LineRawHandlerFactory(
                new UnsubscribeSubcommandHandler(in, out, sub)));
        Map<String, LineRawHandlerFactory> rootFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        rootFactoryMap.put("CLEARCACHE",
            new LineRawHandlerFactory(
                new ClearcacheCommandHandler(in, out, sub)));
        rootFactoryMap.put("SHUTDOWN",
            new LineRawHandlerFactory(
                new ShutdownCommandHandler(in, out)));
        rootFactoryMap.put("COMMAND",
            new LineRawHandlerFactory(
                new NumberedCommandHandler(in, subFactoryMap)));
        return rootFactoryMap;
    }
}
