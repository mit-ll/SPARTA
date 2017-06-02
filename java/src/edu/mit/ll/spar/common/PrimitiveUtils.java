//*****************************************************************************
// Copyright MIT Lincoln Laboratory
// $Date: 2013-02-21 13:58:09 -0500 (Thu, 21 Feb 2013) $
// Project:             SPAR
// Authors:             ni24039
// Description:         Implements methods on Java primitives when
//                      the Java API proves inconvenient and/or
//                      inefficient
//
// Modifications:
// Date         Name            Modification
// ----         ----            ------------
// 120711       ni24039         Original version
// 120727       ni24039         Removed unused methods
// 120803       ni24039         Made generic method for concatArray
// 120807       ni24039         Minor revisions in response to review 43
// 120810       ni24039         Changed converString() to work with
//                              primitive boxed types
//*****************************************************************************
package edu.mit.ll.spar.common;

import java.lang.reflect.Array;

/**
 * Class holding static methods to operate on Java primitives.
 *
 * Methods should be added to this class only if there are no reasonable
 * alternatives within standard Java libraries.
 *
 * Note that this class cannot be instantiated, and users should include "import
 * static PrimitiveUtils.*".
 *
 * @author  ni24039 (last updated by $Author: ni24039 $)
 * @version $Revision: 2409 $
 */
public final class PrimitiveUtils {
    /**
     * Suppresses default constructor for noninstantiability.
     */
    private PrimitiveUtils() {
        throw new AssertionError();
    }

    // TODO(njhwang) Write unit tests for all of these.

    /**
     * Concatenate a sequence of arrays of any class type (except for
     * primitive types, as autoboxing won't work on arrays of primitives).
     * If a primitive type must be used, consider using the object wrapper of
     * the primitive type (i.e. Integer instead of int), or using the
     * primitive versions of concatArrays (a new one may need to be defined if
     * one hasn't been already).
     *
     * @param <T> type for array to be concatenated
     * @param arrays arrays of type T[] to concatenate
     * @return concatenated array of type T[]
     */
    public static <T> T[] concatArrays(final T[]... arrays) {
        int totalLen = 0;
        for (T[] arr : arrays) {
            assert arr != null : "Cannot concatenate array with null object.";
            totalLen += arr.length;
        }
        /*
         * Note that we suppress the warning for the unchecked cast,
         * as there is no way to tell the compiler that this cast is safe.
         */
        @SuppressWarnings("unchecked")
        T[] all = (T[]) Array.newInstance(
            arrays.getClass().getComponentType().getComponentType(), totalLen);
        int copied = 0;
        for (T[] arr : arrays) {
            System.arraycopy(arr, 0, all, copied, arr.length);
            copied += arr.length;
        }
        return all;
    }

    /**
     * Concatenate a sequence of char[] arrays.
     *
     * @param arrays arrays of type char[] to concatenate
     * @return concatenated array of type char[]
     */
    public static char[] concatArrays(final char[]... arrays) {
        int totalLen = 0;
        for (char[] arr : arrays) {
            assert arr != null : "Cannot concatenate array with null object.";
            totalLen += arr.length;
        }
        char[] all = new char[totalLen];
        int copied = 0;
        for (char[] arr : arrays) {
            System.arraycopy(arr, 0, all, copied, arr.length);
            copied += arr.length;
        }
        return all;
    }

    /**
     * Convert a string to the specificed class.
     *
     * @param paramString string to convert to an Object
     * @param paramClass class to convert string to
     * @return Object representing the paramClass representation of paramString
     */
    public static Object convertString(final String paramString,
                                       final Class paramClass) {
        Object paramVal;
        if (paramClass.equals(Boolean.class)
         || paramClass.equals(boolean.class)) {
            paramVal = Boolean.parseBoolean(paramString);
        } else if (paramClass.equals(Character.class)
                || paramClass.equals(char.class)) {
            if (paramString.length() > 1) {
                throw new IllegalArgumentException("Conversion from String to "
                    + "Character can only be done on one-character Strings.");
            }
            paramVal = paramString.charAt(0);
        } else if (paramClass.equals(Byte.class)
                || paramClass.equals(byte.class)) {
            paramVal = Byte.parseByte(paramString);
        } else if (paramClass.equals(Short.class)
                || paramClass.equals(short.class)) {
            paramVal = Short.parseShort(paramString);
        } else if (paramClass.equals(Integer.class)
                || paramClass.equals(int.class)) {
            paramVal = Integer.parseInt(paramString);
        } else if (paramClass.equals(Long.class)
                || paramClass.equals(long.class)) {
            paramVal = Long.parseLong(paramString);
        } else if (paramClass.equals(Float.class)
                || paramClass.equals(float.class)) {
            paramVal = Float.parseFloat(paramString);
        } else if (paramClass.equals(Double.class)
                || paramClass.equals(double.class)) {
            paramVal = Double.parseDouble(paramString);
        } else if (paramClass.equals(String.class)) {
            paramVal = paramString;
        } else {
            throw new IllegalArgumentException("convertString does not support "
                + "the " + paramClass + " class.");
        }
        return paramVal;
    }

  /**
   * Appends the stack trace from an exception to a desired error message.
   *
   * @param msg String to prepend error message
   * @param e Exception that triggered the original error
   * @return String representing desired error message, as well as a full
   *         stack trace
   */
  public static String detailedExceptionString(final String msg,
                                                 final Exception e) {
      StringBuilder results = new StringBuilder();
      results.append(msg);
      results.append("EXCEPTION:\n");
      results.append(e.toString());
      results.append("\n");
      results.append("STACKTRACE:\n");
      for (StackTraceElement s : e.getStackTrace()) {
          results.append(s.toString());
          results.append("\n");
      }
      return results.toString();
  }
}
