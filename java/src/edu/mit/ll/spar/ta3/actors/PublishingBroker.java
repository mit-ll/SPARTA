//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-19 12:13:50 -0400 (Fri, 19 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         PublishingBroker for TA3.1 baseline.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120815       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.actors;

import static edu.mit.ll.spar.common.PrimitiveUtils.detailedExceptionString;

import org.apache.activemq.advisory.AdvisorySupport;
import javax.jms.MessageConsumer;
import javax.jms.MessageListener;
import javax.jms.MessageProducer;
import javax.jms.TextMessage;
import javax.jms.Message;

import org.apache.activemq.ActiveMQConnectionFactory;
import org.apache.activemq.broker.SslBrokerService;
import org.apache.activemq.broker.BrokerService;
import javax.jms.Destination;
import javax.jms.Connection;
import javax.jms.Session;
import javax.jms.Topic;

import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.KeyManager;
import java.security.KeyStore;

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

import java.util.List;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import edu.mit.ll.spar.protocol.handlers.LineRawHandlerFactory;
import edu.mit.ll.spar.protocol.handlers.NumberedCommandHandler;
import edu.mit.ll.spar.protocol.handlers.ShutdownCommandHandler;
import edu.mit.ll.spar.protocol.handlers.RootModeHandler;
import edu.mit.ll.spar.ta3.handlers.ClearcacheCommandHandler;
import edu.mit.ll.spar.ta3.handlers.PublishSubcommandHandler;
import edu.mit.ll.spar.common.SchemaHandler;

import java.util.HashMap;
import java.util.Map;

import uk.co.flamingpenguin.jewel.cli.CliFactory;
import uk.co.flamingpenguin.jewel.cli.Option;

import uk.co.flamingpenguin.jewel.cli.ArgumentValidationException;
import edu.mit.ll.spar.protocol.ProtocolException;
import javax.jms.JMSException;
import java.io.IOException;

/**
 * A combination of a broker and a publisher.
 * TODO(njhwang) Split this into two separate entities.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2997 $
 * @see PubSubActor
 */
public class PublishingBroker extends PublishingActor {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(PublishingBroker.class);
    /**
     * Listens to advisory messages to keep track of the number of
     * consumers.
     */
    private final SubCountAdvisoryListener subCountListener =
        new SubCountAdvisoryListener();
    /** Number of subscribers connected to the broker. */
    //private final int numSubscribers;
    /** Writer. */
    private final Writer output;
    /** Connection factory. */
    private ActiveMQConnectionFactory connectionFactory;
    /** The connection on which messages are sent. */
    private Connection connection;
    /** The broker service object that delivers messages. */
    private BrokerService brokerService;
    /** The publisher that sends messages to clients. */
    private MessageProducer publisher;
    /** The session associated with the connection. */
    private Session session;
    /** Reader. */
    private LineRawReader input;
    /** Schema handler. */
    private SchemaHandler schemaHandler;
    private boolean shutdownComplete;
    private int messageCount = 0;

    /**
     * Sets up command line parameters for use with main().
     */
    public interface CmdOptions {
      // CHECKSTYLE:OFF
      @Option(shortName = "d", longName = "force_disconn",
          defaultValue = "-1", description = "Force network server to close "
          + "after this number of seconds; use to simulate disconnects when "
          + "testing. Negative values will cause network server to never "
          + "disconnect. Default is -1.")
      int getDisconnectTime();

      @Option(shortName = "h", defaultValue = "localhost",
              description = "Connection address to set up for subscribers")
      String getHost();

      @Option(shortName = "f", defaultValue = "metadata_schema.csv",
              description = "Metadata schema configuration file name")
      String getFilename();

      @Option(shortName = "p", defaultValue = "61619",
              description = "Port to set up for subscribers")
      int getPort();
      // TODO(njhwang) error check these values

      @Option(shortName = "s", description = "Enable SSL")
      boolean getSSLOn();

      @Option(shortName = "k", 
              description = "Server JKS keystore file")
      String getKeystore();
      boolean isKeystore();

      @Option(shortName = "t",
              description = "Server JKS truststore file")
      String getTruststore();
      boolean isTruststore();

      @Option(helpRequest = true, description = "Print this help message")
      boolean getHelp();
      // CHECKSTYLE:ON
   }

