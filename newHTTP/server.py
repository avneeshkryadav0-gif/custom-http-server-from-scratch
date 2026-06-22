import socket
import os
import threading
import sqlite3  # Built-in SQL database engine

# Define asset and database paths on the local drive
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')
DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')

# Mapping dictionary for file extensions to MIME types
MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon'
}

def init_db():
    """Initializes the database file and schema before accepting network clients."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create the table if it does not exist yet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("[*] SQL Database initialized successfully and ready.")

def handle_client(client_socket, client_address):
    try:
        # Read the incoming data stream (2048 byte buffer)
        request_bytes = client_socket.recv(2048)
        if not request_bytes:
            client_socket.close()
            return
            
        request_text = request_bytes.decode('utf-8', errors='ignore')
        
        # Split headers out from the body payload via the double newline delimiter (\r\n\r\n)
        parts_of_request = request_text.split("\r\n\r\n")
        header_section = parts_of_request[0]
        body_section = parts_of_request[1] if len(parts_of_request) > 1 else ""
        
        lines = header_section.split("\r\n")
        if not lines or not lines[0]:
            client_socket.close()
            return
            
        # Parse Request Line items (e.g., "POST /submit HTTP/1.1")
        parts = lines[0].split(" ")
        if len(parts) < 2:
            client_socket.close()
            return
            
        method = parts[0]  # "GET" or "POST"
        path = parts[1]    # Target endpoint / resource route
        
        thread_name = threading.current_thread().name
        print(f"[{thread_name}] Detected: {method} request for {path} from {client_address}")
        
        # ---------------------------------------------------------------------
        # BRANCH 1: DATA SUBMISSION OVER WRITE CORRIDOR (POST /submit -> SQL INSERT)
        # ---------------------------------------------------------------------
        if method == "POST" and path == "/submit":
            print(f"[{thread_name}] Processing form submission payload...")
            
            # Defensive check: pull body if TCP window split payload across separate packets
            if not body_section and "Content-Length" in header_section:
                extra_data = client_socket.recv(1024)
                body_section = extra_data.decode('utf-8', errors='ignore')
            
            print(f"[{thread_name}] Form body content: {body_section}")

            # Extract value parameter out of key=value form formatting
            if "username=" in body_section:
                username = body_section.split("username=")[1].split("&")[0].replace("+", " ")
            else:
                username = "Anonymous"
                
            # Execute SQL Write command inside current thread context
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                # Parameterized query design explicitly blocks injection attack parameters
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                conn.commit()
                conn.close()
                print(f"[{thread_name}] SQL success: Inserted user '{username}' into database.")
                
                response_body = f"<h1>Success!</h1><p>'{username}' has been written to the SQL table permanently.</p><a href='/'>Go Back</a> | <a href='/users'>View All Users</a>"
            except Exception as sql_err:
                print(f"[-] Database insertion failure: {sql_err}")
                response_body = "<h1>500 Internal Server Error</h1><p>Failed to save data to database.</p>"
            
            status_line = "HTTP/1.1 200 OK\r\n"
            content_type = "text/html; charset=utf-8"
            
        # ---------------------------------------------------------------------
        # BRANCH 2: DIRECTORY VIEWER RENDER CHANNEL (GET /users -> SQL SELECT)
        # ---------------------------------------------------------------------
        elif method == "GET" and path == "/users":
            print(f"[{thread_name}] Querying database user directory...")
            
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM users ORDER BY id DESC")
                rows = cursor.fetchall()
                conn.close()
                
                # Dynamically compile the layout list from raw rows
                list_items = ""
                for row in rows:
                    user_id, name = row
                    list_items += f"<li><strong>#{user_id}</strong>: {name}</li>"
                
                if not list_items:
                    list_items = "<li>No users registered yet!</li>"
                
                # Construct page framework string wrapping our query outputs
                response_body = f"""
                <!DOCTYPE html>
                <html>
                <head><title>Database Directory</title><link rel='stylesheet' href='/style.css'></head>
                <body>
                    <h1>Registered Users List</h1>
                    <ul>{list_items}</ul>
                    <br>
                    <a href='/'>← Back to Registration Form</a>
                </body>
                </html>
                """
            except Exception as sql_err:
                print(f"[-] Database selection failure: {sql_err}")
                response_body = "<h1>500 Internal Server Error</h1><p>Failed to query database entries.</p>"
                
            status_line = "HTTP/1.1 200 OK\r\n"
            content_type = "text/html; charset=utf-8"

        # ---------------------------------------------------------------------
        # BRANCH 3: STATIC ASSET LOADING WITH LOCAL SANITIZATION (GET ASSETS)
        # ---------------------------------------------------------------------
        else:
            if path == "/":
                path = "/index.html"
                
            # 1. Resolve targeted URL to an absolute path coordinate map location
            requested_path = os.path.abspath(os.path.join(PUBLIC_DIR, path.lstrip("/")))
            # 2. Get the clean absolute boundary directory path constraint
            real_public_dir = os.path.abspath(PUBLIC_DIR)
            
            # 3. SECURITY VERIFICATION CHECK: Common path base folder match validation gates
            if os.path.commonpath([real_public_dir]) == os.path.commonpath([real_public_dir, requested_path]):
                
                if os.path.exists(requested_path) and os.path.isfile(requested_path):
                    with open(requested_path, 'rb') as f:
                        response_body = f.read()
                        
                    status_line = "HTTP/1.1 200 OK\r\n"
                    
                    # Inspect resource extension layout types
                    _, ext = os.path.splitext(requested_path)
                    content_type = MIME_TYPES.get(ext.lower(), 'application/octet-stream')
                else:
                    response_body = b"<h1>404 File Not Found</h1>"
                    status_line = "HTTP/1.1 404 Not Found\r\n"
                    content_type = "text/html; charset=utf-8"
            else:
                # Malicious breakout exploit blocker activation execution
                print(f"[{thread_name}] ⚠️ SECURITY WARNING: Blocked path traversal exploit vector: '{path}'")
                response_body = b"<h1>403 Forbidden: Access Denied</h1>"
                status_line = "HTTP/1.1 403 Forbidden\r\n"
                content_type = "text/html; charset=utf-8"

        # Transform string response types into raw network wire byte layouts
        if isinstance(response_body, str):
            response_body = response_body.encode('utf-8')

        # Format structure envelope headers
        headers = (
            f"{status_line}"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "\r\n"
        )
        
        # Flush structured payloads down connection pipe channels
        client_socket.sendall(headers.encode('utf-8') + response_body)
        
    except Exception as e:
        print(f"[-] Error inside active execution transaction worker thread: {e}")
    finally:
        # Snap pipeline channel interface explicitly shut to avoid holding memory leaks
        client_socket.close()

def start_server():
    # Make sure structural databases exist before executing listen loops
    init_db()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # '0.0.0.0' binds to all network interfaces so external devices can hit it over Wi-Fi
    HOST = '0.0.0.0'
    PORT = 8080
    
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"[*] Secure Application Server running. Accessible locally on port {PORT}")
    
    while True:
        try:
            # Main engine capture loop catches a client connection request
            client_socket, client_address = server_socket.accept()
            
            # Spin up an independent isolated parallel worker execution loop instance
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address)
            )
            client_thread.start()
        except Exception as e:
            print(f"[-] Critical failure inside main application tracking sequence: {e}")

if __name__ == "__main__":
    start_server()