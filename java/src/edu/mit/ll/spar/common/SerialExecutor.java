//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Executor that serially executes all submitted tasks
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 121205       ni24039         Original Version
//*****************************************************************************
package edu.mit.ll.spar.common;

import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Executor that serially executes all submitted tasks.
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public class SerialExecutor implements Executor {
  /** Logger for this class. */
  private static final Logger LOGGER =
      LoggerFactory.getLogger(SerialExecutor.class);
  /** Queue of Runnable tasks. */
  private final LinkedBlockingQueue<Runnable> tasks =
    new LinkedBlockingQueue<Runnable>();
  /** Internal Executor that will actually do the task execution. */
  private final Executor executor;
  /** Current task being executed. */
  private Runnable active;

  /** Constructor. */
  public SerialExecutor() {
    // Internal executor is simply a direct executor that immediately executes
    // its Runnable.
    this.executor = new Executor() {
      public void execute(final Runnable r) {
        r.run();
      }
    };
    active = null;
  }

  /**
   * Submits a new task to the execution queue (and executes it if no other
   * tasks are executing.
   *
   * @param r Runnable task
   */
  public final synchronized void execute(final Runnable r) {
    // Queue a new task, which will execute its Runnable and then tell this
    // SerialExecutor to schedule the next task.
    try {
      tasks.put(new Runnable() {
        public void run() {
          try {
            r.run();
          } finally {
            scheduleNext();
          }
        }
      });
    } catch (InterruptedException e) {
      LOGGER.error(
        "Encountered InterruptedException when queueing new task", e);
      System.exit(1);
    }
    // If no tasks are executing, schedule one.
    if (active == null) {
      scheduleNext();
    }
  }

  /** Executes all remaining tasks in the queue. */
  public final synchronized void executeAll() {
    while ((active = tasks.poll()) != null) {
      executor.execute(active);
    }
  }

  /** If a new task is available in the queue, executes it. */
  private synchronized void scheduleNext() {
    // Execute the next queued task.
    active = tasks.poll();
    if (active != null) {
      executor.execute(active);
    }
  }
}
