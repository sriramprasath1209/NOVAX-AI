import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from src.brain import Brain
from src.db import db
from src import auth


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="no-referrer" />
  <title>NOVAX-AI — Personal AI Workspace</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --novax-bg: #080B14;
      --novax-sidebar: #0D1220;
      --novax-surface: #111827;
      --novax-surface-secondary: #151C2B;
      --novax-border: #1E293B;
      --novax-border-light: rgba(255, 255, 255, 0.08);
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
      --novax-nav-active-bg: rgba(99, 102, 241, 0.14);
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
        radial-gradient(circle at 75% 15%, rgba(99, 102, 241, 0.09) 0%, transparent 45%),
        radial-gradient(circle at 20% 85%, rgba(34, 211, 238, 0.05) 0%, transparent 40%),
        radial-gradient(rgba(248, 250, 252, 0.05) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 40px 40px;
      color: var(--novax-text);
      -webkit-font-smoothing: antialiased;
    }

    .view-container {
      width: 100vw;
      height: 100vh;
      display: none;
    }
    .view-container.active {
      display: flex;
    }

    /* Auth Centered Cards */
    .auth-wrapper {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      overflow-y: auto;
    }

    .auth-brand {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 24px;
      text-align: center;
    }

    .auth-logo {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      background: var(--novax-sidebar);
      display: grid;
      place-items: center;
      box-shadow: 0 0 24px rgba(99, 102, 241, 0.4);
      border: 1px solid rgba(99, 102, 241, 0.4);
      margin-bottom: 12px;
    }

    .auth-title {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: 2px;
      background: linear-gradient(135deg, #FFF 0%, var(--novax-text-secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }

    .auth-subtitle {
      font-size: 12px;
      color: var(--novax-cyan);
      letter-spacing: 1px;
      margin-top: 4px;
      font-weight: 600;
    }

    .auth-card {
      width: 100%;
      max-width: 420px;
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 20px;
      padding: 32px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(99, 102, 241, 0.1);
      backdrop-filter: blur(10px);
    }

    .auth-card h2 {
      margin: 0 0 6px 0;
      font-size: 20px;
      font-weight: 700;
      color: var(--novax-text);
    }

    .auth-card p.card-desc {
      margin: 0 0 24px 0;
      font-size: 14px;
      color: var(--novax-muted);
    }

    .auth-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .form-group label {
      font-size: 13px;
      font-weight: 500;
      color: var(--novax-text-secondary);
    }

    .form-control {
      width: 100%;
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      border-radius: 10px;
      padding: 12px 14px;
      color: var(--novax-text);
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }

    .form-control:focus {
      border-color: var(--novax-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    .btn-primary {
      width: 100%;
      background: linear-gradient(135deg, var(--novax-primary) 0%, var(--novax-secondary) 100%);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 13px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .btn-primary:hover {
      opacity: 0.95;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
    }

    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .auth-divider {
      display: flex;
      align-items: center;
      margin: 20px 0;
      color: var(--novax-muted);
      font-size: 12px;
    }

    .auth-divider::before, .auth-divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: var(--novax-border);
    }

    .auth-divider span {
      padding: 0 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .btn-google {
      width: 100%;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--novax-border);
      border-radius: 10px;
      padding: 12px;
      color: var(--novax-text);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      transition: all 0.2s ease;
    }

    .btn-google:hover {
      background: rgba(255, 255, 255, 0.09);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .auth-footer {
      margin-top: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--novax-muted);
    }

    .auth-footer a {
      color: var(--novax-cyan);
      text-decoration: none;
      font-weight: 600;
    }

    .auth-footer a:hover {
      text-decoration: underline;
    }

    .error-banner {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #FCA5A5;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 13px;
      margin-bottom: 16px;
      display: none;
    }

    /* App Shell / Dashboard */
    .app-shell {
      display: grid;
      grid-template-columns: 280px 1fr;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }

    .sidebar {
      background: var(--novax-sidebar);
      border-right: 1px solid var(--novax-border);
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow-y: auto;
      z-index: 50;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 6px 4px 18px 4px;
      border-bottom: 1px solid rgba(30, 41, 59, 0.8);
      margin-bottom: 16px;
    }

    .brand-logo {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: rgba(13, 18, 32, 0.9);
      display: grid;
      place-items: center;
      box-shadow: 0 0 16px rgba(99, 102, 241, 0.35);
      border: 1px solid rgba(99, 102, 241, 0.35);
    }

    .brand-title {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: 1.5px;
      background: linear-gradient(135deg, #FFF 0%, var(--novax-text-secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-subtitle {
      font-size: 10px;
      color: var(--novax-cyan);
      letter-spacing: 1px;
      font-weight: 600;
    }

    .nav-section {
      margin-bottom: 20px;
    }

    .nav-section-title {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--novax-muted);
      padding: 0 10px 8px 10px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      border-radius: 10px;
      color: var(--novax-text-secondary);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-bottom: 4px;
      text-decoration: none;
    }

    .nav-item:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--novax-text);
    }

    .nav-item.active {
      background: var(--novax-nav-active-bg);
      border: 1px solid var(--novax-nav-active-border);
      color: var(--novax-text);
    }

    .btn-new-chat {
      background: linear-gradient(135deg, var(--novax-primary) 0%, var(--novax-secondary) 100%);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 12px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    .user-profile-bar {
      margin-top: auto;
      padding-top: 16px;
      border-top: 1px solid var(--novax-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .user-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--novax-primary) 0%, var(--novax-cyan) 100%);
      display: grid;
      place-items: center;
      font-weight: 700;
      font-size: 14px;
      color: white;
    }

    .user-details {
      display: flex;
      flex-direction: column;
    }

    .user-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--novax-text);
    }

    .user-status {
      font-size: 11px;
      color: var(--novax-success);
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      background: var(--novax-success);
      border-radius: 50%;
      display: inline-block;
    }

    .btn-logout {
      background: transparent;
      border: 1px solid var(--novax-border);
      color: var(--novax-muted);
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-logout:hover {
      background: rgba(239, 68, 68, 0.15);
      border-color: rgba(239, 68, 68, 0.4);
      color: #FCA5A5;
    }

    /* Main Workspace Panels */
    .main-workspace {
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      background: rgba(8, 11, 20, 0.6);
    }

    .workspace-header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--novax-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(13, 18, 32, 0.6);
      backdrop-filter: blur(12px);
    }

    .workspace-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--novax-text);
    }

    .panel-view {
      flex: 1;
      display: none;
      flex-direction: column;
      height: calc(100vh - 65px);
      overflow-y: auto;
      padding: 24px;
    }

    .panel-view.active {
      display: flex;
    }

    /* Chat View */
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .chat-bubble {
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
    }

    .chat-bubble.user {
      align-self: flex-end;
      background: var(--novax-bubble-user);
      border: 1px solid var(--novax-bubble-user-border);
      color: var(--novax-text);
      border-bottom-right-radius: 4px;
    }

    .chat-bubble.assistant {
      align-self: flex-start;
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
      border-bottom-left-radius: 4px;
    }

    .chat-input-bar {
      padding: 16px 24px;
      border-top: 1px solid var(--novax-border);
      display: flex;
      gap: 12px;
      background: var(--novax-sidebar);
    }

    .chat-input {
      flex: 1;
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 12px;
      padding: 14px 16px;
      color: var(--novax-text);
      font-size: 14px;
      outline: none;
    }

    .chat-input:focus {
      border-color: var(--novax-primary);
    }

    .btn-send {
      background: var(--novax-primary);
      color: white;
      border: none;
      border-radius: 12px;
      padding: 0 20px;
      font-weight: 600;
      cursor: pointer;
    }

    /* Cards & Lists for Memory, Projects, Tasks */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }

    .data-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
    }

    .data-card h3 {
      margin: 0 0 8px 0;
      font-size: 16px;
      color: var(--novax-cyan);
    }

    .data-card p {
      margin: 0;
      font-size: 13px;
      color: var(--novax-text-secondary);
    }
  </style>
