import socket
import subprocess

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')
try:
    # Run VLC with the appropriately selected demuxer (as we're not giving
    # it a filename which would allow it to guess correctly)
    vlc = subprocess.Popen(
        ['vlc', '--demux', 'h264', '-'],
        stdin=subprocess.PIPE)
    while True:
        # Repeatedly read 1k of data from the connection and write it to
        # VLC's stdin
        data = connection.read(1024)
        if not data:
            break
        vlc.stdin.write(data)
finally:
    connection.close()
    server_socket.close()
    vlc.terminate()
