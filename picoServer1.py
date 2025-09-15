import usocket as socket

# Function to read a file and return its content
def read_file(path):
    with open(path, 'r') as f:
        return f.read()

# Your socket setup code would go here
# s = socket.socket(...)
# s.bind(...)
# s.listen(...)

while True:
    conn, addr = s.accept()
    request_line = conn.recv(1024).decode('utf-8').split('\r\n')[0]
    path = request_line.split(' ')[1]

    response = ""
    content_type = ""

    try:
        if path == '/' or path == '/index.html':
            response = read_file('index.html')
            content_type = "text/html"
        
        elif path == '/style.css':
            response = read_file('style.css')
            content_type = "text/css"

        elif path == '/script.js':
            response = read_file('script.js')
            content_type = "application/javascript"

        # You can add more elif blocks for other files (e.g., images)

        else:
            response = "<h1>404 Not Found</h1>"
            content_type = "text/html"

        # Send the response to the client
        conn.send("HTTP/1.1 200 OK\r\n")
        conn.send(f"Content-Type: {content_type}\r\n")
        conn.send("Connection: close\r\n\r\n")
        conn.sendall(response.encode('utf-8'))

    except OSError as e:
        # Handle file not found or other errors
        conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")
        conn.send("Error: File not found or couldn't be read.".encode('utf-8'))
    finally:
        conn.close()