</head>
<body>

  <!-- LOGIN VIEW -->
  <div id="login-view" class="view-container active">
    <div class="auth-wrapper">
      <div class="auth-brand">
        <div class="auth-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1 class="auth-title">NOVAX</h1>
        <div class="auth-subtitle">AI PERSONAL AGENT</div>
        <div style="font-size: 13px; color: var(--novax-muted); margin-top: 6px;">Your intelligent personal assistant.</div>
      </div>

      <div class="auth-card">
        <h2>Welcome back</h2>
        <p class="card-desc">Sign in to continue to NOVAX</p>

        <div id="login-error" class="error-banner"></div>

        <form class="auth-form" onsubmit="handleLogin(event)">
          <div class="form-group">
            <label for="login-email">Email address</label>
            <input type="email" id="login-email" class="form-control" placeholder="name@example.com" required />
          </div>

          <div class="form-group">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label for="login-password">Password</label>
              <a href="#" onclick="alert('Password recovery is handled via your identity provider.')" style="font-size:12px; color:var(--novax-cyan); text-decoration:none;">Forgot password?</a>
            </div>
            <input type="password" id="login-password" class="form-control" placeholder="••••••••" required />
          </div>

          <button type="submit" id="btn-submit-login" class="btn-primary">
            <span>Sign In</span>
          </button>
        </form>

        <div class="auth-divider">
          <span>or</span>
        </div>

        <button class="btn-google" onclick="handleGoogleLogin()">
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.2 9 5 12 5z"/>
            <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"/>
            <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15s.7 5.3 1.9 7.7l3.7-2.9z"/>
            <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.2-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"/>
          </svg>
          <span>Continue with Google</span>
        </button>

        <div class="auth-footer">
          Don't have an account? <a href="#" onclick="showView('signup-view')">Create account</a>
        </div>
      </div>
    </div>
  </div>

  <!-- SIGNUP VIEW -->
  <div id="signup-view" class="view-container">
    <div class="auth-wrapper">
      <div class="auth-brand">
        <div class="auth-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1 class="auth-title">NOVAX</h1>
        <div class="auth-subtitle">AI PERSONAL AGENT</div>
      </div>

      <div class="auth-card">
        <h2>Create your NOVAX account</h2>
        <p class="card-desc">Start building your personal AI workspace.</p>

        <div id="signup-error" class="error-banner"></div>

        <form class="auth-form" onsubmit="handleSignup(event)">
          <div class="form-group">
            <label for="signup-name">Full Name</label>
            <input type="text" id="signup-name" class="form-control" placeholder="Arun" required />
          </div>

          <div class="form-group">
            <label for="signup-email">Email address</label>
            <input type="email" id="signup-email" class="form-control" placeholder="arun@example.com" required />
          </div>

          <div class="form-group">
            <label for="signup-password">Password</label>
            <input type="password" id="signup-password" class="form-control" placeholder="At least 6 characters" required />
          </div>

          <div class="form-group">
            <label for="signup-confirm-password">Confirm Password</label>
            <input type="password" id="signup-confirm-password" class="form-control" placeholder="Confirm password" required />
          </div>

          <button type="submit" id="btn-submit-signup" class="btn-primary">
            <span>Create account</span>
          </button>
        </form>

        <div class="auth-divider">
          <span>or</span>
        </div>

        <button class="btn-google" onclick="handleGoogleLogin()">
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.2 9 5 12 5z"/>
            <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"/>
            <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15s.7 5.3 1.9 7.7l3.7-2.9z"/>
            <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.2-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"/>
          </svg>
          <span>Continue with Google</span>
        </button>

        <div class="auth-footer">
          Already have an account? <a href="#" onclick="showView('login-view')">Sign in</a>
        </div>
      </div>
    </div>
  </div>

  <!-- AUTHENTICATED APP DASHBOARD -->
  <div id="app-view" class="view-container">
    <div class="app-shell">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">NOVAX</div>
            <div class="brand-subtitle">AI PERSONAL AGENT</div>
          </div>
        </div>

        <button class="btn-new-chat" onclick="showPanel('chat-panel')">
          <span>＋ New Chat</span>
        </button>

        <div class="nav-section">
          <div class="nav-section-title">Workspace</div>
          <div class="nav-item active" onclick="showPanel('chat-panel')">
            <span>◉ Conversations</span>
          </div>
          <div class="nav-item" onclick="showPanel('memory-panel')">
            <span>🧠 Memory</span>
          </div>
          <div class="nav-item" onclick="showPanel('projects-panel')">
            <span>📁 Projects</span>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">Agent Tools</div>
          <div class="nav-item" onclick="alert('Tools section is active.')">
            <span>🛠 Tools</span>
          </div>
          <div class="nav-item" onclick="showPanel('tasks-panel')">
            <span>📋 Tasks</span>
          </div>
          <div class="nav-item" onclick="alert('Automations feature enabled.')">
            <span>🔔 Automations</span>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-item" onclick="alert('Settings view loaded.')">
            <span>⚙ Settings</span>
          </div>
        </div>

        <!-- User Profile Bar -->
        <div class="user-profile-bar">
          <div class="user-info">
            <div id="user-avatar" class="user-avatar">U</div>
            <div class="user-details">
              <div id="user-display-name" class="user-name">User</div>
              <div class="user-status"><span class="status-dot"></span> Online</div>
            </div>
          </div>
          <button class="btn-logout" onclick="handleLogout()">Logout</button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-workspace">
        <div class="workspace-header">
          <div id="workspace-title" class="workspace-title">Personal AI Assistant</div>
        </div>

        <!-- Chat Panel -->
        <div id="chat-panel" class="panel-view active">
          <div id="chat-messages" class="chat-container">
            <div class="chat-bubble assistant">
              Welcome to NOVAX! I am your personal AI assistant. How can I help you today?
            </div>
          </div>
          <div class="chat-input-bar">
            <input type="text" id="user-input" class="chat-input" placeholder="Type your message to NOVAX..." onkeydown="if(event.key==='Enter') sendMessage()" />
            <button class="btn-send" onclick="sendMessage()">Send</button>
          </div>
        </div>

        <!-- Memory Panel -->
        <div id="memory-panel" class="panel-view">
          <h2 style="color:var(--novax-cyan); margin-top:0;">Your Personal Memory Space</h2>
          <p style="color:var(--novax-muted); font-size:14px;">Memories stored here are completely isolated to your personal NOVAX account.</p>
          <div id="memory-grid" class="card-grid"></div>
        </div>

        <!-- Projects Panel -->
        <div id="projects-panel" class="panel-view">
          <h2 style="color:var(--novax-cyan); margin-top:0;">Your Private Projects</h2>
          <p style="color:var(--novax-muted); font-size:14px;">Projects created here belong solely to your account.</p>
          <div id="projects-grid" class="card-grid">
            <div class="data-card">
              <h3>NOVAX-AI Personal Workspace</h3>
              <p>Active project workspace initialized for your authenticated profile.</p>
            </div>
          </div>
        </div>

        <!-- Tasks Panel -->
        <div id="tasks-panel" class="panel-view">
          <h2 style="color:var(--novax-cyan); margin-top:0;">Your Personal Tasks</h2>
          <p style="color:var(--novax-muted); font-size:14px;">Manage your daily priorities safely.</p>
          <div id="tasks-grid" class="card-grid">
            <div class="data-card">
              <h3>Personal AI Setup</h3>
              <p>Configure personal preferences and memories in NOVAX.</p>
            </div>
          </div>
        </div>

      </main>
    </div>
  </div>

  <script>
    let currentUser = null;

    function showView(viewId) {
      document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
      const target = document.getElementById(viewId);
      if (target) target.classList.add('active');
    }

    function showPanel(panelId) {
      document.querySelectorAll('.panel-view').forEach(el => el.classList.remove('active'));
      const target = document.getElementById(panelId);
      if (target) target.classList.add('active');
      if (panelId === 'memory-panel') loadMemories();
    }

    function showError(elementId, msg) {
      const el = document.getElementById(elementId);
      if (el) {
        el.innerText = msg;
        el.style.display = 'block';
      }
    }

    function hideError(elementId) {
      const el = document.getElementById(elementId);
      if (el) el.style.display = 'none';
    }

    async function checkAuth() {
      try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated && data.user) {
          currentUser = data.user;
          updateUserProfileUI();
          showView('app-view');
        } else {
          showView('login-view');
        }
      } catch (e) {
        showView('login-view');
      }
    }

    function updateUserProfileUI() {
      if (!currentUser) return;
      document.getElementById('user-display-name').innerText = currentUser.name || 'User';
      document.getElementById('user-avatar').innerText = (currentUser.name || 'U').charAt(0).toUpperCase();
    }

    async function handleLogin(e) {
      e.preventDefault();
      hideError('login-error');
      const email = document.getElementById('login-email').value;
      const password = document.getElementById('login-password').value;
      const btn = document.getElementById('btn-submit-login');

      btn.disabled = true;
      btn.innerText = 'Signing in...';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          currentUser = data.user;
          updateUserProfileUI();
          showView('app-view');
        } else {
          showError('login-error', data.error || 'Invalid email or password.');
        }
      } catch (err) {
        showError('login-error', 'Unable to sign in. Please try again.');
      } finally {
        btn.disabled = false;
        btn.innerText = 'Sign In';
      }
    }

    async function handleSignup(e) {
      e.preventDefault();
      hideError('signup-error');
      const name = document.getElementById('signup-name').value;
      const email = document.getElementById('signup-email').value;
      const password = document.getElementById('signup-password').value;
      const confirmPassword = document.getElementById('signup-confirm-password').value;
      const btn = document.getElementById('btn-submit-signup');

      if (password !== confirmPassword) {
        showError('signup-error', 'Passwords do not match.');
        return;
      }

      btn.disabled = true;
      btn.innerText = 'Creating account...';

      try {
        const res = await fetch('/api/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          currentUser = data.user;
          updateUserProfileUI();
          showView('app-view');
        } else {
          showError('signup-error', data.error || 'Unable to create account.');
        }
      } catch (err) {
        showError('signup-error', 'Unable to sign up. Please try again.');
      } finally {
        btn.disabled = false;
        btn.innerText = 'Create account';
      }
    }

    async function handleGoogleLogin() {
      hideError('login-error');
      hideError('signup-error');
      try {
        const res = await fetch('/api/auth/google');
        const data = await res.json();
        if (data.url) {
          window.location.href = data.url;
        } else {
          const msg = 'Google Auth is not configured. Please add GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET to your .env file.';
          showError('login-error', msg);
          showError('signup-error', msg);
        }
      } catch (e) {
        showError('login-error', 'Google Authentication failed to launch.');
        showError('signup-error', 'Google Authentication failed to launch.');
      }
    }

    async function handleLogout() {
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch (e) {}
      currentUser = null;
      showView('login-view');
    }

    function formatMessageText(text) {
      if (!text) return '';

      // Escape raw HTML tags first
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Convert Markdown links: [Title](https://...) -> clickable <a> tag
      html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, function(match, label, url) {
        return `<a href="${url}" target="_blank" rel="noopener" style="color: var(--novax-cyan); font-weight: 600; text-decoration: underline; word-break: break-all;">${label}</a>`;
      });

      // Convert standalone URLs: https://... -> clickable <a> tag
      html = html.replace(/(^|[\s(])(https?:\/\/[^\s\)]+)/g, function(match, space, url) {
        if (match.includes('href=')) return match;
        return `${space}<a href="${url}" target="_blank" rel="noopener" style="color: var(--novax-cyan); font-weight: 600; text-decoration: underline; word-break: break-all;">${url}</a>`;
      });

      // Convert bold **text** -> <strong>text</strong>
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

      // Convert newlines -> <br/>
      html = html.replace(/\n/g, '<br/>');

      return html;
    }

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;

      const container = document.getElementById('chat-messages');

      const userBubble = document.createElement('div');
      userBubble.className = 'chat-bubble user';
      userBubble.innerText = text;
      container.appendChild(userBubble);

      input.value = '';
      container.scrollTop = container.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'chat-bubble assistant';
        assistantBubble.innerHTML = formatMessageText(data.reply || 'No response returned.');
        container.appendChild(assistantBubble);
        container.scrollTop = container.scrollHeight;
      } catch (e) {
        const errBubble = document.createElement('div');
        errBubble.className = 'chat-bubble assistant';
        errBubble.innerText = 'Error communicating with NOVAX.';
        container.appendChild(errBubble);
      }
    }

    async function loadMemories() {
      try {
        const res = await fetch('/api/memory');
        const memories = await res.json();
        const grid = document.getElementById('memory-grid');
        grid.innerHTML = '';

        let count = 0;
        for (const [cat, items] of Object.entries(memories)) {
          for (const [key, val] of Object.entries(items)) {
            count++;
            const card = document.createElement('div');
            card.className = 'data-card';
            card.innerHTML = `<h3>${key}</h3><p><strong>${cat.toUpperCase()}:</strong> ${val}</p>`;
            grid.appendChild(card);
          }
        }

        if (count === 0) {
          grid.innerHTML = `<div class="data-card"><p>No personal memories saved yet.</p></div>`;
        }
      } catch (e) {}
    }

    // Initialize Auth state on page load
    window.addEventListener('DOMContentLoaded', checkAuth);
  </script>
