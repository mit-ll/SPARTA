//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Silly stubbed actor that doesn't do anything.
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 121205       ni24039         Original version
//*****************************************************************************
package edu.mit.ll.spar.ta3.handlers.test;

import edu.mit.ll.spar.ta3.actors.PublishingBroker;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

/**
 * Silly stubbed actor for unit testing.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 * @see     PublishingBroker
 */
public class StubbedPublishingBroker extends PublishingBroker {
  /** Writer. */
  private Writer output;
  /** Reader. */
  private LineRawReader input;

  /**
   * Constructor.
   *
   * @param in LineRawReader
   * @param out Writer
   */
  public StubbedPublishingBroker(final LineRawReader in,
                                 final Writer out) {
    input = in;
    output = out;
  }

  /** Empty shutdown command. */
  public void shutdown() {}

  /** Empty clearcache command. */
  public void clearcache() {}

  /**
   * Empty publish command.
   *
   * @param metadata String
   * @param payload String
   * @return String
   */
  public final String publish(final String metadata, final String payload) {
    return null;
  }
}
