#!/usr/bin/env python
#
# This file is part of
# "Hacking HTML 5" training materials
# @author Krzysztof Kotowicz <kkotowicz at gmail dot com>
# @copyright Krzysztof Kotowicz <kkotowicz at gmail dot com>
# @see http://blog.kotowicz.net

import socket
import select
import sys

class WebSocketsClient:
  """WebSockets client"""

  PREFIX = "\x00"
  SUFFIX = "\xFF"

  def __init__(self, handshake_file='handshake.bin', **kwargs):
    """Connects to socket and performs the handshake"""
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.buf = ''
    self.handshake(handshake_file, kwargs)

  def __del__(self):
    self.close()

  def close(self):
    self.socket.close();

  def handshake(self, handshake_file, kw):
    """Sends the handshake from the file"""
    self.socket.connect((kw['host'], kw['port']))
    handshake = open(handshake_file,'rb').read()
    handshake = handshake.replace('%HOST%',kw['host'])\
                .replace('%PORT%',str(kw['port']))\
                .replace('%ORIGIN%',kw['origin'])\
                .replace('%PATH%',kw['path'])

    self.socket.sendall(handshake)

  def send_raw(self, s):
    """Send the message through websocket"""
    self.socket.sendall(self.ws_encode(s))
    return s

  def ws_encode(self, s):
    """Encode the message in WebSockets frame"""
    return self.PREFIX + s + self.SUFFIX

  def heartbeat(self,bytes=4096):
    """Sends last heartbeat in buffer back to the server"""
    self.recv_raw(bytes)
    msgs = self.buf.split(self.PREFIX)
    msgs.reverse()
    for msg in msgs:
      if self.is_heartbeat(msg):
        self.send_raw(msg[:-1]) # strip trailing \xFF
        self.buf = self.buf.replace(msg + self.SUFFIX, '') #remove from buffer
        break;

  def recv_raw(self, bytes = 4096):
    """Read bytes from socket into the buffer"""
    read = self.socket.recv(bytes)
    self.buf += read

  def recv(self, bytes = 4096):
    """Return new message from the server (also resends but ignores heartbeats)"""
    self.recv_raw(bytes)
    start = self.buf.find(self.PREFIX)
    if start == -1:
      return ''
    end = self.buf.find(self.SUFFIX, start)
    if end == -1:
      return ''

    # we have a full message in buffer now
    msg = self.buf[start+1:end]
    if start > 0 :
        sys.stdout.write(self.buf[:start]) # something before the message, probably part of handshake
    if len(self.buf) == end:
      self.buf = ''
    else:
      self.buf = self.buf[end+1:]

    if self.is_heartbeat(msg): # heartbeat, resend & ignore
       self.send_raw(msg)
       msg = ''

    return msg

  def has_msg_in_buffer(self):
    """Check if there is a complete message in the buffer"""
    begin = self.buf.find(self.PREFIX)
    if begin == -1:
      return False
    end = self.buf.find(self.SUFFIX, begin)
    if end == -1:
      return False
    return True

  def is_heartbeat(self, s):
    return False #to be defined in child class

  def json_encode(self,s):
    return s #to be defined in child class

  def encode(self, s):
    return s #to be defined in child class

  def send(self, send):
    """Encode and send the message trough socket"""
    if send.startswith('~j'):
      send = send[2:] # strip ~j
      send = self.encode(self.json_encode(send))
    elif send.startswith('~r'): # raw message, not neccessarily socket.io compatible
      send = send[2:]
    else:
      send = self.encode(send)
    return self.send_raw(send)

  def can_recv(self):
    """Check if we're ready for recv()"""
    if self.has_msg_in_buffer():
      return True
    inputready, outputready,exceptrdy = select.select([self.socket],[],[], 0)
    return len(inputready) > 0

class SocketIoClient(WebSocketsClient):
  """Socket.Io compatible client"""

  def is_heartbeat(self, s):
    return s.startswith('~m~4~m~~h~')

  def json_encode(self,s):
    return '~j~' + s

  def encode(self, s):
    return '~m~%d~m~%s' % (len(s), s)

