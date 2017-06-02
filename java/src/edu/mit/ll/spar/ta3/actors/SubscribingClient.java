//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-16 14:25:52 -0400 (Tue, 16 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         SubscribingClient for TA3.1 baseline.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.actors;

import static edu.mit.ll.spar.common.PrimitiveUtils.detailedExceptionString;

import javax.jms.MessageListener;
import javax.jms.MessageConsumer;
import javax.jms.TextMessage;
import javax.jms.Message;

import java.util.concurrent.LinkedBlockingQueue;
import java.util.HashMap;
import java.util.Map;

import org.apache.activemq.ActiveMQConnectionFactory;
import javax.jms.ExceptionListener;
import javax.jms.Connection;
import javax.jms.Session;
import javax.jms.Topic;

import org.apache.activemq.broker.SslContext;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.KeyManager;
import java.security.KeyStore;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.common.ConcurrentBufferedWriter;
import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;
import java.io.OutputStreamWriter;
import java.io.FileInputStream;
import java.io.FileDescriptor;
import java.io.InputStream;
import java.util.Scanner;
import java.io.Writer;
import java.io.File;

import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;

import edu.mit.ll.spar.ta3.handlers.UnsubscribeSubcommandHandler;
import edu.mit.ll.spar.ta3.handlers.SubscribeSubcommandHandler;
import edu.mit.ll.spar.ta3.handlers.ClearcacheCommandHandler;
import edu.mit.ll.spar.protocol.handlers.LineRawHandlerFactory;
import edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler;
import edu.mit.ll.spar.protocol.handlers.ShutdownCommandHandler;
import edu.mit.ll.spar.protocol.handlers.RootModeHandler;

import uk.co.flamingpenguin.jewel.cli.CliFactory;
import uk.co.flamingpenguin.jewel.cli.Option;

import uk.co.flamingpenguin.jewel.cli.ArgumentValidationException;
import edu.mit.ll.spar.protocol.ProtocolException;
import javax.jms.InvalidDestinationException;
import javax.jms.InvalidSelectorException;
import javax.jms.JMSException;
import java.io.IOException;

/**
 * An ActiveMQ client designed to be used with PublishingBroker. In paricular
 * this subscribes to the right user and control topics and has some convenience
 * methods for having the client wait until PublishingBroker sends an end of
 * protocol message, etc.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2985 $
 * @see PubSubActor
 */
public class SubscribingClient extends SubscribingActor {
    /** Interval (ms) at which to try reconnecting to broker. */
    private static final int CONNECT_RETRY_INTERVAL = 5000;
    /** The connection. */
    private Connection connection;
    /**
     * This is the subscriber for messages that are destined to the end user (as
     * opposed to control messages).
     */
    private Map<Integer, MessageConsumer> subscriberMap;
    /** Subscriber for messages on the control stream. */
    private MessageConsumer controller;
    /** This is a message listener for events on the control stream. */
    private MessageListener controllerListener;
    /** the session for all communications with PublishingBroker. */
    private Session session;
    /**
     * The broker stream can (optionally) send a message on the control stream
     * indicating that it has sent all messages. When then message is received
     * this becomes true
     */
    private boolean gotEOPMessage = false;
    /** Topic to subscribe to. */
    private Topic topic;
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(SubscribingClient.class);
    /** Connection factory. */
    private ActiveMQConnectionFactory connectionFactory;
    /** Reader. */
    private LineRawReader input;
    /** Writer. */
    private final Writer output;
    private boolean shutdownComplete;
    private LinkedBlockingQueue<String> receivedPubs;

    /** Facilitates command line paramter parsing. */
    // CHECKSTYLE:OFF
    public interface CmdOptions {
      @Option(shortName = "h", defaultValue = "localhost",
              description = "Connection address with which to connect to broker")
      String getHost();

      @Option(shortName = "p", defaultValue = "61619",
              description = "Port with which to connect to broker")
      int getPort();

