import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from src.brain import Brain


HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NOVAX AI</title>
  <style>
    :root {
      --bg: #0B1120;
      --secondary-bg: #111827;
      --cards: #1F2937;
      --primary-accent: #3B82F6;
      --secondary-accent: #06B6D4;
      --success: #22C55E;
      --warning: #F59E0B;
      --error: #EF4444;
      --text: #F8FAFC;
      --secondary-text: #94A3B8;
    }

    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, rgba(6, 182, 212, 0.15), transparent 30%), var(--bg);
      color: var(--text);
    }

    .app-shell {
      display: grid;
      grid-template-columns: 320px 1fr;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }

    .sidebar {
      background: linear-gradient(180deg, rgba(17,24,39,0.98), rgba(15,23,42,0.95));
      border-right: 1px solid rgba(148, 163, 184, 0.16);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      height: 100vh;
      overflow-y: auto;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 700;
      letter-spacing: 0.01em;
    }

    .brand-badge {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--primary-accent), var(--secondary-accent));
      display: grid;
      place-items: center;
      font-size: 1.1rem;
    }

    .panel-card {
      background: rgba(31, 41, 55, 0.72);
      border: 1px solid rgba(148, 163, 184, 0.16);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 20px 40px rgba(2, 6, 23, 0.2);
    }

    .panel-card h3 {
      margin: 0 0 10px;
      font-size: 0.95rem;
      color: var(--text);
    }

    .panel-card p {
      margin: 0;
      color: var(--secondary-text);
      line-height: 1.5;
      font-size: 0.94rem;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .chip {
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(59, 130, 246, 0.16);
      color: #dbeafe;
      font-size: 0.82rem;
      border: 1px solid rgba(59,130,246,0.22);
    }

    .chat-panel {
      display: flex;
      flex-direction: column;
      padding: 20px;
      gap: 14px;
      height: 100vh;
      min-height: 0;
      overflow: hidden;
      box-sizing: border-box;
    }

    .chat-header {
      flex-shrink: 0;
      background: rgba(17,24,39,0.9);
      border: 1px solid rgba(148,163,184,0.16);
      border-radius: 20px;
      padding: 14px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 12px 30px rgba(2,6,23,0.2);
    }

    .chat-header h2 { margin: 0; font-size: 1.1rem; }
    .chat-header .status { color: var(--secondary-text); font-size: 0.92rem; }

    .messages {
      flex: 1;
      background: rgba(17,24,39,0.92);
      border: 1px solid rgba(148,163,184,0.16);
      border-radius: 24px;
      padding: 18px;
      overflow-y: auto;
      scroll-behavior: smooth;
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: 0;
    }

    .bubble {
      max-width: 78%;
      padding: 12px 14px;
      border-radius: 16px;
      line-height: 1.5;
      font-size: 0.97rem;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
      word-break: break-word;
    }

    .bubble.user {
      align-self: flex-end;
      background: linear-gradient(135deg, var(--primary-accent), #2563eb);
      color: white;
      border-bottom-right-radius: 6px;
    }

    .bubble.ai {
      align-self: flex-start;
      background: rgba(31, 41, 55, 0.92);
      color: var(--text);
      border-bottom-left-radius: 6px;
      border: 1px solid rgba(148,163,184,0.15);
    }

    .bubble a {
      color: #38bdf8;
      text-decoration: underline;
      text-underline-offset: 3px;
      font-weight: 500;
      word-break: break-all;
    }
    .bubble a:hover {
      color: #7dd3fc;
    }

    .composer {
      flex-shrink: 0;
      display: flex;
      gap: 10px;
      padding: 14px;
      background: rgba(17,24,39,0.95);
      border: 1px solid rgba(148,163,184,0.16);
      border-radius: 20px;
      box-shadow: 0 12px 30px rgba(2,6,23,0.2);
    }

    .composer input {
      flex: 1;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--text);
      font-size: 0.98rem;
    }

    .composer input::placeholder { color: var(--secondary-text); }

    .composer button {
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      background: linear-gradient(135deg, var(--primary-accent), var(--secondary-accent));
      color: white;
      font-weight: 700;
      cursor: pointer;
    }

    .composer button:hover { filter: brightness(1.05); }

    .typing {
      color: var(--secondary-text);
      font-style: italic;
      font-size: 0.9rem;
      padding-left: 4px;
    }

    @media (max-width: 900px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid rgba(148,163,184,0.16); }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-badge">N</div>
        <div>
          <div>NOVAX AI</div>
          <div style="color: var(--secondary-text); font-size: 0.9rem;">Your adaptive assistant</div>
        </div>
      </div>

      <div class="panel-card">
        <h3>What NOVAX can do</h3>
        <p>Chat naturally, remember details, and stay helpful even in offline mode.</p>
        <div class="chip-row">
          <span class="chip">Smart chat</span>
          <span class="chip">Memory</span>
          <span class="chip">Fast replies</span>
        </div>
      </div>

      <div class="panel-card">
        <h3>Try a prompt</h3>
        <p>Ask for help, tell it your name, or start a conversation.</p>
        <div class="chip-row">
          <span class="chip">Remember my name is Alex</span>
          <span class="chip">Help me write code</span>
          <span class="chip">Summarize this idea</span>
        </div>
      </div>
    </aside>

    <main class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>Nova conversation</h2>
          <div class="status">Online • polished dark theme • memory enabled</div>
        </div>
        <div style="color: var(--success); font-weight: 700;">● Ready</div>
      </header>

      <section class="messages" id="messages">
        <div class="bubble ai">Hello! I’m NOVAX-AI. I can chat naturally, remember details, and help you with everyday tasks.</div>
      </section>

      <form class="composer" id="chat-form">
        <input id="message-input" placeholder="Message NOVAX..." autocomplete="off" />
        <button type="submit">Send</button>
      </form>
    </main>
  </div>

  <script>
    const messages = document.getElementById('messages');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');

    function formatMarkdown(text) {
      if (!text) return '';
      // Escape basic HTML
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Convert Markdown links: [Link Text](https://...)
      html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, function(match, label, url) {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
      });

      // Convert raw unformatted URLs into clickable links: https://...
      html = html.replace(/(^|[^"'>])(https?:\/\/[^\s<)]+)/g, function(match, prefix, url) {
        return `${prefix}<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });

      // Line breaks
      html = html.replace(/\n/g, '<br>');
      return html;
    }

    function scrollToBottom() {
      requestAnimationFrame(() => {
        messages.scrollTo({
          top: messages.scrollHeight,
          behavior: 'smooth'
        });
      });
    }

    function appendBubble(role, text) {
      const bubble = document.createElement('div');
      bubble.className = `bubble ${role}`;
      if (role === 'ai') {
        bubble.innerHTML = formatMarkdown(text);
      } else {
        bubble.textContent = text;
      }
      messages.appendChild(bubble);
      scrollToBottom();
    }

    function showTyping() {
      const typing = document.createElement('div');
      typing.id = 'typing';
      typing.className = 'typing';
      typing.textContent = 'NOVAX is thinking...';
      messages.appendChild(typing);
      scrollToBottom();
    }

    function hideTyping() {
      const typing = document.getElementById('typing');
      if (typing) typing.remove();
      scrollToBottom();
    }
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        appendBubble('user', text);
        input.value = '';
        showTyping();

        try {
          const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
          });

          const data = await response.json();
          hideTyping();
          appendBubble('ai', data.reply || 'No reply returned.');
        } catch (error) {
          hideTyping();
          appendBubble('ai', 'Sorry, I could not reach the assistant right now.');
        }
      });
    </script>
  </body>
</html>
"""


class NOVAXRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return

        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self._send_json({"error": "not found"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, status=400)
            return

        message = (data.get("message") or "").strip()
        if not message:
            self._send_json({"error": "message is required"}, status=400)
            return

        response = self.server.brain.get_response(message)
        self._send_json({"reply": response})

    def log_message(self, format, *args):
        return

    def _send_html(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class NOVAXServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.brain = Brain()


def run_server(host="127.0.0.1", port=None):
    port = port or int(os.environ.get("PORT", "8000"))
    server = NOVAXServer((host, port), NOVAXRequestHandler)
    print(f"NOVAX web server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NOVAX server...")
    finally:
        server.server_close()