    /**
     * Constructor.
     *
     * @param in InputStream
     * @param out Writer
     * @param connectHost String host to monitor for connections
     * @param connectPort int port to monitor for connections
     * @param schemaFilename path to schema configuration *.csv file
     * @param numSubs number of subscribers to wait for before accepting
     *                commands
     *
     * @throws JMSException if ActiveMQ encounters errors
     * @throws IOException if I/O errors occur
     */
    public PublishingBroker(final LineRawReader in,
                            final Writer out,
                            final String connectHost,
                            final int connectPort,
                            final String schemaFilename,
                            final boolean SSLOn,
                            final String keystore,
                            final String truststore)
        throws JMSException, IOException {
        //numSubscribers = numSubs;
        shutdownComplete = false;
        if (!SSLOn) {
          brokerService = new BrokerService();
        } else {
          brokerService = new SslBrokerService();
        }

        // Subscribers will connect to this TCP socket.
        try {
          if (!SSLOn) {
            brokerService.addConnector("tcp://" + connectHost
                + ":" + connectPort);
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
              //ks.load(bin, "password".toCharArray());
              ks.load(bin, "SPARtest".toCharArray());
              KeyManagerFactory kmf = 
                  KeyManagerFactory.getInstance(
                      KeyManagerFactory.getDefaultAlgorithm());  
              //kmf.init(ks, "password".toCharArray());
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

            // Add SSL connector to broker
            ((SslBrokerService)brokerService).addSslConnector(
                "ssl://" + connectHost + ":" + connectPort 
                + "?transport.enabledCipherSuites="
                + "TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA"
                //+ "SSL_RSA_WITH_RC4_128_SHA,SSL_DH_anon_WITH_3DES_EDE_CBC_SHA"
                + "?transport.needClientAuth=true", km, tm, null);
          }
        // Note that addConnector() throws Exception (nothing more specific).
        } catch (Exception e) {
          LOGGER.error(detailedExceptionString("Generic Exception thrown when"
              + " adding connection to broker service.\n", e));
          System.exit(1);
          /*throw new JMSException(String.format("Error occurred when attempting"
              + " to add network connection [%s:%d] to broker service.",
              connectHost, connectPort));*/
        }

        // Set up the broker
        brokerService.setUseShutdownHook(false);
        brokerService.setPersistent(false);
        brokerService.setBrokerName(BROKER_NAME);
        /*
         * Set up the publisher/broker topic connection.
         *
         * Publisher will connect to the broker via VM, since they logically
         * act as a single entity and will be in the same JVM.
         *
         * create=false disallows VM transport to create an embedded broker,
         *      and prevents race conditions from occuring
         * broker.persistent=false indicates persistent storage is not being
         *      used by broker
         * TODO(njhwang) Put these in a config file
         */
        String connectURL = "vm://" + brokerService.getBrokerName()
            + "?marshal=false&broker.persistent=false&create=false";
        connectionFactory = new ActiveMQConnectionFactory(connectURL);

        /*
         * Lends performance boost since we do not mutate JMS messages after
         * they are sent.
         */
        connectionFactory.setCopyMessageOnSend(false);
        /*
         * Lends performance boost, but means send() returns immediately
         * whether the message has been sent or not, and could lead to
         * message loss.
         */
        connectionFactory.setUseAsyncSend(true);
        // TODO(njhwang) Consider setting setDispatchAsync as well

        // Set up I/O.
        output = new ConcurrentBufferedWriter(out, DEFAULT_BUFFER_SIZE);
        input = in;

        // Set up command handlers.
        Map<String, LineRawHandlerFactory> subFactoryMap =
            new HashMap<String, LineRawHandlerFactory>();
        subFactoryMap.put("PUBLISH",
            new LineRawHandlerFactory(
                new PublishSubcommandHandler(input, output, this)));
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

        // Set up schema handler.
        schemaHandler = new SchemaHandler(schemaFilename);
    }

    /** Silly constructor required by StubbedPublishingBroker in test. */
    protected PublishingBroker() {
      output = null;
      //numSubscribers = 0;
    }