      @Option(shortName = "r", defaultValue = "20",
              description = "Length of publications received history. "
                          + "Increasing this will decrease the chance that "
                          + "more than one subscription will activate for a "
                          + "single subscription, at the cost of higher "
                          + "average publication processing time.")
      int getPubHistoryLength();

      @Option(shortName = "n", defaultValue = "0",
              description = "Client ID; used primiarly to simulate command "
                          + "line aguments that need to have unique values "
                          + "for each instance.")
      int getClientID();

      @Option(shortName = "s", description = "Enable SSL")
      boolean getSSLOn();

      @Option(shortName = "k", 
              description = "Client JKS keystore file")
      String getKeystore();
      boolean isKeystore();

      @Option(shortName = "t",
              description = "Client JKS truststore file")
      String getTruststore();
      boolean isTruststore();

      // TODO(njhwang) error check these values

      @Option(helpRequest = true, description = "Print this help message")
      boolean getHelp();
    }
    // CHECKSTYLE:ON

    /**
     * Constructor.
     *
     * @param in InputStream
     * @param out Writer
     * @param connectHost the host where the PublishingBroker can be found
     * @param connectPort the port where the PublishingBroker can be found
     *
     * @throws JMSException if anything goes wrong setting up AcitveMQ
     * @throws IOException if I/O errors occur
     */
    public SubscribingClient(
            final LineRawReader in, final Writer out,
            final String connectHost, final int connectPort, 
            final int pubHistoryLength,
            final boolean SSLOn, final String keystore,
            final String truststore)
            throws JMSException, IOException {
        String connectionUrl = null;
        try {
          if (!SSLOn) {
            connectionUrl = "tcp://" + connectHost + ":" + connectPort;
          } else {
            // Fetch server keystore info
            byte[] sslCert = null;
            if (keystore != null) {
              FileInputStream f = new FileInputStream(keystore);
              ByteArrayOutputStream b = new ByteArrayOutputStream();
              byte[] buf = new byte[512];
              int i = f.read(buf);
              while (i  > 0) {
                  b.write(buf, 0, i);
                  i = f.read(buf);
              }
              f.close();
              sslCert = b.toByteArray();
            }
            KeyManager[] km = null;
            if (sslCert != null && sslCert.length > 0) {
              ByteArrayInputStream bin = new ByteArrayInputStream(sslCert);
              KeyStore ks = KeyStore.getInstance("jks");
              ks.load(bin, "SPARtest".toCharArray());
              KeyManagerFactory kmf = 
                  KeyManagerFactory.getInstance(
                      KeyManagerFactory.getDefaultAlgorithm());  
              kmf.init(ks, "SPARtest".toCharArray());
              km = kmf.getKeyManagers();
            }

            // Fetch client keystore info
            TrustManager[] tm = null;
            if (truststore != null) {
              KeyStore tks = KeyStore.getInstance("jks");
              tks.load(new FileInputStream(truststore), null);
              TrustManagerFactory tmf  = 
                  TrustManagerFactory.getInstance(
                      TrustManagerFactory.getDefaultAlgorithm());
              tmf.init(tks);
              tm = tmf.getTrustManagers();
            }

            // Set the SSL context and connection URL
            SslContext.setCurrentSslContext(new SslContext(km, tm, null));
            connectionUrl = "ssl://" + connectHost + ":" + connectPort;
          }
        } catch (Exception e) {
          LOGGER.error(detailedExceptionString("Encountered "
              + "Exception while attempting to set up network "
              + "connection.\n", e));
          System.exit(1);
        }
        connectionFactory = new ActiveMQConnectionFactory(connectionUrl);
        output = new ConcurrentBufferedWriter(out, DEFAULT_BUFFER_SIZE);
        input = in;

        // Setting up command handlers.
        Map<String, LineRawHandlerFactory> subFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        subFactoryMap.put("SUBSCRIBE",
            new LineRawHandlerFactory(
                new SubscribeSubcommandHandler(input, output, this)));
        subFactoryMap.put("UNSUBSCRIBE",
            new LineRawHandlerFactory(
                new UnsubscribeSubcommandHandler(input, output, this)));
        Map<String, LineRawHandlerFactory> rootFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        rootFactoryMap.put("CLEARCACHE",
            new LineRawHandlerFactory(
                new ClearcacheCommandHandler(input, output, this)));
        rootFactoryMap.put("SHUTDOWN",
            new LineRawHandlerFactory(
                new ShutdownCommandHandler(input, output)));
        setNumberedCommandHandler(
          new NumberedCommandHandler(input, subFactoryMap));
        rootFactoryMap.put("COMMAND",
            new LineRawHandlerFactory(getNumberedCommandHandler()));
        setRootModeHandler(new RootModeHandler(input, rootFactoryMap));

        receivedPubs = new LinkedBlockingQueue<String>(pubHistoryLength);
    }

