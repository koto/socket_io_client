#!/usr/bin/env python
#
# This file is part of
# "Hacking HTML 5" training materials
# @author Krzysztof Kotowicz <kkotowicz at gmail dot com>
# @copyright Krzysztof Kotowicz <kkotowicz at gmail dot com>
# @see http://blog.kotowicz.net

import sys
import os
import select
import WebSocketsClient
from colorize import colorize, color_names

if __name__ == '__main__': # script part
  if len(sys.argv) == 1 :
    print "socket_io_client by Krzysztof Kotowicz, http://blog.kotowicz.net"
    print
    print "Usage: "
    print "socket_io_client host port [origin_to_simulate] [socket_io_path]"
    print
    print "Example: socket_io_client websocket.example.org 8888 client.example.org /socket.io/websocket"
    sys.exit(1)

  HOST = len(sys.argv) <= 1 and 'websocket.security.localhost' or sys.argv[1]    # The remote host
  PORT = len(sys.argv) <= 2 and 8124 or int(sys.argv[2])                           # The remote port
  ORIGIN = len(sys.argv) <= 3 and 'victim.security.localhost' or sys.argv[3]     # origin to simulate
  PATH = len(sys.argv) <= 4 and '/socket.io/websocket' or sys.argv[4]

  interactive = os.isatty(0)

  sys.stderr.write("Connecting to " + HOST + ":" + str(PORT) + "\n")
  client = WebSocketsClient.SocketIoClient(host=HOST,port=PORT,origin=ORIGIN,path=PATH)

  if (interactive):
    prompt = colorize("\nWhat to send (nothing: quit, ~jXXX: json object, ~rXXX - raw socket data XXX):", fg='green')
  else:
    prompt = ""

  quit = False
  p = 0

  import random
  while not quit:
    try:
      sys.stderr.flush()

      # Wait for input from stdin & socket
      inputready, outputready,exceptrdy = select.select([0],[],[], 0)
      if client.can_recv():
        inputready.append(client.socket)
      for i in inputready:
          if i == client.socket:
              data = client.recv()
              if data == False:
                  sys.stderr.write(colorize('Socket empty, quitting',fg='red'))
                  quit = True
                  break
              else:
                  if len(data) == 0:
                    break
                  sys.stdout.write(client.ws_encode(data))
                  if interactive:
                    sys.stderr.write(prompt)
          elif i == 0:
              data = sys.stdin.readline().strip()
              if not data:
                  sys.stderr.write(colorize('Shutting down.', fg='red'))
                  quit = True
                  break
              else:
                sent = client.send(data)
                if interactive:
                  data = colorize("Sent: " + sent, fg='yellow')
                  sys.stderr.write(data)
                  sys.stderr.write(prompt)
                else:
                  sys.stderr.write("Sent payload #%i\n" % p)
                  p = p + 1
      if len(inputready) > 0:
        sys.stdout.flush()
        sys.stderr.flush()

    except KeyboardInterrupt:
      sys.stderr.write(colorize('Interrupted.',fg='red'))
      quit = True
      pass

  client.close()
  sys.stderr.write("\n")
