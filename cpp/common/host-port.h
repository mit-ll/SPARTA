//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class for managing network addresses and ports 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 07 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_HOST_PORT_H_
#define CPP_COMMON_HOST_PORT_H_

#include <arpa/inet.h>
#include <string>

/// Simple class to make handling IPv4 addresses and ports easy to work with.
/// Handles network vs. host byte ordering, etc.
class HostPort {
 public:
  /// Default constructor.
  HostPort() {}
  /// Constructs a HostPort from a address in standard dotted decimal notation
  /// and a port in host byte order.
  HostPort(const char* addr, uint16_t port);
  /// Constructs a HostPort from an saddr_in struct. As these generally hold the
  /// data in network byte order that is assumed here.
  HostPort(const struct sockaddr_in& saddr);
  /// Returns a HostPort for the "any" address. This is useful for servers as it
  /// allows you to bind to all network interfaces on the given port. The port is
  /// in host byte order.
  static HostPort AnyAddress(uint16_t port);

  /// Return the address in netowrk byte order
  uint32_t AddressNetworkOrder() const {
    return address_;
  }

  /// The address in host order.
  uint32_t AddressHostOrder() const {
    return ntohl(address_);
  }

  /// Return the port in network byte order
  uint16_t PortNetworkOrder() const {
    return port_;
  }

  /// The port in host order.
  uint16_t PortHostOrder() const {
    return ntohs(port_);
  }

  /// Returns the struct sockaddr_in struct that is required by various unix
  /// system calls.
  sockaddr_in ToSockAddr() const;

  /// Return a string represenation like "192.168.0.1:332"
  std::string ToString() const;

  /// So we can use HostPort objects as keys in std::map and such. Compares first
  /// by address, then by port (in network byte order).
  bool operator<(const HostPort& other) const;
  bool operator==(const HostPort& other) const;

 private:
  /// Network address in network byte order
  uint32_t address_;
  /// Port in network byte order
  uint16_t port_;
};

#endif