    /** Silly constructor needed for StubbedSubscribingClient in test. */
    protected SubscribingClient() {
      output = null;
    }

    /**
     * Runs SubscribingClient.
     *
     * @throws JMSException if ActiveMQ encounters errors
     */
    public final void run() throws JMSException {
        // Connect to PublishingBroker.
        while (true) {
          try {
            connection = connectionFactory.createTopicConnection();
            break;
          } catch (JMSException e) {
            LOGGER.info("Could not connect to broker. Retrying in " +
                CONNECT_RETRY_INTERVAL + " seconds.");
            try {
              Thread.sleep(CONNECT_RETRY_INTERVAL);
            } catch (InterruptedException ie) {
              LOGGER.warn("InterruptedException occurred when waiting to "
                  + "retry connecting to broker.");
            }
          }
        }
        connection.setExceptionListener(new ExceptionListener() {
          public void onException(JMSException e) {
            // This feels like a fragile hack, but ActiveMQ doesn't seem to
            // provide many good ways to track a broken connection to the
            // broker. When the TCP transport that supports this connection
            // receives any sort of Exception, this method will get called.
            // ActiveMQ doesn't set the JMSException's error code, nor does it
            // set a linked exception (as provided for by the JMS API), but it
            // does set the "cause" as a java.io.EOFException object when the
            // connection is broken. We therefore check that the cause is an
            // EOFException, and assume that this means the connection to the
            // broker was lost.
            if (e.getCause() instanceof java.io.EOFException) {
              try {
                  output.write("DISCONNECTION\n");
                  output.flush();
              } catch (IOException ioe) {
                  LOGGER.error(detailedExceptionString("Encountered "
                      + "IOException when attempting to send DISCONNECTION "
                      + "message.\n", ioe));
                  System.exit(1);
              }            
            }
          }
        });
        session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
        Topic controlTopic = session.createTopic(CONTROL_TOPIC_NAME);
        controller = session.createConsumer(controlTopic);
        controllerListener = new ControllerListener();
        controller.setMessageListener(controllerListener);
        topic = session.createTopic(TOPIC_NAME);
        subscriberMap = new HashMap<Integer, MessageConsumer>();
        connection.start();

        // Set up command loop.
        String rootModeCommand = "";
        while (!rootModeCommand.equals("SHUTDOWN")) {
          try {
            output.write("READY\n");
            output.flush();
          } catch (IOException e) {
            LOGGER.error(detailedExceptionString("Error occurred when "
                  + "attempting to write READY signal.\n", e));
            System.exit(1);
          }
          try {
            rootModeCommand = getRootModeHandler().parseAndExecute();
          } catch (ProtocolException e) {
            LOGGER.error(detailedExceptionString("Error occurred when "
                  + "attempting to parse protocol.\n", e));
            System.exit(1);
          } catch (IOException e) {
            LOGGER.warn("Error occurred when attempting to read data; "
                  + "pipe with test harness probably lost.");
            break;
          }
        }

        // Make sure numbered commands have completed.
        LOGGER.info("Received SHUTDOWN. Waiting for commands to complete.");
        getNumberedCommandHandler().shutdown();
    }