    /**
     * Runs the command loop and publishing broker.
     *
     * @throws JMSException if ActiveMQ encounters errors
     */
    public final void run() throws JMSException {
        try {
          brokerService.start();
        // Note that start() only throws Exception (nothing more specific).
        } catch (Exception e) {
          LOGGER.error(detailedExceptionString("Generic Exception thrown when"
              + " adding starting broker service.\n", e));
          System.exit(1);
        }
        brokerService.waitUntilStarted();
        connection = connectionFactory.createConnection();

        /*
         * Set up the publisher/broker topic session.
         *
         * createSession parameters:
         * false (i.e., non-transacted) lets us select the acknowledgement mode
         * AUTO_ACKNOWLEDGE makes the publisher's session acknowledge receipt of
         * messages when the publisher's session successfully returns from
         * receive(), or when the publisher's MessageListener returns a message
         * to the publisher
         */
        session = connection.createSession(false,
            Session.AUTO_ACKNOWLEDGE);

        // Create a topic desination for the publisher.
        Topic topic = session.createTopic(TOPIC_NAME);

        // Create the publisher.
        publisher = session.createProducer(topic);

        // ActiveMQ sends "Advisory Messages" when certain events happen. Here
        // we subscribe to consumer advisory messages on the SPAR_TOPIC so we'll
        // get notified when new consumers subscribe or unsubscribe. This allows
        // us to do things like progamatically wait until a certain number of
        // consumers have arrived, etc.
        Destination advisoryDestination =
           AdvisorySupport.getConsumerAdvisoryTopic(topic);
        MessageConsumer advisoryConsumer =
           session.createConsumer(advisoryDestination);
        advisoryConsumer.setMessageListener(subCountListener);
        connection.start();

        // Wait for the given number of subscribers to connect before accepting
        // any commands.
        //waitForSubCount(numSubscribers);

        // Start the command loop.
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
            LOGGER.warn(detailedExceptionString("Error occurred when "
                  + "attempting to read data; "
                  + "pipe with test harness probably lost.", e));
            break;
          }
        }

        // Make sure all numbered commands complete before returning.
        LOGGER.info("Received SHUTDOWN. Waiting for commands to complete.");
        getNumberedCommandHandler().shutdown();
    }

    /**
     * Getter for schemaHandler.
     *
     * @return SchemaHandler
     */
    public final SchemaHandler getSchemaHandler() {
      return schemaHandler;
    }

    /**
     * Nested class that receives advisory messages and keeps track of the
     * number of connected consumers.
     *
     * @see MessageListener
     */
    class SubCountAdvisoryListener implements MessageListener {
        /** The number of connected subscribers. */
        private int subCount = 0;

        @Override
        public void onMessage(final Message msg) {
            int currCount = subCount;
            try {
                currCount = msg.getIntProperty("consumerCount");
            } catch (JMSException e) {
                LOGGER.error(detailedExceptionString("Exception occured when "
                      + "attempting to access consumerCount property.\n", e));
                System.exit(1);
            }
            synchronized (this) {
                // TODO(njhwang) Note that I'm not 100% sure that this is
                // sufficient. The client subscribes to the control stream
                // before subscribing to the topic stream and I *think* we are
                // guaranteed that this means the control connection is up and
                // running before the topic connection but the docs aren't
                // clear. There may be a race condition here in which we'd think
                // a consumer is subscribed but the control subscription is not
                // yet active so that endOfProtocol messages could get lost.
                // Unit tests pass so I don't think this would be an issue and
                // it'd be a huge pain to fix so I'm leaving this for now but it
                // may become necessary to track connections to both the regular
                // topic and the control topic and only count a consumer as
                // connected when we've seen both connections occur. If so
                // here's some code that took a while to track down that would
                // be helpful:
                //
                // ActiveMQMessage amqm = (ActiveMQMessage) msg;
                // ConsumerInfo cinfo = (ConsumerInfo) amqm.getDataStructure();
                // String topic_name = cinfo.getDestination().getPhysicalName();
                subCount = currCount;
                this.notifyAll();
            }
        }

        /**
         * Returns the number of consumers connected to the broker.
         * @return int
         */
        public final synchronized int getSubCount() {
            return subCount;
        }
    }

    /**
     * This sends a special end of protocol message on the control connection.
     * The client has a corresponding waitForProtocolEndMessage() message. This
     * makes it easy to synchronize shutting down the client only when all
     * messages have been received.
     *
     * @throws JMSException if ActiveMQ encounters errors
     */
    private void sendEOPMessage() throws JMSException {
        TextMessage msg = session.createTextMessage();
        Topic controlTopic = session.createTopic(CONTROL_TOPIC_NAME);
        MessageProducer controller = session.createProducer(controlTopic);
        controller.send(msg);
        controller.close();
    }

    /**
     * This *must* be called to properly destroy the class.
     * Note that the API advises against simply stopping/starting a broker
     * and expecting it to function properly. One should simply create a new
     * PublishingBroker.
     *
     * @throws JMSException if ActiveMQ encounters errors
     * @throws IOException if I/O errors occur
     */
    // CHECKSTYLE:OFF
    public synchronized void shutdown() throws Exception {
    // CHECKSTYLE:ON
        LOGGER.info("Sending EOP message to clients.");
        sendEOPMessage();
        LOGGER.info("Waiting for clients to disconnect.");
        waitForSubDisconnects();
        LOGGER.info("Shutting down server components.");
        publisher.close();
        session.close();
        connection.stop();
        connection.close();
        brokerService.stop();
        brokerService.waitUntilStopped();
        output.close();
        input.close();
        LOGGER.info("Shut down complete.");
        shutdownComplete = true;
    }

    /** Empty CLEARCACHE handler. This baseline does not need to do anything. */
    // CHECKSTYLE:OFF
    public void clearcache() {
    // CHECKSTYLE:ON
      return;
    }


    /**
     * Wait for all subscribers to disconnect.
     */
    public final void waitForSubDisconnects() {
        synchronized (subCountListener) {
            while (subCountListener.getSubCount() > 0) {
                try {
                    subCountListener.wait();
                } catch (InterruptedException e) {
                    LOGGER.error(detailedExceptionString("Encountered "
                        + "InterruptedException when waiting for "
                        + "subscribers to disconnect.\n", e));
                    System.exit(1);
                }
            }
        }
    }

    /**
     * PUBLISH command handler.
     *
     * @param metadata metadata
     * @param payload payload
     * @return String
     */
    // CHECKSTYLE:OFF
    public String publish(final String metadata, final String payload) {
    // CHECKSTYLE:ON
        assert session != null : "Attempting to publish before "
          + "PublishingBroker has been started.";
        String[] metadataValues = null;
        try {
          metadataValues = schemaHandler.splitMetadata(metadata);
        } catch (ProtocolException e) {
            return detailedExceptionString("PublishingBroker failed to parse"
                    + " publish metadata values.\n", e);
        }
        List<TextMessage> messages = null;
        try {
            messages = 
              schemaHandler.createMessages(metadataValues, payload, session);
        } catch (JMSException e) {
            return detailedExceptionString("PublishingBroker failed to create"
                + " text message(s).\n", e);
        } catch (ProtocolException e) {
            return detailedExceptionString("PublishingBroker failed to parse"
                    + " publish metadata values.\n", e);
        }

        // Perform publish operation(s).
        for (TextMessage msg : messages) {
          try {
              msg.setJMSMessageID(String.valueOf(messageCount++));
              publisher.send(msg);
          } catch (JMSException e) {
              return detailedExceptionString("PublishingBroker failed to "
                      + "publish message.\n", e);
          }
        }
        return null;
    }

  /**
   * Main method.
   *
   * @param args String[]
   * @throws JMSException if ActiveMQ encounters errors
   * @throws IOException if I/O errors occur
   */
  public static void main(final String[] args) {
    CmdOptions options = null;
    try {
       options = CliFactory.parseArguments(CmdOptions.class, args);
    } catch (ArgumentValidationException e) {
       System.out.println(e);
       System.exit(1);
    }
    PublishingBroker pub = null;
    try {
      pub = new PublishingBroker(
          new LineRawReader(FileDescriptor.in, DEFAULT_BUFFER_SIZE),
          new OutputStreamWriter(System.out),
          options.getHost(), options.getPort(),
          options.getFilename(), options.getSSLOn(),
          options.getKeystore(), options.getTruststore());
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Could not instantiate PublishingBroker.\n", e));
      System.exit(1);
    }
    final PublishingBroker finalPub = pub;
    Runtime.getRuntime().addShutdownHook(new Thread() {
      public void run() {
        try {
          if (!finalPub.shutdownComplete) {
            LOGGER.info("Did not shutdown gracefully. Performing cleanup.");
            finalPub.shutdown();
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
      finalPub.run();
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Error occurred when running PublishingBroker.\n", e));
      System.exit(1);
    }
    try {
      finalPub.shutdown();
      System.exit(0);
    } catch (Exception e) {
      LOGGER.warn(
          detailedExceptionString("Failed to shutdown gracefully.\n", e));
      System.exit(1);
    }
  }
}