</body>
</html>
"""


class NOVAXRequestHandler(BaseHTTPRequestHandler):

    def _get_authenticated_user(self):
        cookie_header = self.headers.get("Cookie", "")
        session_id = None
        if cookie_header:
            cookies = {}
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    cookies[k] = v
            session_id = cookies.get("session_id")

        if not session_id:
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                session_id = auth_header[7:].strip()

        if not session_id:
            return None

        session = auth.validate_session(session_id)
        if not session:
            return None

        return {
            "id": session["user_id"],
            "email": session["email"],
            "name": session["name"],
            "session_id": session_id
        }

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return

        elif parsed.path == "/assets/logo.svg":
            asset_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
            if os.path.exists(asset_path):
                with open(asset_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        elif parsed.path == "/api/auth/me":
            user = self._get_authenticated_user()
            if user:
                self._send_json({"authenticated": True, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}})
            else:
                self._send_json({"authenticated": False})
            return

        elif parsed.path == "/api/auth/google":
            host = self.headers.get("Host", "127.0.0.1:8000")
            redirect_uri = f"http://{host}/api/auth/google/callback"
            url = auth.get_google_auth_url(redirect_uri)
            self._send_json({"url": url})
            return

        elif parsed.path == "/api/auth/google/callback":
            query = parse_qs(parsed.query)
            code = query.get("code", [None])[0]
            host = self.headers.get("Host", "127.0.0.1:8000")
            redirect_uri = f"http://{host}/api/auth/google/callback"

            if not code:
                self._send_json({"error": "Missing code parameter"}, status=400)
                return

            user, err = auth.process_google_callback(code, redirect_uri)
            if err:
                self._send_json({"error": err}, status=400)
                return

            session_id = auth.create_session(user["id"])
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax")
            self.end_headers()
            return

        elif parsed.path == "/api/memory":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            memories = self.server.brain.memory.load_memory(user_id=user["id"])
            self._send_json(memories)
            return

        elif parsed.path == "/api/conversations":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            conversations = db.get_user_conversations(user["id"])
            self._send_json(conversations)
            return

        elif parsed.path == "/api/projects":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            projects = db.get_user_projects(user["id"])
            self._send_json(projects)
            return

        elif parsed.path == "/api/tasks":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            tasks = db.get_user_tasks(user["id"])
            self._send_json(tasks)
            return

        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, status=400)
            return

        # Auth Endpoints (Unprotected)
        if parsed.path == "/api/auth/signup":
            email = data.get("email")
            password = data.get("password")
            name = data.get("name")

            user, err = auth.register_user(email, password, name)
            if err:
                self._send_json({"error": err}, status=400)
                return

            session_id = auth.create_session(user["id"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax")
            res_body = json.dumps({"success": True, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}).encode("utf-8")
            self.send_header("Content-Length", str(len(res_body)))
            self.end_headers()
            self.wfile.write(res_body)
            return

        elif parsed.path == "/api/auth/login":
            email = data.get("email")
            password = data.get("password")

            user, err = auth.login_user(email, password)
            if err:
                self._send_json({"error": err}, status=400)
                return

            session_id = auth.create_session(user["id"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax")
            res_body = json.dumps({"success": True, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}).encode("utf-8")
            self.send_header("Content-Length", str(len(res_body)))
            self.end_headers()
            self.wfile.write(res_body)
            return

        elif parsed.path == "/api/auth/logout":
            user = self._get_authenticated_user()
            if user:
                auth.logout_session(user["session_id"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", "session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
            res_body = json.dumps({"success": True}).encode("utf-8")
            self.send_header("Content-Length", str(len(res_body)))
            self.end_headers()
            self.wfile.write(res_body)
            return

        # Protected Data Endpoints
        user = self._get_authenticated_user()
        if not user:
            self._send_json({"error": "Unauthorized"}, status=401)
            return

        if parsed.path == "/api/chat":
            message = (data.get("message") or "").strip()
            if not message:
                self._send_json({"error": "message is required"}, status=400)
                return

            response = self.server.brain.get_response(message, user_id=user["id"], user_name=user["name"])
            self._send_json({"reply": response})
            return

        elif parsed.path == "/api/memory":
            category = data.get("category")
            key = data.get("key")
            value = data.get("value")
            is_delete = data.get("delete", False)

            if not category or not key:
                self._send_json({"error": "category and key required"}, status=400)
                return

            if is_delete:
                self.server.brain.memory.delete(category, key, user_id=user["id"])
            else:
                self.server.brain.memory.set(category, key, value, user_id=user["id"])

            updated = self.server.brain.memory.load_memory(user_id=user["id"])
            self._send_json({"success": True, "memory": updated})
            return

        elif parsed.path == "/api/clear":
            self.server.brain.conversation.clear(user_id=user["id"])
            self._send_json({"success": True})
            return

        self._send_json({"error": "not found"}, status=404)

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
    allow_reuse_address = True

    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.brain = Brain()


def run_server(host="127.0.0.1", port=None):
    initial_port = port or int(os.environ.get("PORT", "8000"))
    max_tries = 10
    server = None
    actual_port = initial_port

    for i in range(max_tries):
        current_port = initial_port + i
        try:
            server = NOVAXServer((host, current_port), NOVAXRequestHandler)
            actual_port = current_port
            break
        except OSError as e:
            if e.errno == 48 and port is None:  # Address already in use
                continue
            raise e

    if not server:
        print(f"Could not bind to any port starting from {initial_port}.")
        return

    print(f"NOVAX web server running at http://{host}:{actual_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NOVAX server...")
    finally:
        server.server_close()