    /** An inner class that receives messages on the subscription topic. */
    class SubscriberListener implements MessageListener {
        /**
         * Outputs a PUBLICATION message when a message is received.
         *
         * @param msg Message
         */
        @Override
        public void onMessage(final Message msg) {
            synchronized (this) {
                String msgId = null;
                try {
                    msgId = msg.getJMSMessageID();
                } catch (JMSException e) {
                    LOGGER.error(detailedExceptionString("Could not "
                      + "retrieve JMS message ID from message.\n", e));
                    System.exit(1);
                }
                if (!receivedPubs.contains(msgId)) {
                  try {
                      String payload = ((TextMessage) msg).getText();
                      output.write("PUBLICATION\n"
                          + "PAYLOAD\nRAW\n" + payload.length() + "\n"
                          + payload + "ENDRAW\nENDPAYLOAD\n"
                          + "ENDPUBLICATION\n");
                      output.flush();
                  } catch (IOException e) {
                      LOGGER.error(detailedExceptionString("Encountered "
                          + "IOException when attempting to send "
                          + "PUBLICATION message.\n", e));
                      System.exit(1);
                  } catch (ClassCastException e) {
                      LOGGER.error(detailedExceptionString("SubscriberListener "
                         + "can only accept messages of type TextMessage.\n", e));
                      System.exit(1);
                  } catch (JMSException e) {
                      LOGGER.error(detailedExceptionString("Encountered "
                         + "JMSException when attempting to send PUBLICATION "
                         + "message.\n", e));
                      System.exit(1);
                  }
                  if (receivedPubs.remainingCapacity() == 0) {
                    try {
                      receivedPubs.take();   
                    } catch (InterruptedException e) {
                      LOGGER.error(detailedExceptionString("Could not update "
                         + "received publication history.\n", e));
                      System.exit(1);
                    }
                  }
                  receivedPubs.offer(msgId);
                }
                this.notifyAll();
            }
        }
    }

    /** Listener for control messages (i.e., end of protocol messages). */
    class ControllerListener implements MessageListener {
        /**
         * Notifies any waiters that the EOP message was received.
         *
         * @param msg Message
         */
        @Override
        public void onMessage(final Message msg) {
            synchronized (this) {
                gotEOPMessage = true;
                this.notifyAll();
            }
        }
    }

    /**
     * This will block until an end of protocol message is received on the
     * control stream. PublishingBroker has a sendEndOfProtocolMessage method
     * that will generate the necessary message.
     */
    public final void waitForEOPMessage() {
        synchronized (controllerListener) {
            while (!gotEOPMessage) {
                try {
                    controllerListener.wait();
                } catch (InterruptedException e) {
                    LOGGER.warn("Encountered InterruptedException while "
                        + "waiting for end of protocol message.", e);
                    return;
                }
            }
        }
    }

    /**
     * Getter for the EOP message flag.
     *
     * @return boolean
     */
    public final boolean getEOPStatus() {
      synchronized (controllerListener) {
        return gotEOPMessage;
      }
    }

    /**
     * Must be called before the object is destroyed.
     *
     * @throws JMSException if ActiveMQ throws any exceptions
     * @throws IOException if I/O errors occur
     */
    // CHECKSTYLE:OFF
    public synchronized void shutdown() throws JMSException, IOException {
    // CHECKSTYLE:ON
        LOGGER.info("Waiting for EOP message from server.");
        waitForEOPMessage();
        LOGGER.info("Shutting down client components.");
        controller.close();
        for (MessageConsumer c : subscriberMap.values()) {
           c.close();
        }
        session.close();
        connection.stop();
        connection.close();
        output.close();
        input.close();
        LOGGER.info("Shut down complete.");
        shutdownComplete = true;
    }

