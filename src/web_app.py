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
  <meta name="referrer" content="no-referrer" />
  <title>NOVAX AI - Deep Space</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --novax-bg: #080B14;
      --novax-sidebar: #0D1220;
      --novax-surface: #111827;
      --novax-surface-secondary: #151C2B;
      --novax-border: #1E293B;
      --novax-primary: #6366F1;
      --novax-primary-hover: #818CF8;
      --novax-primary-active: #4F46E5;
      --novax-secondary: #8B5CF6;
      --novax-cyan: #22D3EE;
      --novax-text: #F8FAFC;
      --novax-text-secondary: #CBD5E1;
      --novax-muted: #94A3B8;
      --novax-disabled: #64748B;
      --novax-success: #22C55E;
      --novax-error: #EF4444;
      --novax-bubble-user: #1A1733;
      --novax-bubble-user-border: rgba(99, 102, 241, 0.30);
      --novax-nav-active-bg: rgba(99, 102, 241, 0.15);
      --novax-nav-active-border: rgba(99, 102, 241, 0.35);
      --novax-nav-active-icon: #818CF8;
    }

    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background-color: var(--novax-bg);
      background-image: 
        radial-gradient(circle at 60% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 20% 80%, rgba(34, 211, 238, 0.04) 0%, transparent 40%),
        radial-gradient(rgba(248, 250, 252, 0.08) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 48px 48px;
      color: var(--novax-text);
    }

    .app-shell {
      display: grid;
      grid-template-columns: 280px 1fr;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }

    /* Sidebar */
    .sidebar {
      background: var(--novax-sidebar);
      border-right: 1px solid var(--novax-border);
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow-y: auto;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 50;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 6px 20px 6px;
      border-bottom: 1px solid rgba(30, 41, 59, 0.8);
      margin-bottom: 20px;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--novax-primary), var(--novax-secondary));
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 1.1rem;
      color: #ffffff;
      box-shadow: 0 0 16px rgba(99, 102, 241, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .brand-info {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-weight: 700;
      font-size: 1.05rem;
      letter-spacing: 0.08em;
      color: var(--novax-text);
    }

    .brand-subtitle {
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      color: var(--novax-muted);
      margin-top: 1px;
    }

    /* Navigation */
    .nav-section {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 0.9rem;
      font-weight: 500;
      color: var(--novax-muted);
      background: transparent;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.18s ease;
      text-decoration: none;
    }

    .nav-item svg {
      width: 18px;
      height: 18px;
      stroke: var(--novax-disabled);
      transition: stroke 0.18s ease;
      flex-shrink: 0;
    }

    .nav-item:hover {
      background: rgba(99, 102, 241, 0.08);
      color: var(--novax-text);
    }

    .nav-item:hover svg {
      stroke: var(--novax-primary-hover);
    }

    .nav-item.active {
      background: var(--novax-nav-active-bg);
      border-color: var(--novax-nav-active-border);
      color: var(--novax-text);
      font-weight: 600;
    }

    .nav-item.active svg {
      stroke: var(--novax-nav-active-icon);
    }

    .new-chat-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 11px 16px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--novax-primary), #4F46E5);
      color: #ffffff;
      font-weight: 600;
      font-size: 0.9rem;
      border: 1px solid rgba(255, 255, 255, 0.12);
      cursor: pointer;
      margin-bottom: 16px;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25);
      transition: all 0.2s ease;
    }

    .new-chat-btn:hover {
      background: linear-gradient(135deg, var(--novax-primary-hover), var(--novax-primary));
      box-shadow: 0 6px 18px rgba(99, 102, 241, 0.38);
    }

    /* User Profile */
    .user-profile {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-top: 1px solid var(--novax-border);
      margin-top: 16px;
      background: rgba(17, 24, 39, 0.5);
      border-radius: 12px;
    }

    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      display: grid;
      place-items: center;
      font-weight: 600;
      font-size: 0.88rem;
      color: var(--novax-cyan);
    }

    .user-info {
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .user-name {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--novax-text);
    }

    .user-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.75rem;
      color: var(--novax-muted);
    }

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--novax-success);
      box-shadow: 0 0 6px var(--novax-success);
    }

    /* Main Chat Panel */
    .chat-panel {
      display: flex;
      flex-direction: column;
      height: 100vh;
      min-height: 0;
      overflow: hidden;
      position: relative;
    }

    /* Header */
    .chat-header {
      flex-shrink: 0;
      background: rgba(13, 18, 32, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--novax-border);
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 20;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .mobile-menu-btn {
      display: none;
      background: transparent;
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
      padding: 6px;
      border-radius: 8px;
      cursor: pointer;
    }

    .header-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--novax-text);
    }

    .header-status {
      font-size: 0.8rem;
      color: var(--novax-muted);
      margin-top: 1px;
    }

    .header-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid rgba(34, 197, 94, 0.25);
      color: var(--novax-success);
      font-size: 0.78rem;
      font-weight: 600;
    }

    /* Messages List */
    .messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      scroll-behavior: smooth;
      display: flex;
      flex-direction: column;
      gap: 18px;
      min-height: 0;
      max-width: 960px;
      width: 100%;
      margin: 0 auto;
    }

    /* Welcome Hero Card */
    .welcome-card {
      text-align: center;
      padding: 40px 20px 20px 20px;
      margin-bottom: 10px;
    }

    .welcome-heading {
      font-size: 1.8rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin: 0 0 8px 0;
      background: linear-gradient(135deg, var(--novax-text) 30%, var(--novax-primary-hover) 70%, var(--novax-cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .welcome-subtitle {
      font-size: 0.95rem;
      color: var(--novax-muted);
      margin: 0;
    }

    /* Message Bubbles */
    .message-row {
      display: flex;
      gap: 12px;
      max-width: 85%;
    }

    .message-row.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message-row.ai {
      align-self: flex-start;
    }

    .msg-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 0.8rem;
      font-weight: 700;
      flex-shrink: 0;
      margin-top: 4px;
    }

    .message-row.ai .msg-avatar {
      background: linear-gradient(135deg, var(--novax-primary), var(--novax-secondary));
      color: #ffffff;
      box-shadow: 0 0 10px rgba(99, 102, 241, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .message-row.user .msg-avatar {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      color: var(--novax-cyan);
    }

    .bubble {
      padding: 13px 16px;
      border-radius: 14px;
      line-height: 1.55;
      font-size: 0.94rem;
      word-break: break-word;
      position: relative;
    }

    .bubble.user {
      background: var(--novax-bubble-user);
      border: 1px solid var(--novax-bubble-user-border);
      color: var(--novax-text);
      border-top-right-radius: 4px;
    }

    .bubble.ai {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
      border-top-left-radius: 4px;
    }

    .bubble a {
      color: var(--novax-cyan);
      text-decoration: underline;
      text-underline-offset: 3px;
      font-weight: 500;
    }

    .bubble a:hover {
      color: var(--novax-primary-hover);
    }

    .bubble img.chat-img {
      max-width: 100%;
      max-height: 300px;
      border-radius: 12px;
      margin: 10px 0;
      display: block;
      object-fit: cover;
      border: 1px solid var(--novax-border);
      cursor: pointer;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
      transition: transform 0.2s ease;
    }

    .bubble img.chat-img:hover {
      transform: scale(1.01);
    }

    .typing-indicator {
      color: var(--novax-muted);
      font-style: italic;
      font-size: 0.86rem;
      padding: 8px 14px;
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 12px;
      align-self: flex-start;
    }

    /* Bottom Input Section */
    .chat-bottom {
      flex-shrink: 0;
      padding: 14px 24px 20px 24px;
      max-width: 960px;
      width: 100%;
      margin: 0 auto;
      box-sizing: border-box;
    }

    /* Suggested Prompts Chips */
    .suggested-prompts {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }

    .suggestion-chip {
      padding: 7px 13px;
      border-radius: 999px;
      background: rgba(17, 24, 39, 0.7);
      border: 1px solid var(--novax-border);
      color: var(--novax-muted);
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .suggestion-chip:hover {
      background: rgba(99, 102, 241, 0.12);
      border-color: var(--novax-primary-hover);
      color: var(--novax-text);
      transform: translateY(-1px);
    }

    /* Floating Composer Form */
    .composer {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 8px 8px 16px;
      background: var(--novax-surface);
      border: 1px solid #334155;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      transition: all 0.2s ease;
    }

    .composer:focus-within {
      border-color: var(--novax-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25), 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .composer input {
      flex: 1;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--novax-text);
      font-size: 0.95rem;
      font-family: inherit;
    }

    .composer input::placeholder {
      color: var(--novax-disabled);
    }

    .send-btn {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--novax-primary);
      border: 0;
      color: #ffffff;
      display: grid;
      place-items: center;
      cursor: pointer;
      transition: all 0.18s ease;
      flex-shrink: 0;
    }

    .send-btn:hover {
      background: var(--novax-primary-hover);
    }

    .send-btn:active {
      background: var(--novax-primary-active);
    }

    .send-btn svg {
      width: 18px;
      height: 18px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .app-shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 260px;
        transform: translateX(-100%);
      }
      .sidebar.open {
        transform: translateX(0);
      }
      .mobile-menu-btn {
        display: block;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <div class="brand-logo">N</div>
        <div class="brand-info">
          <span class="brand-title">NOVAX</span>
          <span class="brand-subtitle">AI PERSONAL AGENT</span>
        </div>
      </div>

      <button class="new-chat-btn" onclick="clearMessages()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        New Chat
      </button>

      <nav class="nav-section">
        <a class="nav-item active" href="#">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Conversations
        </a>
        <a class="nav-item" href="#">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          Memory
        </a>
        <a class="nav-item" href="#">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          Projects
        </a>
        <a class="nav-item" href="#">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
          Tools
        </a>
        <a class="nav-item" href="#">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Settings
        </a>
      </nav>

      <div class="user-profile">
        <div class="avatar">S</div>
        <div class="user-info">
          <span class="user-name">Sriram</span>
          <span class="user-status">
            <span class="status-dot"></span> Online
          </span>
        </div>
      </div>
    </aside>

    <!-- Main Chat Panel -->
    <main class="chat-panel">
      <header class="chat-header">
        <div class="header-left">
          <button class="mobile-menu-btn" onclick="toggleSidebar()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          </button>
          <div>
            <div class="header-title">NOVAX Intelligence</div>
            <div class="header-status">Deep Space v2.0 • Online • Memory Active</div>
          </div>
        </div>
        <div class="header-badge">● Ready</div>
      </header>

      <section class="messages" id="messages">
        <div class="welcome-card">
          <h1 class="welcome-heading">Welcome to NOVAX</h1>
          <p class="welcome-subtitle">Your AI assistant is ready to help you.</p>
        </div>
        <div class="message-row ai">
          <div class="msg-avatar">N</div>
          <div class="bubble ai">Hello! I’m NOVAX-AI, your personal agent. How can I assist you today?</div>
        </div>
      </section>

      <div class="chat-bottom">
        <div class="suggested-prompts">
          <button class="suggestion-chip" onclick="sendSuggested('Explain quantum computing')">Explain quantum computing</button>
          <button class="suggestion-chip" onclick="sendSuggested('Help me with Python')">Help me with Python</button>
          <button class="suggestion-chip" onclick="sendSuggested('Summarize this idea')">Summarize this idea</button>
          <button class="suggestion-chip" onclick="sendSuggested('Write some code')">Write some code</button>
        </div>

        <form class="composer" id="chat-form">
          <input id="message-input" placeholder="Ask NOVAX anything..." autocomplete="off" />
          <button type="submit" class="send-btn" title="Send message">
            <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </form>
      </div>
    </main>
  </div>

  <script>
    const messages = document.getElementById('messages');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const sidebar = document.getElementById('sidebar');

    function toggleSidebar() {
      sidebar.classList.toggle('open');
    }

    function clearMessages() {
      messages.innerHTML = `
        <div class="welcome-card">
          <h1 class="welcome-heading">Welcome to NOVAX</h1>
          <p class="welcome-subtitle">Your AI assistant is ready to help you.</p>
        </div>
        <div class="message-row ai">
          <div class="msg-avatar">N</div>
          <div class="bubble ai">Hello! I’m NOVAX-AI, your personal agent. How can I assist you today?</div>
        </div>
      `;
    }

    function formatMarkdown(text) {
      if (!text) return '';
      text = text.replace(/https?:\/\/maps\.app\.goo\.gl\/[^\s\)]+/g, 'https://www.google.com/maps');

      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Convert Markdown Images: ![alt](url)
      html = html.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s\)]+)\)/g, function(match, alt, url) {
        const fallbackUrl = 'https://image.pollinations.ai/prompt/' + encodeURIComponent(alt || 'photo') + '?width=600&height=400&nologo=true';
        return `<img src="${url}" alt="${alt}" class="chat-img" onclick="window.open('${url}', '_blank')" onerror="this.onerror=null; this.src='${fallbackUrl}';" />`;
      });

      // Convert Markdown links: [Link Text](https://...)
      html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, function(match, label, url) {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
      });

      // Convert raw unformatted URLs into clickable links
      html = html.replace(/(^|[^"'>=])(https?:\/\/[^\s<)]+)/g, function(match, prefix, url) {
        return `${prefix}<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });

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
      const row = document.createElement('div');
      row.className = `message-row ${role}`;
      
      const avatar = document.createElement('div');
      avatar.className = 'msg-avatar';
      avatar.textContent = role === 'ai' ? 'N' : 'S';

      const bubble = document.createElement('div');
      bubble.className = `bubble ${role}`;

      if (role === 'ai') {
        bubble.innerHTML = formatMarkdown(text);
      } else {
        bubble.textContent = text;
      }

      row.appendChild(avatar);
      row.appendChild(bubble);
      messages.appendChild(row);
      scrollToBottom();
    }

    function showTyping() {
      const typing = document.createElement('div');
      typing.id = 'typing';
      typing.className = 'typing-indicator';
      typing.textContent = 'NOVAX is processing...';
      messages.appendChild(typing);
      scrollToBottom();
    }

    function hideTyping() {
      const typing = document.getElementById('typing');
      if (typing) typing.remove();
      scrollToBottom();
    }

    function sendSuggested(promptText) {
      input.value = promptText;
      form.dispatchEvent(new Event('submit'));
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
