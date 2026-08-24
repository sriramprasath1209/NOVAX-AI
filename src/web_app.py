import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from src.brain import Brain


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="no-referrer" />
  <title>NOVAX-AI — Deep Space Command Center</title>
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
      overflow: hidden;
      padding: 3px;
      flex-shrink: 0;
    }

    .brand-logo-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    .brand-info {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-weight: 800;
      font-size: 1.1rem;
      letter-spacing: 0.08em;
      color: var(--novax-text);
      line-height: 1.2;
    }

    .brand-subtitle {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      color: var(--novax-muted);
      margin-top: 2px;
    }

    /* Navigation */
    .new-chat-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 12px 16px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--novax-primary), #4F46E5);
      color: #ffffff;
      font-weight: 600;
      font-size: 0.92rem;
      border: 1px solid rgba(255, 255, 255, 0.15);
      cursor: pointer;
      margin-bottom: 16px;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
      transition: all 0.2s ease;
    }

    .new-chat-btn:hover {
      background: linear-gradient(135deg, var(--novax-primary-hover), var(--novax-primary));
      box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
      transform: translateY(-1px);
    }

    .new-chat-btn:active {
      transform: translateY(0);
    }

    .nav-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 16px;
    }

    .nav-section-title {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: var(--novax-disabled);
      padding: 12px 12px 6px 12px;
      text-transform: uppercase;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 500;
      color: var(--novax-muted);
      background: transparent;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.18s ease;
      text-decoration: none;
    }

    .nav-item-icon {
      font-size: 1.05rem;
      display: grid;
      place-items: center;
      width: 20px;
      height: 20px;
      line-height: 1;
    }

    .nav-item:hover {
      background: rgba(99, 102, 241, 0.08);
      color: var(--novax-text);
    }

    .nav-item.active {
      background: var(--novax-nav-active-bg);
      border-color: var(--novax-nav-active-border);
      color: var(--novax-text);
      font-weight: 600;
    }

    .nav-item.active .nav-item-icon {
      color: var(--novax-cyan);
    }

    /* User Profile */
    .sidebar-footer {
      margin-top: auto;
      padding-top: 12px;
    }

    .user-profile {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      border: 1px solid var(--novax-border);
      background: rgba(17, 24, 39, 0.6);
      border-radius: 12px;
    }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--novax-surface-secondary);
      border: 1.5px solid var(--novax-cyan);
      display: grid;
      place-items: center;
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--novax-cyan);
      box-shadow: 0 0 10px rgba(34, 211, 238, 0.2);
    }

    .user-info {
      display: flex;
      flex-direction: column;
      flex: 1;
      overflow: hidden;
    }

    .user-name {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--novax-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .user-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.74rem;
      color: var(--novax-muted);
    }

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--novax-success);
      box-shadow: 0 0 6px var(--novax-success);
    }

    /* Main Container */
    .main-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
      min-height: 0;
      overflow: hidden;
      position: relative;
    }

    /* Header */
    .main-header {
      flex-shrink: 0;
      background: rgba(13, 18, 32, 0.88);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
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
      gap: 14px;
    }

    .mobile-menu-btn {
      display: none;
      background: transparent;
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
      padding: 8px;
      border-radius: 8px;
      cursor: pointer;
    }

    .header-title-container {
      display: flex;
      flex-direction: column;
    }

    .header-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--novax-text);
      letter-spacing: -0.01em;
    }

    .header-status {
      font-size: 0.78rem;
      color: var(--novax-muted);
      margin-top: 1px;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .top-right-logo {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 5px 12px 5px 8px;
      border-radius: 12px;
      background: rgba(17, 24, 39, 0.8);
      border: 1px solid rgba(99, 102, 241, 0.3);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
    }

    .header-logo-img {
      width: 24px;
      height: 24px;
      object-fit: contain;
    }

    .header-logo-text {
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      background: linear-gradient(135deg, #F8FAFC, var(--novax-primary-hover));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
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

    /* Views Framework */
    .view-content {
      display: none;
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      min-height: 0;
      width: 100%;
    }

    .view-content.active {
      display: flex;
      flex-direction: column;
    }

    /* CHAT VIEW */
    #view-chat {
      padding: 0;
    }

    .messages-scroll {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      scroll-behavior: smooth;
      display: flex;
      flex-direction: column;
      gap: 18px;
      min-height: 0;
      max-width: 920px;
      width: 100%;
      margin: 0 auto;
    }

    /* Welcome Hero Card */
    .welcome-card {
      text-align: center;
      padding: 32px 20px 20px 20px;
      margin-bottom: 10px;
      animation: fadeIn 0.4s ease-out;
    }

    .welcome-logo {
      width: 72px;
      height: 72px;
      margin-bottom: 16px;
      filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.45));
    }

    .welcome-heading {
      font-size: 1.8rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin: 0 0 8px 0;
      background: linear-gradient(135deg, var(--novax-text) 30%, var(--novax-primary-hover) 70%, var(--novax-cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .welcome-subtitle {
      font-size: 0.95rem;
      color: var(--novax-muted);
      margin: 0 0 24px 0;
    }

    .suggestion-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      max-width: 760px;
      margin: 0 auto;
    }

    .suggestion-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      padding: 14px 16px;
      border-radius: 12px;
      text-align: left;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .suggestion-card:hover {
      border-color: var(--novax-primary);
      background: rgba(17, 24, 39, 0.9);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }

    .suggestion-icon {
      font-size: 1.1rem;
      margin-bottom: 2px;
    }

    .suggestion-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--novax-text);
    }

    .suggestion-desc {
      font-size: 0.76rem;
      color: var(--novax-muted);
    }

    /* Message Bubbles */
    .message-row {
      display: flex;
      gap: 12px;
      max-width: 86%;
      animation: messageSlide 0.25s ease-out;
    }

    @keyframes messageSlide {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
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
      background: rgba(13, 18, 32, 0.95);
      color: #ffffff;
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
      border: 1px solid rgba(99, 102, 241, 0.4);
      padding: 3px;
      overflow: hidden;
    }

    .ai-avatar-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
    }

    .message-row.user .msg-avatar {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-cyan);
      color: var(--novax-cyan);
    }

    .bubble {
      padding: 13px 16px;
      border-radius: 14px;
      line-height: 1.55;
      font-size: 0.93rem;
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

    .bubble table {
      border-collapse: collapse;
      width: 100%;
      margin: 10px 0;
      font-size: 0.85rem;
    }

    .bubble th, .bubble td {
      border: 1px solid var(--novax-border);
      padding: 8px 12px;
      text-align: left;
    }

    .bubble th {
      background: rgba(99, 102, 241, 0.15);
      color: var(--novax-cyan);
    }

    .bubble code {
      background: rgba(0, 0, 0, 0.4);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.85em;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .bubble pre {
      background: #0A0E1A;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      border: 1px solid var(--novax-border);
    }

    .bubble pre code {
      background: transparent;
      padding: 0;
      border: none;
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
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--novax-primary-hover);
      animation: pulse 1.2s infinite ease-in-out;
    }

    @keyframes pulse {
      0%, 100% { opacity: 0.3; transform: scale(0.8); }
      50% { opacity: 1; transform: scale(1.2); }
    }

    /* Composer */
    .chat-bottom {
      flex-shrink: 0;
      padding: 14px 24px 20px 24px;
      max-width: 920px;
      width: 100%;
      margin: 0 auto;
      box-sizing: border-box;
    }

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

    .send-btn svg {
      width: 18px;
      height: 18px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    /* MODULE VIEWS STYLING */
    .module-container {
      max-width: 1000px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .module-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--novax-border);
    }

    .module-title-box h2 {
      font-size: 1.3rem;
      font-weight: 700;
      margin: 0 0 4px 0;
      color: var(--novax-text);
    }

    .module-title-box p {
      font-size: 0.85rem;
      color: var(--novax-muted);
      margin: 0;
    }

    .btn-action {
      padding: 9px 16px;
      border-radius: 8px;
      background: var(--novax-primary);
      color: white;
      font-weight: 600;
      font-size: 0.85rem;
      border: 0;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.18s ease;
    }

    .btn-action:hover {
      background: var(--novax-primary-hover);
    }

    .btn-secondary {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
    }

    .btn-secondary:hover {
      background: rgba(99, 102, 241, 0.15);
      border-color: var(--novax-primary-hover);
    }

    /* MEMORY CARDS */
    .memory-notice {
      background: rgba(99, 102, 241, 0.08);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 0.84rem;
      color: var(--novax-text-secondary);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .memory-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }

    .memory-category-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .memory-cat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--novax-border);
      padding-bottom: 8px;
    }

    .memory-cat-title {
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: var(--novax-cyan);
      text-transform: uppercase;
    }

    .memory-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--novax-surface-secondary);
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid var(--novax-border);
    }

    .memory-item-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .memory-key {
      font-size: 0.75rem;
      color: var(--novax-muted);
      text-transform: uppercase;
      font-weight: 600;
    }

    .memory-val {
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--novax-text);
    }

    .memory-del-btn {
      background: transparent;
      border: 0;
      color: var(--novax-disabled);
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      transition: color 0.18s ease;
    }

    .memory-del-btn:hover {
      color: var(--novax-error);
    }

    /* Form Modal / Inline */
    .memory-form-box {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .form-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .form-group {
      flex: 1;
      min-width: 160px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .form-group label {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--novax-muted);
    }

    .form-group input, .form-group select {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      color: var(--novax-text);
      padding: 9px 12px;
      border-radius: 8px;
      font-size: 0.88rem;
      outline: none;
    }

    .form-group input:focus, .form-group select:focus {
      border-color: var(--novax-primary);
    }

    /* PROJECTS VIEW */
    .projects-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 16px;
    }

    .project-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: all 0.2s ease;
    }

    .project-card:hover {
      border-color: var(--novax-primary);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }

    .project-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .project-icon {
      font-size: 1.5rem;
      width: 44px;
      height: 44px;
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      border-radius: 10px;
      display: grid;
      place-items: center;
    }

    .project-status-badge {
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 700;
      background: rgba(99, 102, 241, 0.15);
      color: var(--novax-primary-hover);
      border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .project-name {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--novax-text);
      margin: 0;
    }

    .project-desc {
      font-size: 0.85rem;
      color: var(--novax-muted);
      margin: 0;
      line-height: 1.4;
    }

    .project-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      color: var(--novax-disabled);
      padding-top: 10px;
      border-top: 1px solid var(--novax-border);
    }

    /* TOOLS VIEW */
    .tools-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }

    .tool-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .tool-header {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .tool-icon {
      font-size: 1.4rem;
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.25);
      display: grid;
      place-items: center;
    }

    .tool-name {
      font-size: 0.98rem;
      font-weight: 700;
      color: var(--novax-text);
    }

    .tool-status {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 999px;
      display: inline-block;
    }

    .tool-status.available {
      background: rgba(34, 197, 94, 0.15);
      color: var(--novax-success);
      border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .tool-status.ready {
      background: rgba(34, 211, 238, 0.15);
      color: var(--novax-cyan);
      border: 1px solid rgba(34, 211, 238, 0.3);
    }

    .tool-status.soon {
      background: rgba(148, 163, 184, 0.1);
      color: var(--novax-disabled);
      border: 1px solid rgba(148, 163, 184, 0.2);
    }

    .tool-desc {
      font-size: 0.84rem;
      color: var(--novax-muted);
      line-height: 1.45;
      margin: 0;
    }

    /* TASKS VIEW */
    .tasks-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .task-item {
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      padding: 12px 16px;
      border-radius: 10px;
      transition: border-color 0.18s ease;
    }

    .task-item:hover {
      border-color: var(--novax-primary-hover);
    }

    .task-checkbox {
      width: 18px;
      height: 18px;
      border-radius: 4px;
      border: 2px solid var(--novax-primary);
      cursor: pointer;
      display: grid;
      place-items: center;
      background: transparent;
      color: transparent;
    }

    .task-checkbox.checked {
      background: var(--novax-primary);
      color: white;
    }

    .task-text {
      font-size: 0.9rem;
      color: var(--novax-text);
      flex: 1;
    }

    .task-text.completed {
      text-decoration: line-through;
      color: var(--novax-disabled);
    }

    .task-tag {
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 6px;
      background: var(--novax-surface-secondary);
      color: var(--novax-muted);
      border: 1px solid var(--novax-border);
    }

    /* AUTOMATIONS VIEW */
    .automation-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
    }

    .automation-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .automation-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .automation-name {
      font-size: 0.98rem;
      font-weight: 700;
      color: var(--novax-text);
    }

    .toggle-switch {
      width: 38px;
      height: 20px;
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      border-radius: 999px;
      position: relative;
      cursor: pointer;
      transition: background 0.2s ease;
    }

    .toggle-switch.active {
      background: var(--novax-primary);
      border-color: var(--novax-primary);
    }

    .toggle-knob {
      width: 14px;
      height: 14px;
      background: white;
      border-radius: 50%;
      position: absolute;
      top: 2px;
      left: 2px;
      transition: transform 0.2s ease;
    }

    .toggle-switch.active .toggle-knob {
      transform: translateX(18px);
    }

    .automation-schedule {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--novax-cyan);
    }

    /* SETTINGS VIEW */
    .settings-group {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .settings-group-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--novax-text);
      padding-bottom: 8px;
      border-bottom: 1px solid var(--novax-border);
    }

    .setting-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }

    .setting-label {
      font-size: 0.88rem;
      font-weight: 500;
      color: var(--novax-text);
    }

    .setting-desc {
      font-size: 0.78rem;
      color: var(--novax-muted);
      margin-top: 2px;
    }

    /* RESPONSIVE */
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
    <!-- SIDEBAR -->
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <div class="brand-logo">
          <img src="/assets/logo.svg" alt="NOVAX Logo" class="brand-logo-img" />
        </div>
        <div class="brand-info">
          <span class="brand-title">NOVAX</span>
          <span class="brand-subtitle">AI PERSONAL AGENT</span>
        </div>
      </div>

      <button class="new-chat-btn" onclick="startNewChat()">
        <span>＋</span> New Chat
      </button>

      <nav class="nav-group">
        <a class="nav-item active" onclick="switchView('chat', this)">
          <span class="nav-item-icon">💬</span>
          <span>Chat</span>
        </a>
        <a class="nav-item" onclick="switchView('conversations', this)">
          <span class="nav-item-icon">◉</span>
          <span>Conversations</span>
        </a>
        <a class="nav-item" onclick="switchView('memory', this)">
          <span class="nav-item-icon">🧠</span>
          <span>Memory</span>
        </a>
        <a class="nav-item" onclick="switchView('projects', this)">
          <span class="nav-item-icon">📁</span>
          <span>Projects</span>
        </a>

        <div class="nav-section-title">AGENT</div>

        <a class="nav-item" onclick="switchView('tools', this)">
          <span class="nav-item-icon">🛠</span>
          <span>Tools</span>
        </a>
        <a class="nav-item" onclick="switchView('tasks', this)">
          <span class="nav-item-icon">📋</span>
          <span>Tasks</span>
        </a>
        <a class="nav-item" onclick="switchView('automations', this)">
          <span class="nav-item-icon">🔔</span>
          <span>Automations</span>
        </a>

        <div class="nav-section-title">SYSTEM</div>

        <a class="nav-item" onclick="switchView('settings', this)">
          <span class="nav-item-icon">⚙</span>
          <span>Settings</span>
        </a>
      </nav>

      <div class="sidebar-footer">
        <div class="user-profile">
          <div class="avatar">S</div>
          <div class="user-info">
            <span class="user-name">Sriram</span>
            <span class="user-status">
              <span class="status-dot"></span> Online
            </span>
          </div>
        </div>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="main-container">
      <!-- HEADER -->
      <header class="main-header">
        <div class="header-left">
          <button class="mobile-menu-btn" onclick="toggleSidebar()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          </button>
          <div class="header-title-container">
            <div class="header-title" id="header-title-text">NOVAX Intelligence</div>
            <div class="header-status" id="header-subtitle-text">Deep Space v2.0 • Ready • Personal Agent Active</div>
          </div>
        </div>
        <div class="header-right">
          <div class="top-right-logo">
            <img src="/assets/logo.svg" alt="NOVAX Logo" class="header-logo-img" />
            <span class="header-logo-text">NOVAX-AI</span>
          </div>
          <div class="header-badge" id="ai-status-badge">● Ready</div>
        </div>
      </header>

      <!-- VIEW 1: CHAT -->
      <section class="view-content active" id="view-chat">
        <div class="messages-scroll" id="messages">
          <div class="welcome-card" id="welcome-hero">
            <img src="/assets/logo.svg" alt="NOVAX AI" class="welcome-logo" />
            <h1 class="welcome-heading">Welcome to NOVAX</h1>
            <p class="welcome-subtitle">Your intelligent personal agent for reasoning, memory, and automated workflows.</p>

            <div class="suggestion-grid">
              <div class="suggestion-card" onclick="sendPrompt('Explain Quantum Computing in simple terms')">
                <span class="suggestion-icon">💡</span>
                <span class="suggestion-title">Explain something to me</span>
                <span class="suggestion-desc">Quantum Computing explained simply</span>
              </div>
              <div class="suggestion-card" onclick="sendPrompt('Write a Python script for web scraping')">
                <span class="suggestion-icon">💻</span>
                <span class="suggestion-title">Help me write code</span>
                <span class="suggestion-desc">Python web scraper implementation</span>
              </div>
              <div class="suggestion-card" onclick="sendPrompt('Compare Python vs Rust for system programming')">
                <span class="suggestion-icon">📊</span>
                <span class="suggestion-title">Analyze this</span>
                <span class="suggestion-desc">Compare Python vs Rust</span>
              </div>
              <div class="suggestion-card" onclick="sendPrompt('Create a roadmap for a machine learning app')">
                <span class="suggestion-icon">🚀</span>
                <span class="suggestion-title">Help me plan a project</span>
                <span class="suggestion-desc">Machine Learning app roadmap</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-bottom">
          <form class="composer" id="chat-form">
            <input id="message-input" placeholder="Ask NOVAX anything..." autocomplete="off" />
            <button type="submit" class="send-btn" title="Send message">
              <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </form>
        </div>
      </section>

      <!-- VIEW 2: CONVERSATIONS -->
      <section class="view-content" id="view-conversations">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>Conversations History</h2>
              <p>Manage and review your active and archived chat sessions with NOVAX.</p>
            </div>
            <button class="btn-action btn-secondary" onclick="clearAllConversations()">
              🗑 Clear Current Session
            </button>
          </div>

          <div class="memory-grid">
            <div class="memory-category-card">
              <div class="memory-cat-header">
                <span class="memory-cat-title">Today</span>
              </div>
              <div class="memory-item" onclick="switchView('chat')">
                <div class="memory-item-info">
                  <span class="memory-val">NOVAX Architecture & Interface</span>
                  <span class="memory-key">Active Session • Just now</span>
                </div>
              </div>
              <div class="memory-item" onclick="switchView('chat')">
                <div class="memory-item-info">
                  <span class="memory-val">Python Data Structures Practice</span>
                  <span class="memory-key">2 hours ago</span>
                </div>
              </div>
            </div>

            <div class="memory-category-card">
              <div class="memory-cat-header">
                <span class="memory-cat-title">Yesterday</span>
              </div>
              <div class="memory-item">
                <div class="memory-item-info">
                  <span class="memory-val">DSA Problem Solving & LeetCode</span>
                  <span class="memory-key">Yesterday • 4:15 PM</span>
                </div>
              </div>
              <div class="memory-item">
                <div class="memory-item-info">
                  <span class="memory-val">Hackathon Brainstorming & Ideas</span>
                  <span class="memory-key">Yesterday • 11:30 AM</span>
                </div>
              </div>
            </div>

            <div class="memory-category-card">
              <div class="memory-cat-header">
                <span class="memory-cat-title">Older</span>
              </div>
              <div class="memory-item">
                <div class="memory-item-info">
                  <span class="memory-val">System Architecture & Intent Systems</span>
                  <span class="memory-key">3 days ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- VIEW 3: MEMORY -->
      <section class="view-content" id="view-memory">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>NOVAX Agent Memory</h2>
              <p>Personal information, education, preferences, and interests remembered by NOVAX.</p>
            </div>
            <button class="btn-action" onclick="toggleMemoryForm()">
              ＋ Add Memory
            </button>
          </div>

          <div class="memory-notice">
            🔒 <span>Memories belong to you. Information stored here shapes NOVAX's personal responses while staying strictly local.</span>
          </div>

          <!-- Add Memory Form -->
          <div class="memory-form-box" id="memory-add-form" style="display: none;">
            <div class="form-row">
              <div class="form-group">
                <label>Category</label>
                <select id="mem-category">
                  <option value="profile">PROFILE</option>
                  <option value="education">EDUCATION</option>
                  <option value="preferences">PREFERENCES</option>
                  <option value="interests">INTERESTS</option>
                </select>
              </div>
              <div class="form-group">
                <label>Key / Aspect</label>
                <input type="text" id="mem-key" placeholder="e.g. Favorite Language" />
              </div>
              <div class="form-group">
                <label>Value</label>
                <input type="text" id="mem-value" placeholder="e.g. Python" />
              </div>
            </div>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
              <button class="btn-action btn-secondary" onclick="toggleMemoryForm()">Cancel</button>
              <button class="btn-action" onclick="saveNewMemory()">Save Memory</button>
            </div>
          </div>

          <div class="memory-grid" id="memory-cards-container">
            <!-- Dynamic items rendered from backend API -->
          </div>
        </div>
      </section>

      <!-- VIEW 4: PROJECTS -->
      <section class="view-content" id="view-projects">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>Projects Workspace</h2>
              <p>Organize your chats, code, and agent tasks around your active projects.</p>
            </div>
            <button class="btn-action" onclick="alert('Project workspace created for NOVAX-AI')">
              ＋ New Project
            </button>
          </div>

          <div class="projects-grid">
            <div class="project-card">
              <div class="project-top">
                <div class="project-icon">🚀</div>
                <span class="project-status-badge">Active</span>
              </div>
              <h3 class="project-name">NOVAX-AI</h3>
              <p class="project-desc">Development, documentation, and agent task management for the NOVAX personal assistant.</p>
              <div class="project-meta">
                <span>12 Conversations</span>
                <span>8 Tasks</span>
              </div>
            </div>

            <div class="project-card">
              <div class="project-top">
                <div class="project-icon">💡</div>
                <span class="project-status-badge">Research</span>
              </div>
              <h3 class="project-name">Hackathon 2026</h3>
              <p class="project-desc">Research ideas, problem statements, and presentation planning.</p>
              <div class="project-meta">
                <span>4 Conversations</span>
                <span>3 Tasks</span>
              </div>
            </div>

            <div class="project-card">
              <div class="project-top">
                <div class="project-icon">🧠</div>
                <span class="project-status-badge">Ongoing</span>
              </div>
              <h3 class="project-name">DSA Practice</h3>
              <p class="project-desc">Data Structures, Algorithms practice, and LeetCode problem notes.</p>
              <div class="project-meta">
                <span>9 Conversations</span>
                <span>5 Tasks</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- VIEW 5: TOOLS -->
      <section class="view-content" id="view-tools">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>NOVAX Capabilities & Tools</h2>
              <p>Intelligent tools available to NOVAX for real-time information retrieval and task execution.</p>
            </div>
          </div>

          <div class="tools-grid">
            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">🔍</div>
                <div>
                  <div class="tool-name">Web Search</div>
                  <span class="tool-status available">Available (Live)</span>
                </div>
              </div>
              <p class="tool-desc">Search the internet for live news, real-time facts, and verified Wikipedia summaries.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">🧮</div>
                <div>
                  <div class="tool-name">Calculator</div>
                  <span class="tool-status available">Available</span>
                </div>
              </div>
              <p class="tool-desc">Perform mathematical evaluations, unit conversions, and data calculation logic.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">💻</div>
                <div>
                  <div class="tool-name">Code Runner</div>
                  <span class="tool-status available">Available</span>
                </div>
              </div>
              <p class="tool-desc">Analyze, format, and generate clean code snippets across programming languages.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">📄</div>
                <div>
                  <div class="tool-name">Document Reader</div>
                  <span class="tool-status ready">Ready</span>
                </div>
              </div>
              <p class="tool-desc">Parse text content, extract structured data, and summarize key insights.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">📝</div>
                <div>
                  <div class="tool-name">Text Analyzer</div>
                  <span class="tool-status available">Available</span>
                </div>
              </div>
              <p class="tool-desc">Synthesize text, rephrase content, and format tabular markdown data on demand.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">📊</div>
                <div>
                  <div class="tool-name">Data Analyzer</div>
                  <span class="tool-status ready">Ready</span>
                </div>
              </div>
              <p class="tool-desc">Process structured datasets and generate clear Markdown table outputs.</p>
            </div>

            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-icon">🎨</div>
                <div>
                  <div class="tool-name">Image Analyzer</div>
                  <span class="tool-status soon">Coming Soon</span>
                </div>
              </div>
              <p class="tool-desc">Visual inspection and multimodal image description processing.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- VIEW 6: TASKS -->
      <section class="view-content" id="view-tasks">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>Agent & User Tasks</h2>
              <p>Track your goals, daily routines, and items managed with NOVAX.</p>
            </div>
            <button class="btn-action" onclick="addNewTask()">＋ Add Task</button>
          </div>

          <div class="tasks-list" id="tasks-container">
            <div class="task-item">
              <div class="task-checkbox checked" onclick="toggleTask(this)">✓</div>
              <span class="task-text completed">Complete DSA Arrays practice</span>
              <span class="task-tag">DSA</span>
            </div>
            <div class="task-item">
              <div class="task-checkbox" onclick="toggleTask(this)"></div>
              <span class="task-text">Update NOVAX README and documentation</span>
              <span class="task-tag">NOVAX-AI</span>
            </div>
            <div class="task-item">
              <div class="task-checkbox" onclick="toggleTask(this)"></div>
              <span class="task-text">Study Python async patterns</span>
              <span class="task-tag">Learning</span>
            </div>
            <div class="task-item">
              <div class="task-checkbox" onclick="toggleTask(this)"></div>
              <span class="task-text">Hackathon presentation preparation</span>
              <span class="task-tag">Hackathon</span>
            </div>
          </div>
        </div>
      </section>

      <!-- VIEW 7: AUTOMATIONS -->
      <section class="view-content" id="view-automations">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>Scheduled Automations</h2>
              <p>Configure recurring triggers and agent actions performed on schedule.</p>
            </div>
          </div>

          <div class="automation-cards">
            <div class="automation-card">
              <div class="automation-top">
                <span class="automation-name">Daily DSA Reminder</span>
                <div class="toggle-switch active" onclick="toggleSwitch(this)">
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <span class="automation-schedule">Every day • 7:00 PM</span>
              <p class="tool-desc">Sends a daily notification with recommended LeetCode practice problems.</p>
            </div>

            <div class="automation-card">
              <div class="automation-top">
                <span class="automation-name">Project Progress Check</span>
                <div class="toggle-switch active" onclick="toggleSwitch(this)">
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <span class="automation-schedule">Every Monday • 9:00 AM</span>
              <p class="tool-desc">Summarizes active project tasks and highlights upcoming milestones.</p>
            </div>

            <div class="automation-card">
              <div class="automation-top">
                <span class="automation-name">AI News Feed Briefing</span>
                <div class="toggle-switch" onclick="toggleSwitch(this)">
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <span class="automation-schedule">Every morning • 8:00 AM</span>
              <p class="tool-desc">Fetches live AI technology developments and summarizes headlines.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- VIEW 8: SETTINGS -->
      <section class="view-content" id="view-settings">
        <div class="module-container">
          <div class="module-header">
            <div class="module-title-box">
              <h2>Settings & Preferences</h2>
              <p>Customize NOVAX appearance, AI models, and system configuration.</p>
            </div>
          </div>

          <div class="settings-group">
            <span class="settings-group-title">Appearance Theme</span>
            <div class="setting-row">
              <div>
                <div class="setting-label">Visual Theme</div>
                <div class="setting-desc">Primary visual theme for NOVAX Interface</div>
              </div>
              <select style="background: var(--novax-surface-secondary); border: 1px solid var(--novax-border); color: var(--novax-text); padding: 8px 12px; border-radius: 8px;">
                <option selected>NOVAX — Deep Space</option>
                <option>Dark Neutral</option>
                <option>System Default</option>
              </select>
            </div>
          </div>

          <div class="settings-group">
            <span class="settings-group-title">AI Engine & Search</span>
            <div class="setting-row">
              <div>
                <div class="setting-label">Live Web Search Enrichment</div>
                <div class="setting-desc">Allow NOVAX to query Wikipedia and real-time news feeds</div>
              </div>
              <div class="toggle-switch active" onclick="toggleSwitch(this)">
                <div class="toggle-knob"></div>
              </div>
            </div>
          </div>

          <div class="settings-group">
            <span class="settings-group-title">About NOVAX</span>
            <div class="setting-row">
              <div>
                <div class="setting-label">Version</div>
                <div class="setting-desc">NOVAX AI Personal Agent v2.0.0 (Deep Space)</div>
              </div>
              <span class="header-badge">Latest</span>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>

  <script>
    const messages = document.getElementById('messages');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const sidebar = document.getElementById('sidebar');
    const welcomeHero = document.getElementById('welcome-hero');
    const headerTitleText = document.getElementById('header-title-text');
    const headerSubtitleText = document.getElementById('header-subtitle-text');
    const aiStatusBadge = document.getElementById('ai-status-badge');

    let currentView = 'chat';

    function toggleSidebar() {
      sidebar.classList.toggle('open');
    }

    function switchView(viewName, el) {
      currentView = viewName;
      document.querySelectorAll('.view-content').forEach(v => v.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

      const targetView = document.getElementById(`view-${viewName}`);
      if (targetView) targetView.classList.add('active');

      if (el) el.classList.add('active');

      // Update Header Text dynamically
      const viewTitles = {
        'chat': { title: 'NOVAX Intelligence', status: 'Deep Space v2.0 • Ready • Personal Agent Active' },
        'conversations': { title: 'Conversations', status: 'Chat Session Management & History' },
        'memory': { title: 'Agent Memory', status: 'Personal Memory & Preferences' },
        'projects': { title: 'Projects Workspace', status: 'Active Development & Goal Tracking' },
        'tools': { title: 'Tools & Capabilities', status: 'Agent Integration & Web Search' },
        'tasks': { title: 'Tasks & Planning', status: 'Goal Management & Daily Checklists' },
        'automations': { title: 'Scheduled Automations', status: 'Recurring Agent Actions & Triggers' },
        'settings': { title: 'Settings', status: 'Theme, AI Engine, & Configuration' }
      };

      if (viewTitles[viewName]) {
        headerTitleText.textContent = viewTitles[viewName].title;
        headerSubtitleText.textContent = viewTitles[viewName].status;
      }

      if (viewName === 'memory') {
        loadMemories();
      }

      if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
      }
    }

    function startNewChat() {
      switchView('chat', document.querySelector('.nav-item'));
      fetch('/api/clear', { method: 'POST' }).catch(() => {});

      messages.innerHTML = `
        <div class="welcome-card" id="welcome-hero">
          <img src="/assets/logo.svg" alt="NOVAX AI" class="welcome-logo" />
          <h1 class="welcome-heading">Welcome to NOVAX</h1>
          <p class="welcome-subtitle">Your intelligent personal agent for reasoning, memory, and automated workflows.</p>

          <div class="suggestion-grid">
            <div class="suggestion-card" onclick="sendPrompt('Explain Quantum Computing in simple terms')">
              <span class="suggestion-icon">💡</span>
              <span class="suggestion-title">Explain something to me</span>
              <span class="suggestion-desc">Quantum Computing explained simply</span>
            </div>
            <div class="suggestion-card" onclick="sendPrompt('Write a Python script for web scraping')">
              <span class="suggestion-icon">💻</span>
              <span class="suggestion-title">Help me write code</span>
              <span class="suggestion-desc">Python web scraper implementation</span>
            </div>
            <div class="suggestion-card" onclick="sendPrompt('Compare Python vs Rust for system programming')">
              <span class="suggestion-icon">📊</span>
              <span class="suggestion-title">Analyze this</span>
              <span class="suggestion-desc">Compare Python vs Rust</span>
            </div>
            <div class="suggestion-card" onclick="sendPrompt('Create a roadmap for a machine learning app')">
              <span class="suggestion-icon">🚀</span>
              <span class="suggestion-title">Help me plan a project</span>
              <span class="suggestion-desc">Machine Learning app roadmap</span>
            </div>
          </div>
        </div>
      `;
    }

    function sendPrompt(text) {
      input.value = text;
      form.dispatchEvent(new Event('submit'));
    }

    function formatMarkdown(text) {
      if (!text) return '';
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Markdown Tables
      if (html.includes('|')) {
        const lines = html.split('\n');
        let inTable = false;
        let tableHtml = '';
        let processedLines = [];

        lines.forEach(line => {
          const trimmed = line.trim();
          if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            if (!inTable) {
              inTable = true;
              tableHtml = '<table>';
            }

            if (trimmed.includes('---')) {
              return; // Skip separator line
            }

            const cells = trimmed.split('|').slice(1, -1);
            const tag = tableHtml.includes('<th>') ? 'td' : 'th';
            tableHtml += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
          } else {
            if (inTable) {
              inTable = false;
              tableHtml += '</table>';
              processedLines.push(tableHtml);
              tableHtml = '';
            }
            processedLines.push(line);
          }
        });
        if (inTable) {
          tableHtml += '</table>';
          processedLines.push(tableHtml);
        }
        html = processedLines.join('\n');
      }

      // Code blocks
      html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

      // Convert Markdown Images: ![alt](url)
      html = html.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s\)]+)\)/g, function(match, alt, url) {
        return `<img src="${url}" alt="${alt}" style="max-width:100%; border-radius:8px; margin:8px 0;" />`;
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
      const hero = document.getElementById('welcome-hero');
      if (hero && messages.children.length === 1) {
        hero.style.display = 'none';
      }

      const row = document.createElement('div');
      row.className = `message-row ${role}`;
      
      const avatar = document.createElement('div');
      avatar.className = 'msg-avatar';
      if (role === 'ai') {
        avatar.innerHTML = '<img src="/assets/logo.svg" alt="NOVAX AI" class="ai-avatar-img" />';
      } else {
        avatar.textContent = 'S';
      }

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
      aiStatusBadge.textContent = '● Thinking...';
      aiStatusBadge.style.color = 'var(--novax-cyan)';
      aiStatusBadge.style.borderColor = 'rgba(34, 211, 238, 0.3)';

      const typing = document.createElement('div');
      typing.id = 'typing';
      typing.className = 'typing-indicator';
      typing.innerHTML = '<div class="pulse-dot"></div> NOVAX is processing...';
      messages.appendChild(typing);
      scrollToBottom();
    }

    function hideTyping() {
      aiStatusBadge.textContent = '● Ready';
      aiStatusBadge.style.color = 'var(--novax-success)';
      aiStatusBadge.style.borderColor = 'rgba(34, 197, 94, 0.25)';

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

    // MEMORY INTEGRATION
    async function loadMemories() {
      const container = document.getElementById('memory-cards-container');
      container.innerHTML = '<p style="color: var(--novax-muted);">Loading memory items...</p>';

      try {
        const res = await fetch('/api/memory');
        const memoryData = await res.json();

        container.innerHTML = '';
        const categories = ['profile', 'education', 'preferences', 'interests'];

        categories.forEach(cat => {
          const items = memoryData[cat] || {};
          const card = document.createElement('div');
          card.className = 'memory-category-card';

          let itemsHtml = '';
          const keys = Object.keys(items);

          if (keys.length === 0) {
            itemsHtml = `<div style="font-size: 0.82rem; color: var(--novax-disabled); font-style: italic;">No ${cat} memories stored yet.</div>`;
          } else {
            keys.forEach(k => {
              itemsHtml += `
                <div class="memory-item">
                  <div class="memory-item-info">
                    <span class="memory-key">${k}</span>
                    <span class="memory-val">${items[k]}</span>
                  </div>
                  <button class="memory-del-btn" onclick="deleteMemory('${cat}', '${k}')" title="Delete Memory">✕</button>
                </div>
              `;
            });
          }

          card.innerHTML = `
            <div class="memory-cat-header">
              <span class="memory-cat-title">${cat.toUpperCase()}</span>
            </div>
            ${itemsHtml}
          `;

          container.appendChild(card);
        });
      } catch (err) {
        container.innerHTML = '<p style="color: var(--novax-error);">Failed to load memory data.</p>';
      }
    }

    function toggleMemoryForm() {
      const f = document.getElementById('memory-add-form');
      f.style.display = (f.style.display === 'none') ? 'flex' : 'none';
    }

    async function saveNewMemory() {
      const category = document.getElementById('mem-category').value;
      const key = document.getElementById('mem-key').value.trim();
      const value = document.getElementById('mem-value').value.trim();

      if (!key || !value) {
        alert('Please fill in both key and value.');
        return;
      }

      try {
        await fetch('/api/memory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, key, value })
        });
        document.getElementById('mem-key').value = '';
        document.getElementById('mem-value').value = '';
        toggleMemoryForm();
        loadMemories();
      } catch (e) {
        alert('Failed to save memory.');
      }
    }

    async function deleteMemory(category, key) {
      if (!confirm(`Delete memory item "${key}" from ${category.toUpperCase()}?`)) return;

      try {
        await fetch('/api/memory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, key, delete: true })
        });
        loadMemories();
      } catch (e) {
        alert('Failed to delete memory.');
      }
    }

    function clearAllConversations() {
      if (confirm('Clear active chat session history?')) {
        startNewChat();
      }
    }

    function toggleTask(el) {
      el.classList.toggle('checked');
      const textEl = el.nextElementSibling;
      if (textEl) textEl.classList.toggle('completed');
    }

    function addNewTask() {
      const taskText = prompt('Enter new task description:');
      if (!taskText || !taskText.trim()) return;

      const container = document.getElementById('tasks-container');
      const item = document.createElement('div');
      item.className = 'task-item';
      item.innerHTML = `
        <div class="task-checkbox" onclick="toggleTask(this)"></div>
        <span class="task-text">${taskText.trim()}</span>
        <span class="task-tag">User Task</span>
      `;
      container.appendChild(item);
    }

    function toggleSwitch(el) {
      el.classList.toggle('active');
    }
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
        elif parsed.path == "/api/memory":
            memories = self.server.brain.memory.load_memory()
            self._send_json(memories)
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

        if parsed.path == "/api/chat":
            message = (data.get("message") or "").strip()
            if not message:
                self._send_json({"error": "message is required"}, status=400)
                return

            response = self.server.brain.get_response(message)
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
                self.server.brain.memory.delete(category, key)
            else:
                self.server.brain.memory.set(category, key, value)

            updated = self.server.brain.memory.load_memory()
            self._send_json({"success": True, "memory": updated})
            return

        elif parsed.path == "/api/clear":
            self.server.brain.conversation.clear()
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