    /** Empty CLEARCACHE handler. This baseline doesn't need to do anything. */
    // CHECKSTYLE:OFF
    public void clearcache() {
    // CHECKSTYLE:ON
      return;
    }

    /**
     * Subscribes to the main topic with the provided subscription rule, and
     * writes the results of the subscribe task (success or failed) to the
     * output.
     *
     * @param subId subscription ID
     * @param subRule SQL where clause to filter with
     * @return String results
     */
    // CHECKSTYLE:OFF
    public String subscribe(final int subId, final String subRule) {
    // CHECKSTYLE:ON
        MessageConsumer subscriber = null;
        assert session != null : "SubscribingClient.start() must be called "
          + "once before attempting to call SubscribingClient.subscribe().";
        // Check if subscriber ID already exists.
        if (subscriberMap.get(subId) != null) {
          return "Subscriber ID already subscribed.";
        }
        // Create a new subscriber.
        try {
            subscriber = session.createConsumer(topic, subRule, false);
        } catch (InvalidDestinationException e) {
            return detailedExceptionString("SubscribingClient could not access"
                + " SPAR message topic.", e);
        } catch (InvalidSelectorException e) {
            return detailedExceptionString("Invalid subscription rule.", e);
        } catch (JMSException e) {
            return detailedExceptionString("SubscribingClient failed to create"
                + " consumer.", e);
        }
        // Configure the new subscriber's MessageListener.
        try {
            subscriber.setMessageListener(new SubscriberListener());
        } catch (JMSException e) {
            return detailedExceptionString("SubscribingClient failed to set "
                + "consumer message listener.", e);
        }
        // Put the new subscriber in the subscriber directory.
        subscriberMap.put(subId, subscriber);
        return null;
    }

    /**
     * UNSUBSCRIBE command handler.
     *
     * @param subId subscription ID
     * @return String results
     */
    // CHECKSTYLE:OFF
    public String unsubscribe(final int subId) {
    // CHECKSTYLE:ON
        MessageConsumer subscriber = subscriberMap.get(subId);
        if (subscriber == null) {
          return "Subscriber ID does not exist.";
        }
        try {
            subscriber.close();
        } catch (JMSException e) {
            return detailedExceptionString("SubscribingClient failed to close"
                + " consumer.", e);
        }
        subscriberMap.remove(subId);
        return null;
    }

  /**
   * Main method.
   *
   * @param args String[]
   */
  public static void main(final String[] args) {
    CmdOptions options = null;
    try {
       options = CliFactory.parseArguments(CmdOptions.class, args);
    } catch (ArgumentValidationException e) {
       System.out.println(e);
       System.exit(1);
    }
    SubscribingClient sub = null;
    try {
      sub = new SubscribingClient(
          new LineRawReader(FileDescriptor.in, DEFAULT_BUFFER_SIZE),
          new OutputStreamWriter(System.out),
          options.getHost(), options.getPort(), options.getPubHistoryLength(),
          options.getSSLOn(), options.getKeystore(), options.getTruststore());
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Could not instantiate SubscribingClient.", e));
      System.exit(1);
    }
    final SubscribingClient finalSub = sub;
    Runtime.getRuntime().addShutdownHook(new Thread() {
      public void run() {
        try {
          if (!finalSub.shutdownComplete) {
            LOGGER.info("Did not shutdown gracefully. Performing cleanup.");
            finalSub.shutdown();
          }
          Runtime.getRuntime().halt(0);
        } catch (Exception e) {
          LOGGER.warn(
              detailedExceptionString("Failed to clean up gracefully.\n", e));
          Runtime.getRuntime().halt(1);
        }
      }
    });
    try {
      finalSub.run();
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Error occurred when running SubscribingClient.\n", e));
      System.exit(1);
    }
  try {
      finalSub.shutdown();
      System.exit(0);
    } catch (Exception e) {
      LOGGER.warn(
          detailedExceptionString("Failed to shutdown gracefully.\n", e));
      System.exit(1);
    }
  }
}
