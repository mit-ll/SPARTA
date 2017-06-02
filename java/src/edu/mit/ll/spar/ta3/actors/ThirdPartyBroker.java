//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-04-19 12:13:50 -0400 (Fri, 19 Apr 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         ThirdPartyBroker for TA3.1 baseline.
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

import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;

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
public class ThirdPartyBroker {
    /** Logger for this class. */
    private static final Logger LOGGER =
        LoggerFactory.getLogger(ThirdPartyBroker.class);
    /** Broker name. */
    protected static final String BROKER_NAME = "SPAR_BROKER";
    /** The broker service object that delivers messages. */
    private BrokerService brokerService;
    private boolean shutdownComplete;

    /**
     * Sets up command line parameters for use with main().
     */
    public interface CmdOptions {
      // CHECKSTYLE:OFF
      @Option(shortName = "h", defaultValue = "localhost",
              description = "Connection address to set up for subscribers")
      String getHost();

      @Option(shortName = "p", defaultValue = "61619",
              description = "Port to set up for subscribers")
      int getPort();

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
    public ThirdPartyBroker(final String connectHost,
                            final int connectPort,
                            final boolean SSLOn,
                            final String keystore,
                            final String truststore)
        throws JMSException, IOException {
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
    }

    /**
     * This *must* be called to properly destroy the class.
     * Note that the API advises against simply stopping/starting a broker
     * and expecting it to function properly. One should simply create a new
     * ThirdPartyBroker.
     *
     * @throws JMSException if ActiveMQ encounters errors
     * @throws IOException if I/O errors occur
     */
    // CHECKSTYLE:OFF
    public synchronized void shutdown() throws Exception {
    // CHECKSTYLE:ON
        brokerService.stop();
        brokerService.waitUntilStopped();
        shutdownComplete = true;
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
    ThirdPartyBroker broker = null;
    try {
      broker = new ThirdPartyBroker(options.getHost(), options.getPort(),
          options.getSSLOn(), options.getKeystore(), options.getTruststore());
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Could not instantiate ThirdPartyBroker.\n", e));
      System.exit(1);
    }
    final ThirdPartyBroker finalBroker = broker;
    Runtime.getRuntime().addShutdownHook(new Thread() {
      public void run() {
        try {
          if (!finalBroker.shutdownComplete) {
            LOGGER.info("Did not shutdown gracefully. Performing cleanup.");
            finalBroker.shutdown();
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
      finalBroker.run();
    } catch (Exception e) {
      LOGGER.error(
        detailedExceptionString("Error occurred when running ThirdPartyBroker.\n", e));
      System.exit(1);
    }
    /*try {
      finalBroker.shutdown();
      System.exit(0);
    } catch (Exception e) {
      LOGGER.warn(
          detailedExceptionString("Failed to shutdown gracefully.\n", e));
      System.exit(1);
    }*/
  }
}
