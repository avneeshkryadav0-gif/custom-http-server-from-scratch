# Custom Multi-Threaded HTTP Application Server from Scratch

A lightweight, high-performance HTTP web application server built using pure Python sockets without any high-level web frameworks (like Flask, Django, or Express). This project implements low-level systems networking, concurrent request processing, structural HTTP request/response parsing, dynamic MIME-type mapping, security path sanitization, and data persistence using an SQL database.

## 🚀 Features

* **Low-Level Socket Architecture:** Communicates directly with the operating system network layer using standard Python `socket` APIs (TCP/IP stack).
* **Multi-Threaded Concurrency:** Utilizes a worker-thread model to handle multiple incoming client requests simultaneously without blocking the main event loop.
* **Dynamic Route & Protocol Parsing:** Extracts and analyzes raw HTTP request line items, headers, and payload bodies to separate traffic workflows cleanly.
* **Persistent SQL Storage:** Integrates a built-in SQLite database layer to permanently store and retrieve dynamic user-submitted form data.
* **Robust File I/O Engine:** Reads and streams raw binary data from disk while dynamically identifying and injecting appropriate `Content-Type` MIME headers (HTML, CSS, JS, PNG, etc.).
* **Directory Traversal Defense:** Implements strict logical boundary validation (`os.path.commonpath`) to prevent path traversal vulnerability attacks (`../`).
* **LAN Visibility:** Configured to listen across all network interfaces (`0.0.0.0`), allowing local network devices like phones or tablets to access the application via Wi-Fi.

---

## 🏗️ System Architecture

The server splits tasks between a main control intercept thread and an independent pool of concurrent workers:

1. **Main Loop:** Initializes the socket, runs database schema checks, binds to port `8080`, and runs an infinite event monitoring execution loop (`accept()`).
2. **Worker Thread:** Instantly spun up upon a connection event. Parses incoming text bytes, directs routing logic based on the HTTP verb (`GET`/`POST`), interacts with files/SQL, compiles structural HTTP headers, flushes bytes down the wire, and cleanly shuts the connection down.

---

## 📁 File Structure

```text
├── server.py          # Core multi-threaded server application logic & SQL initialization
├── database.db        # SQLite database file (Automatically generated on runtime)
└── public/            # Dedicated root directory containing static asset web views
    ├── index.html     # Client registration user interface markup
    └── style.css      # Core style formatting template sheets
