//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of HostPort 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 07 Sep 2012   omd            Original Version
//*****************************************************************

#include "host-port.h"

#include <sstream>

#include "check.h"

using std::string;

HostPort::HostPort(const char* addr, uint16_t port)
    : address_(inet_addr(addr)), port_(htons(port)) {
}
HostPort::HostPort(const sockaddr_in& saddr)
    : address_(saddr.sin_addr.s_addr), port_(saddr.sin_port) {
  CHECK(saddr.sin_family == AF_INET);
}

HostPort HostPort::AnyAddress(uint16_t port) {
  HostPort ret;
  ret.address_ = htonl(INADDR_ANY);
  ret.port_ = htons(port);
  return ret;
}

string HostPort::ToString() const {
  // Maximum number of characters in an IPv4 address
  const int kMaxAddrLength = 15;

  std::ostringstream result;

  // Add 1 for '\0'
  char address_buffer[kMaxAddrLength + 1];
  in_addr addr_struct;
  addr_struct.s_addr = address_;
  result << inet_ntop(AF_INET, &addr_struct, address_buffer,
                      kMaxAddrLength + 1);
  result << ":" << ntohs(port_);
  return result.str();
}


sockaddr_in HostPort::ToSockAddr() const {
  sockaddr_in ret;
  // Zero out everything as some OSs have extra fields that we're not going to
  // fill in.
  bzero(&ret, sizeof(ret));
  ret.sin_family = AF_INET;
  ret.sin_port = PortNetworkOrder();
  ret.sin_addr.s_addr = AddressNetworkOrder();
  return ret;
}

bool HostPort::operator<(const HostPort& other) const {
  if (address_ < other.address_) {
    return true;
  } else if (address_ > other.address_) {
    return false;
  } else {
    return port_ < other.port_;
  }
}

bool HostPort::operator==(const HostPort& other) const {
  return address_ == other.address_ && port_ == other.port_;
}

