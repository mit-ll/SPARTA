//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2014-06-09 09:15:28 -0400 (Mon, 09 Jun 2014) $
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

import edu.mit.ll.spar.ta3.actors.SubscribingClient;

import edu.mit.ll.spar.protocol.reader.LineRawReader;
import java.io.Writer;

/**
 * Silly stubbed actor for unit testing.
 *
 * @author  ni24039 (last updated by $Author: mi24752 $)
 * @version $Revision: 4983 $
 * @see     edu.mit.ll.spar.ta3.actors.PublishingBroker
 */
public class StubbedSubscribingClient extends SubscribingClient {
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
  public StubbedSubscribingClient(final LineRawReader in,
                                  final Writer out) {
    input = in;
    output = out;
  }

  /** Empty shutdown command. */
  public void shutdown() {}

  /** Empty clearcache command. */
  public void clearcache() {}

  /**
   * Empty subscribe command.
   *
   * @param subId int
   * @param subRule String
   * @return String
   */
  public final String subscribe(final int subId, final String subRule) {
    return null;
  }

  /**
   * Empty unsubscribe command.
   *
   * @param subId int
   * @return String
   */
  public final String unsubscribe(final int subId) {
    return null;
  }
}
