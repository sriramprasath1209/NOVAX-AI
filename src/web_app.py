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

    /* Sidebar Conversations List */
    .sidebar-conv-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
      margin: 4px 0 12px 0;
      max-height: 220px;
      overflow-y: auto;
    }

    .sidebar-conv-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 13px;
      color: var(--novax-text-secondary);
      cursor: pointer;
      transition: all 0.2s ease;
      text-decoration: none;
    }

    .sidebar-conv-item:hover {
      background: rgba(255, 255, 255, 0.06);
      color: var(--novax-text);
    }

    .sidebar-conv-item.active {
      background: var(--novax-nav-active-bg);
      border: 1px solid var(--novax-nav-active-border);
      color: var(--novax-cyan);
      font-weight: 600;
    }

    .sidebar-conv-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }

    .sidebar-conv-del {
      opacity: 0;
      background: transparent;
      border: none;
      color: var(--novax-muted);
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
      transition: all 0.2s ease;
    }

    .sidebar-conv-item:hover .sidebar-conv-del {
      opacity: 1;
    }

    .sidebar-conv-del:hover {
      color: var(--novax-error);
      background: rgba(239, 68, 68, 0.15);
    }

    /* Message Bubbles & Actions */
    .chat-bubble-wrapper {
      position: relative;
      display: flex;
      flex-direction: column;
      width: 100%;
    }

    .chat-bubble-wrapper.user {
      align-items: flex-end;
    }

    .chat-bubble-wrapper.assistant {
      align-items: flex-start;
    }

    .msg-delete-btn {
      position: absolute;
      top: 6px;
      right: 6px;
      opacity: 0;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--novax-border);
      color: var(--novax-muted);
      border-radius: 6px;
      padding: 2px 6px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s ease;
      z-index: 10;
    }

    .chat-bubble-wrapper:hover .msg-delete-btn {
      opacity: 1;
    }

    .msg-delete-btn:hover {
      color: #FCA5A5;
      background: rgba(239, 68, 68, 0.25);
      border-color: rgba(239, 68, 68, 0.4);
    }

    /* Conversations Panel Cards */
    .conv-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
    }

    .conv-card:hover {
      border-color: var(--novax-primary);
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(99, 102, 241, 0.15);
    }

    .conv-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
    }

    .conv-card-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--novax-text);
      margin: 0;
      word-break: break-word;
    }

    .conv-card-meta {
      font-size: 12px;
      color: var(--novax-muted);
      margin-bottom: 14px;
    }

    .conv-card-actions {
      display: flex;
      gap: 8px;
    }

    /* Memory Center Styling */
    .memory-center-wrapper {
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding-bottom: 40px;
    }

    .memory-header-banner {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(34, 211, 238, 0.08) 100%);
      border: 1px solid var(--novax-nav-active-border);
      border-radius: 18px;
      padding: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }

    .memory-stat-chip {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      border-radius: 12px;
      padding: 8px 14px;
      font-size: 13px;
      color: var(--novax-text-secondary);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .memory-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 18px;
      padding: 24px;
      transition: all 0.2s ease;
    }

    .memory-card:hover {
      border-color: rgba(99, 102, 241, 0.4);
    }

    .memory-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .memory-card-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--novax-cyan);
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 0;
    }

    .memory-field-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
    }

    .memory-field-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      background: rgba(17, 24, 39, 0.4);
      padding: 10px 14px;
      border-radius: 12px;
      border: 1px solid var(--novax-border-light);
    }

    .memory-field-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--novax-muted);
    }

    .memory-field-val {
      font-size: 14px;
      font-weight: 500;
      color: var(--novax-text);
      word-break: break-word;
    }

    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 6px;
    }

    .mem-chip {
      background: rgba(99, 102, 241, 0.18);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: var(--novax-text);
      border-radius: 20px;
      padding: 5px 12px;
      font-size: 13px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .mem-chip-del {
      background: transparent;
      border: none;
      color: var(--novax-muted);
      cursor: pointer;
      font-size: 14px;
      padding: 0 2px;
      border-radius: 50%;
      transition: all 0.2s ease;
    }

    .mem-chip-del:hover {
      color: var(--novax-error);
    }

    .source-badge {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 7px;
      border-radius: 10px;
      display: inline-block;
    }
    .source-badge.USER {
      background: rgba(99, 102, 241, 0.25);
      color: #818CF8;
      border: 1px solid rgba(99, 102, 241, 0.4);
    }
    .source-badge.CONVERSATION {
      background: rgba(34, 211, 238, 0.2);
      color: var(--novax-cyan);
      border: 1px solid rgba(34, 211, 238, 0.4);
    }
    .source-badge.SYSTEM {
      background: rgba(139, 92, 246, 0.25);
      color: #C084FC;
      border: 1px solid rgba(139, 92, 246, 0.4);
    }

    .pref-option-group {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 6px;
    }

    .pref-radio-label {
      background: var(--novax-surface-secondary);
      border: 1px solid var(--novax-border);
      border-radius: 10px;
      padding: 8px 14px;
      font-size: 13px;
      cursor: pointer;
      color: var(--novax-text-secondary);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .pref-radio-label.selected {
      background: var(--novax-nav-active-bg);
      border-color: var(--novax-primary);
      color: var(--novax-text);
      font-weight: 600;
    }

    .wizard-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(4, 6, 12, 0.85);
      backdrop-filter: blur(8px);
      z-index: 1000;
      display: none;
      place-items: center;
      padding: 20px;
    }

    .wizard-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 20px;
      width: 100%;
      max-width: 540px;
      padding: 28px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
    }

    /* Thinking Indicator Styling */
    .thinking-bubble {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: var(--novax-cyan);
      font-weight: 500;
      font-size: 14px;
    }

    .thinking-dots {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .thinking-pulse-dot {
      width: 6px;
      height: 6px;
      background: var(--novax-cyan);
      border-radius: 50%;
      display: inline-block;
      animation: thinkingPulse 1.4s infinite ease-in-out both;
    }

    .thinking-pulse-dot:nth-child(1) { animation-delay: -0.32s; }
    .thinking-pulse-dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes thinkingPulse {
      0%, 80%, 100% { transform: scale(0.2); opacity: 0.2; }
      40% { transform: scale(1); opacity: 1; }
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

        <button class="btn-new-chat" onclick="startNewChat()">
          <span>+ New Chat</span>
        </button>

        <div class="nav-section">
          <div class="nav-section-title">Workspace</div>
          <div class="nav-item active" id="nav-item-conversations-panel" onclick="showPanel('conversations-panel')">
            <span>Conversations</span>
          </div>
          <div class="nav-item" id="nav-item-chat" onclick="showPanel('chat-panel')">
            <span>Active Chat</span>
          </div>
          <div class="nav-item" onclick="showPanel('memory-panel')">
            <span>Memory</span>
          </div>
          <div class="nav-item" onclick="showPanel('projects-panel')">
            <span>Projects</span>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">Agent Tools</div>
          <div class="nav-item" onclick="alert('Tools section is active.')">
            <span>Tools</span>
          </div>
          <div class="nav-item" onclick="showPanel('tasks-panel')">
            <span>Tasks</span>
          </div>
          <div class="nav-item" onclick="alert('Automations feature enabled.')">
            <span>Automations</span>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-item" onclick="alert('Settings view loaded.')">
            <span>Settings</span>
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
            <div class="chat-bubble-wrapper assistant">
              <div class="chat-bubble assistant">
                Welcome to NOVAX! I am your personal AI assistant. How can I help you today?
              </div>
            </div>
          </div>
          <div class="chat-input-bar">
            <input type="text" id="user-input" class="chat-input" placeholder="Type your message to NOVAX..." onkeydown="if(event.key==='Enter') sendMessage()" />
            <button class="btn-send" onclick="sendMessage()">Send</button>
          </div>
        </div>

        <!-- Conversations Panel -->
        <div id="conversations-panel" class="panel-view">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px;">
            <div>
              <h2 style="color:var(--novax-cyan); margin:0;">Conversations</h2>
              <p style="color:var(--novax-muted); font-size:14px; margin:4px 0 0 0;">All your previous chats are stored here with their headings. You can reopen, write on them, or delete them.</p>
            </div>
            <input type="text" id="search-conversations-input" class="form-control" style="width:240px;" placeholder="Search conversations..." oninput="filterConversations()" />
          </div>
          <div id="conversations-grid" class="card-grid"></div>
        </div>

        <!-- Personal Memory Center Panel -->
        <div id="memory-panel" class="panel-view">
          <div class="memory-center-wrapper">

            <!-- Banner Header -->
            <div class="memory-header-banner">
              <div>
                <h1 style="font-size:24px; font-weight:800; color:var(--novax-text); margin:0 0 6px 0; display:flex; align-items:center; gap:10px;">
                  Personalize NOVAX
                </h1>
                <p style="color:var(--novax-text-secondary); font-size:14px; margin:0;">
                  Help NOVAX understand you better by adding information about yourself. You control what NOVAX remembers.
                </p>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                <button class="btn-primary" onclick="startPersonalizationWizard()" style="padding:10px 18px; width:auto;">
                  Start Personalization
                </button>
              </div>
            </div>

            <!-- Top Summary & Search Bar -->
            <div style="display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;">
              <div id="memory-summary-bar" style="display:flex; gap:10px; flex-wrap:wrap;">
                <div class="memory-stat-chip">Memories: <strong id="total-memory-count" style="color:var(--novax-cyan);">0</strong> items</div>
                <div class="memory-stat-chip">Status: <strong style="color:var(--novax-success);">User Isolated</strong></div>
              </div>
              <div style="position:relative; width:280px;">
                <input type="text" id="memory-search-input" class="form-control" placeholder="Search your memories..." oninput="onMemorySearchInput(this.value)" />
              </div>
            </div>

            <!-- Main Memory Categories Container -->
            <div id="memory-categories-container" style="display:flex; flex-direction:column; gap:20px;"></div>

            <!-- Dangerous Action: Memory Management -->
            <div class="memory-card" style="border-color:rgba(239,68,68,0.3); background:rgba(239,68,68,0.04);">
              <div class="memory-card-header" style="border-bottom:none; margin-bottom:0; padding-bottom:0;">
                <div>
                  <h3 class="memory-card-title" style="color:#FCA5A5;">Memory Management</h3>
                  <p style="color:var(--novax-muted); font-size:13px; margin:4px 0 0 0;">Permanently remove your saved personal memories from NOVAX-AI.</p>
                </div>
                <button class="btn-logout" onclick="clearAllMemoriesConfirm()" style="color:#FCA5A5; border-color:rgba(239,68,68,0.4); padding:8px 16px;">
                  Clear All Memories
                </button>
              </div>
            </div>

          </div>
        </div>

        <!-- First-Time Personalization Wizard Modal -->
        <div id="wizard-modal" class="wizard-overlay">
          <div class="wizard-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h2 style="color:var(--novax-cyan); margin:0; font-size:20px;">Let's Personalize NOVAX</h2>
              <span id="wizard-step-indicator" style="font-size:12px; color:var(--novax-muted);">Step 1 of 6</span>
            </div>
            <p style="color:var(--novax-text-secondary); font-size:14px; margin-bottom:20px;">
              You can tell NOVAX about yourself so it can give you more relevant answers. You can skip any step.
            </p>
            <div id="wizard-step-body"></div>
            <div style="display:flex; justify-content:space-between; margin-top:24px;">
              <button class="btn-logout" onclick="skipWizardStep()">Skip</button>
              <button class="btn-primary" id="btn-wizard-next" onclick="nextWizardStep()" style="width:auto; padding:10px 20px;">Next Step →</button>
            </div>
          </div>
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
    let currentConversationId = null;
    let allConversationsCache = [];

    function generateConvId() {
      return 'conv_' + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
    }

    function showView(viewId) {
      document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
      const target = document.getElementById(viewId);
      if (target) target.classList.add('active');
    }

    function showPanel(panelId) {
      document.querySelectorAll('.panel-view').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

      const target = document.getElementById(panelId);
      if (target) target.classList.add('active');

      if (panelId === 'chat-panel') {
        const navItem = document.getElementById('nav-item-chat');
        if (navItem) navItem.classList.add('active');
      } else if (panelId === 'conversations-panel') {
        const navItem = document.getElementById('nav-item-conversations-panel');
        if (navItem) navItem.classList.add('active');
        loadConversationsList();
      } else if (panelId === 'memory-panel') {
        loadMemories();
      }
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
          startNewChat();
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

    function startNewChat() {
      currentConversationId = generateConvId();

      const container = document.getElementById('chat-messages');
      container.innerHTML = `
        <div class="chat-bubble-wrapper assistant">
          <div class="chat-bubble assistant">
            Welcome to NOVAX! I am your personal AI assistant. How can I help you today?
          </div>
        </div>
      `;

      showPanel('chat-panel');
      loadConversationsList();
    }

    async function loadConversationsList() {
      try {
        const res = await fetch('/api/conversations');
        if (!res.ok) return;
        const conversations = await res.json();
        allConversationsCache = conversations || [];
        renderSidebarConversations(allConversationsCache);
        renderGridConversations(allConversationsCache);
      } catch (e) {}
    }

    function renderSidebarConversations(conversations) {
      const container = document.getElementById('sidebar-conversations-list');
      if (!container) return;
      container.innerHTML = '';

      if (!conversations || conversations.length === 0) {
        container.innerHTML = '<div style="font-size:12px; color:var(--novax-muted); padding:6px 10px;">No saved chats yet.</div>';
        return;
      }

      conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'sidebar-conv-item' + (conv.id === currentConversationId ? ' active' : '');
        item.onclick = (e) => {
          if (e.target.classList.contains('sidebar-conv-del')) return;
          openConversation(conv.id);
        };

        item.innerHTML = `
          <span class="sidebar-conv-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
          <button class="sidebar-conv-del" onclick="deleteConversation('${conv.id}', event)" title="Delete Conversation">✕</button>
        `;
        container.appendChild(item);
      });
    }

    function renderGridConversations(conversations) {
      const grid = document.getElementById('conversations-grid');
      if (!grid) return;
      grid.innerHTML = '';

      if (!conversations || conversations.length === 0) {
        grid.innerHTML = '<div class="data-card"><p>No saved conversations found.</p></div>';
        return;
      }

      conversations.forEach(conv => {
        const card = document.createElement('div');
        card.className = 'conv-card';

        const dateStr = conv.created_at ? new Date(conv.created_at * 1000).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
        const msgCount = conv.message_count || 0;

        card.innerHTML = `
          <div>
            <div class="conv-card-header">
              <h3 class="conv-card-title">${escapeHtml(conv.title)}</h3>
            </div>
            <div class="conv-card-meta">
              Date: ${dateStr} &nbsp;•&nbsp; ${msgCount} message${msgCount === 1 ? '' : 's'}
            </div>
          </div>
          <div class="conv-card-actions">
            <button class="btn-primary" style="padding:8px 14px; font-size:13px; flex:1;" onclick="openConversation('${conv.id}')">Open & Write</button>
            <button class="btn-logout" style="padding:8px 10px; font-size:13px; color:var(--novax-cyan);" onclick="renameConversationPrompt('${conv.id}', '${escapeHtml(conv.title).replace(/'/g, "\\'")}')">Rename</button>
            <button class="btn-logout" style="padding:8px 10px; font-size:13px; color:#FCA5A5;" onclick="deleteConversation('${conv.id}')">Delete</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterConversations() {
      const q = (document.getElementById('search-conversations-input').value || '').toLowerCase().trim();
      if (!q) {
        renderGridConversations(allConversationsCache);
        return;
      }
      const filtered = allConversationsCache.filter(c => (c.title || '').toLowerCase().includes(q));
      renderGridConversations(filtered);
    }

    async function openConversation(convId) {
      try {
        const res = await fetch('/api/conversations/messages?id=' + encodeURIComponent(convId));
        if (!res.ok) return;
        const data = await res.json();

        currentConversationId = convId;

        const container = document.getElementById('chat-messages');
        container.innerHTML = '';

        if (!data.messages || data.messages.length === 0) {
          container.innerHTML = `
            <div class="chat-bubble-wrapper assistant">
              <div class="chat-bubble assistant">No messages in this chat session yet. Type below to write!</div>
            </div>
          `;
        } else {
          data.messages.forEach(msg => {
            appendMessageBubble(msg.role, msg.content, msg.id);
          });
        }

        showPanel('chat-panel');
        renderSidebarConversations(allConversationsCache);
        container.scrollTop = container.scrollHeight;
      } catch (e) {}
    }

    function appendMessageBubble(role, content, msgId) {
      const container = document.getElementById('chat-messages');
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-bubble-wrapper ' + (role === 'user' ? 'user' : 'assistant');
      if (msgId) wrapper.dataset.msgId = msgId;

      const bubble = document.createElement('div');
      bubble.className = 'chat-bubble ' + (role === 'user' ? 'user' : 'assistant');

      if (role === 'user') {
        bubble.innerText = content;
      } else {
        bubble.innerHTML = formatMessageText(content);
      }

      if (msgId) {
        const delBtn = document.createElement('button');
        delBtn.className = 'msg-delete-btn';
        delBtn.innerText = 'Delete';
        delBtn.onclick = (e) => {
          e.stopPropagation();
          deleteMessage(msgId, wrapper);
        };
        wrapper.appendChild(delBtn);
      }

      wrapper.appendChild(bubble);
      container.appendChild(wrapper);
      container.scrollTop = container.scrollHeight;
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
          startNewChat();
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
          startNewChat();
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

    async function handleLogout() {
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch (e) {}
      currentUser = null;
      currentConversationId = null;
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

      if (!currentConversationId) {
        currentConversationId = generateConvId();
      }

      const container = document.getElementById('chat-messages');
      appendMessageBubble('user', text, null);

      input.value = '';
      container.scrollTop = container.scrollHeight;

      // Show NOVAX Thinking Indicator
      const thinkingWrapper = document.createElement('div');
      thinkingWrapper.className = 'chat-bubble-wrapper assistant';
      thinkingWrapper.id = 'thinking-bubble-active';
      thinkingWrapper.innerHTML = `
        <div class="chat-bubble assistant">
          <span class="thinking-bubble">
            <span>NOVAX is thinking</span>
            <span class="thinking-dots">
              <span class="thinking-pulse-dot"></span>
              <span class="thinking-pulse-dot"></span>
              <span class="thinking-pulse-dot"></span>
            </span>
          </span>
        </div>
      `;
      container.appendChild(thinkingWrapper);
      container.scrollTop = container.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, conversation_id: currentConversationId })
        });
        const data = await res.json();

        // Remove thinking indicator
        const activeThinking = document.getElementById('thinking-bubble-active');
        if (activeThinking) activeThinking.remove();

        appendMessageBubble('assistant', data.reply || 'No response returned.', null);
        loadConversationsList();
      } catch (e) {
        const activeThinking = document.getElementById('thinking-bubble-active');
        if (activeThinking) activeThinking.remove();

        appendMessageBubble('assistant', 'Error communicating with NOVAX.', null);
      }
    }

    async function deleteConversation(convId, e) {
      if (e) e.stopPropagation();
      if (!confirm('Are you sure you want to delete this conversation?')) return;

      try {
        await fetch('/api/conversations/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: convId })
        });

        if (currentConversationId === convId) {
          startNewChat();
        } else {
          loadConversationsList();
        }
      } catch (err) {}
    }

    function deleteCurrentConversation() {
      if (currentConversationId) {
        deleteConversation(currentConversationId);
      }
    }

    async function deleteMessage(msgId, wrapperElement) {
      try {
        const res = await fetch('/api/messages/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: msgId })
        });
        if (res.ok) {
          if (wrapperElement) wrapperElement.remove();
          loadConversationsList();
        }
      } catch (e) {}
    }

    function renameCurrentConversation() {
      if (!currentConversationId) return;
      renameConversationPrompt(currentConversationId, "");
    }

    async function renameConversationPrompt(convId, oldTitle) {
      const newTitle = prompt('Enter new heading/title for this conversation:', oldTitle);
      if (!newTitle || !newTitle.trim() || newTitle.trim() === oldTitle) return;

      try {
        const res = await fetch('/api/conversations/rename', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: convId, title: newTitle.trim() })
        });
        if (res.ok) {
          loadConversationsList();
        }
      } catch (e) {}
    }

    function escapeHtml(text) {
      if (!text) return '';
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    let currentMemoriesData = {};
    let wizardCurrentStep = 1;

    async function loadMemories() {
      try {
        const res = await fetch('/api/memory');
        if (!res.ok) return;
        currentMemoriesData = await res.json() || {};
        renderMemoryCenter(currentMemoriesData);
      } catch (e) {}
    }

    function renderMemoryCenter(memories, filterQuery = '') {
      const container = document.getElementById('memory-categories-container');
      if (!container) return;
      container.innerHTML = '';

      let totalItems = 0;

      const categories = [
        { id: 'profile', title: 'Profile' },
        { id: 'education', title: 'Education' },
        { id: 'career', title: 'Career & Skills' },
        { id: 'interests', title: 'Interests' },
        { id: 'goals', title: 'Goals' },
        { id: 'preferences', title: 'Response Preferences' },
        { id: 'projects', title: 'Projects' },
        { id: 'routines', title: 'Routines' },
        { id: 'custom', title: 'Custom Memories' }
      ];

      Object.keys(memories).forEach(cat => {
        if (memories[cat]) {
          totalItems += Object.keys(memories[cat]).length;
        }
      });
      document.getElementById('total-memory-count').innerText = totalItems;

      const q = filterQuery.toLowerCase().trim();

      categories.forEach(catConfig => {
        const catData = memories[catConfig.id] || memories[catConfig.id.toLowerCase()] || {};
        const itemsCount = Object.keys(catData).length;

        if (q) {
          const catText = (catConfig.title + ' ' + JSON.stringify(catData)).toLowerCase();
          if (!catText.includes(q)) return;
        }

        const card = document.createElement('div');
        card.className = 'memory-card';

        let bodyHtml = '';
        if (catConfig.id === 'profile') bodyHtml = renderProfileCategoryHtml(catData);
        else if (catConfig.id === 'education') bodyHtml = renderEducationCategoryHtml(catData);
        else if (catConfig.id === 'career') bodyHtml = renderCareerSkillsCategoryHtml(catData);
        else if (catConfig.id === 'interests') bodyHtml = renderInterestsCategoryHtml(catData);
        else if (catConfig.id === 'goals') bodyHtml = renderGoalsCategoryHtml(catData);
        else if (catConfig.id === 'preferences') bodyHtml = renderPreferencesCategoryHtml(catData);
        else if (catConfig.id === 'projects') bodyHtml = renderProjectsCategoryHtml(catData);
        else if (catConfig.id === 'routines') bodyHtml = renderRoutinesCategoryHtml(catData);
        else bodyHtml = renderCustomCategoryHtml(catData);

        card.innerHTML = `
          <div class="memory-card-header">
            <h3 class="memory-card-title">${catConfig.title}</h3>
            <span style="font-size:12px; color:var(--novax-muted); font-weight:600;">${itemsCount} item${itemsCount === 1 ? '' : 's'}</span>
          </div>
          <div>${bodyHtml}</div>
        `;
        container.appendChild(card);
      });

      if (container.children.length === 0 && q) {
        container.innerHTML = `<div class="memory-card"><p style="color:var(--novax-muted); text-align:center; margin:0;">No memories found matching "${escapeHtml(q)}".</p></div>`;
      }
    }

    function getVal(data, key, defaultVal = '') {
      if (!data || !data[key]) return defaultVal;
      return data[key].value || data[key] || defaultVal;
    }

    function renderProfileCategoryHtml(data) {
      const name = getVal(data, 'name');
      const prefName = getVal(data, 'preferred_name');
      const pronouns = getVal(data, 'pronouns');
      const ageRange = getVal(data, 'age_range');
      const country = getVal(data, 'country');
      const city = getVal(data, 'city');
      const timezone = getVal(data, 'timezone');
      const language = getVal(data, 'language');

      if (!name && !country && !timezone && !language) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">NOVAX doesn't know about your profile details yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="promptEditProfile()">+ Add Profile Info</button>
        `;
      }

      return `
        <div class="memory-field-grid">
          <div class="memory-field-item"><span class="memory-field-label">Full Name</span><span class="memory-field-val">${escapeHtml(name || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Preferred Name</span><span class="memory-field-val">${escapeHtml(prefName || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Pronouns</span><span class="memory-field-val">${escapeHtml(pronouns || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Age Range</span><span class="memory-field-val">${escapeHtml(ageRange || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Country</span><span class="memory-field-val">${escapeHtml(country || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">City</span><span class="memory-field-val">${escapeHtml(city || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Timezone</span><span class="memory-field-val">${escapeHtml(timezone || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Preferred Language</span><span class="memory-field-val">${escapeHtml(language || 'Not specified')}</span></div>
        </div>
        <div style="margin-top:14px;">
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditProfile()">Edit Profile</button>
        </div>
      `;
    }

    async function promptEditProfile() {
      const data = currentMemoriesData['profile'] || {};
      const name = prompt('Full Name:', getVal(data, 'name'));
      if (name !== null) await saveMemoryItem('profile', 'name', name.trim());
      const prefName = prompt('Preferred Name:', getVal(data, 'preferred_name'));
      if (prefName !== null) await saveMemoryItem('profile', 'preferred_name', prefName.trim());
      const country = prompt('Country:', getVal(data, 'country'));
      if (country !== null) await saveMemoryItem('profile', 'country', country.trim());
      const timezone = prompt('Timezone (e.g. Asia/Kolkata):', getVal(data, 'timezone'));
      if (timezone !== null) await saveMemoryItem('profile', 'timezone', timezone.trim());
      const language = prompt('Preferred Language:', getVal(data, 'language'));
      if (language !== null) await saveMemoryItem('profile', 'language', language.trim());
      loadMemories();
    }

    function renderEducationCategoryHtml(data) {
      const status = getVal(data, 'status');
      const institution = getVal(data, 'institution');
      const course = getVal(data, 'course');
      const field = getVal(data, 'field');
      const year = getVal(data, 'year');
      const subjectsStr = getVal(data, 'subjects');

      const subjects = subjectsStr ? subjectsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

      if (!status && !institution && !course) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">NOVAX doesn't know about your education yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="promptEditEducation()">+ Add Education</button>
        `;
      }

      let chipHtml = subjects.map(s => `
        <span class="mem-chip">
          ${escapeHtml(s)}
          <button class="mem-chip-del" onclick="removeSubjectChip('${escapeHtml(s).replace(/'/g, "\\'")}')">✕</button>
        </span>
      `).join('');

      return `
        <div class="memory-field-grid" style="margin-bottom:12px;">
          <div class="memory-field-item"><span class="memory-field-label">Status</span><span class="memory-field-val">${escapeHtml(status || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Institution</span><span class="memory-field-val">${escapeHtml(institution || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Degree / Course</span><span class="memory-field-val">${escapeHtml(course || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Field of Study</span><span class="memory-field-val">${escapeHtml(field || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Current Year</span><span class="memory-field-val">${escapeHtml(year || 'Not specified')}</span></div>
        </div>
        <div style="margin-bottom:12px;">
          <span class="memory-field-label">Subjects</span>
          <div class="chip-container">${chipHtml || '<span style="font-size:13px; color:var(--novax-muted);">No subjects added yet.</span>'}</div>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditEducation()">Edit Education</button>
          <button class="btn-logout" style="color:var(--novax-primary); padding:6px 14px; font-size:13px;" onclick="addSubjectPrompt()">+ Add Subject</button>
        </div>
      `;
    }

    async function promptEditEducation() {
      const data = currentMemoriesData['education'] || {};
      const status = prompt('Education Status (e.g. Student, Graduate):', getVal(data, 'status'));
      if (status !== null) await saveMemoryItem('education', 'status', status.trim());
      const institution = prompt('Institution / University:', getVal(data, 'institution'));
      if (institution !== null) await saveMemoryItem('education', 'institution', institution.trim());
      const course = prompt('Degree / Course (e.g. B.Tech):', getVal(data, 'course'));
      if (course !== null) await saveMemoryItem('education', 'course', course.trim());
      const field = prompt('Field of Study (e.g. Computer Science):', getVal(data, 'field'));
      if (field !== null) await saveMemoryItem('education', 'field', field.trim());
      const year = prompt('Current Year (e.g. 2nd Year):', getVal(data, 'year'));
      if (year !== null) await saveMemoryItem('education', 'year', year.trim());
      loadMemories();
    }

    async function addSubjectPrompt() {
      const s = prompt('Enter subject name:');
      if (!s || !s.trim()) return;
      const data = currentMemoriesData['education'] || {};
      let existing = getVal(data, 'subjects');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(Boolean) : [];
      if (!list.includes(s.trim())) {
        list.push(s.trim());
        await saveMemoryItem('education', 'subjects', list.join(', '));
        loadMemories();
      }
    }

    async function removeSubjectChip(sub) {
      const data = currentMemoriesData['education'] || {};
      let existing = getVal(data, 'subjects');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(x => x !== sub) : [];
      await saveMemoryItem('education', 'subjects', list.join(', '));
      loadMemories();
    }

    function renderCareerSkillsCategoryHtml(data) {
      const occupation = getVal(data, 'occupation');
      const experience = getVal(data, 'experience');
      const targetRole = getVal(data, 'target_role');
      const careerGoal = getVal(data, 'career_goal');
      const techSkillsStr = getVal(data, 'tech_skills');

      const techSkills = techSkillsStr ? techSkillsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

      let chipsHtml = techSkills.map(s => `
        <span class="mem-chip">
          ${escapeHtml(s)}
          <button class="mem-chip-del" onclick="removeTechSkillChip('${escapeHtml(s).replace(/'/g, "\\'")}')">✕</button>
        </span>
      `).join('');

      return `
        <div class="memory-field-grid" style="margin-bottom:12px;">
          <div class="memory-field-item"><span class="memory-field-label">Occupation</span><span class="memory-field-val">${escapeHtml(occupation || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Experience Level</span><span class="memory-field-val">${escapeHtml(experience || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Target Role</span><span class="memory-field-val">${escapeHtml(targetRole || 'Not specified')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Career Goal</span><span class="memory-field-val">${escapeHtml(careerGoal || 'Not specified')}</span></div>
        </div>
        <div style="margin-bottom:12px;">
          <span class="memory-field-label">Technical & Soft Skills</span>
          <div class="chip-container">${chipsHtml || '<span style="font-size:13px; color:var(--novax-muted);">No skills added yet.</span>'}</div>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditCareer()">Edit Career Info</button>
          <button class="btn-logout" style="color:var(--novax-primary); padding:6px 14px; font-size:13px;" onclick="addSkillPrompt()">+ Add Skill</button>
        </div>
      `;
    }

    async function promptEditCareer() {
      const data = currentMemoriesData['career'] || {};
      const occ = prompt('Occupation:', getVal(data, 'occupation'));
      if (occ !== null) await saveMemoryItem('career', 'occupation', occ.trim());
      const exp = prompt('Experience Level (e.g. Beginner, Intermediate, Senior):', getVal(data, 'experience'));
      if (exp !== null) await saveMemoryItem('career', 'experience', exp.trim());
      const role = prompt('Target Role (e.g. AI Engineer):', getVal(data, 'target_role'));
      if (role !== null) await saveMemoryItem('career', 'target_role', role.trim());
      const goal = prompt('Career Goal:', getVal(data, 'career_goal'));
      if (goal !== null) await saveMemoryItem('career', 'career_goal', goal.trim());
      loadMemories();
    }

    async function addSkillPrompt() {
      const s = prompt('Enter skill (e.g. Python, Git, DSA, React):');
      if (!s || !s.trim()) return;
      const data = currentMemoriesData['career'] || {};
      let existing = getVal(data, 'tech_skills');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(Boolean) : [];
      if (!list.includes(s.trim())) {
        list.push(s.trim());
        await saveMemoryItem('career', 'tech_skills', list.join(', '));
        loadMemories();
      }
    }

    async function removeTechSkillChip(sk) {
      const data = currentMemoriesData['career'] || {};
      let existing = getVal(data, 'tech_skills');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(x => x !== sk) : [];
      await saveMemoryItem('career', 'tech_skills', list.join(', '));
      loadMemories();
    }

    function renderInterestsCategoryHtml(data) {
      const itemsStr = getVal(data, 'interests_list');
      const interests = itemsStr ? itemsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

      let chipsHtml = interests.map(s => `
        <span class="mem-chip">
          ${escapeHtml(s)}
          <button class="mem-chip-del" onclick="removeInterestChip('${escapeHtml(s).replace(/'/g, "\\'")}')">✕</button>
        </span>
      `).join('');

      return `
        <div style="margin-bottom:12px;">
          <span class="memory-field-label">Hobbies, Topics & Technologies</span>
          <div class="chip-container">${chipsHtml || '<span style="font-size:13px; color:var(--novax-muted);">No interests added yet.</span>'}</div>
        </div>
        <div>
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="addInterestPrompt()">+ Add Interest</button>
        </div>
      `;
    }

    async function addInterestPrompt() {
      const s = prompt('Enter interest / topic / hobby (e.g. Artificial Intelligence, Programming, Hackathons):');
      if (!s || !s.trim()) return;
      const data = currentMemoriesData['interests'] || {};
      let existing = getVal(data, 'interests_list');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(Boolean) : [];
      if (!list.includes(s.trim())) {
        list.push(s.trim());
        await saveMemoryItem('interests', 'interests_list', list.join(', '));
        loadMemories();
      }
    }

    async function removeInterestChip(item) {
      const data = currentMemoriesData['interests'] || {};
      let existing = getVal(data, 'interests_list');
      let list = existing ? existing.split(',').map(x => x.trim()).filter(x => x !== item) : [];
      await saveMemoryItem('interests', 'interests_list', list.join(', '));
      loadMemories();
    }

    function renderGoalsCategoryHtml(data) {
      const shortTerm = getVal(data, 'short_term');
      const longTerm = getVal(data, 'long_term');

      return `
        <div class="memory-field-grid" style="margin-bottom:12px;">
          <div class="memory-field-item">
            <span class="memory-field-label">Short-Term Goals</span>
            <span class="memory-field-val">${escapeHtml(shortTerm || 'Not specified')}</span>
          </div>
          <div class="memory-field-item">
            <span class="memory-field-label">Long-Term Goals</span>
            <span class="memory-field-val">${escapeHtml(longTerm || 'Not specified')}</span>
          </div>
        </div>
        <div>
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditGoals()">Edit Goals</button>
        </div>
      `;
    }

    async function promptEditGoals() {
      const data = currentMemoriesData['goals'] || {};
      const st = prompt('Short-Term Goals:', getVal(data, 'short_term'));
      if (st !== null) await saveMemoryItem('goals', 'short_term', st.trim());
      const lt = prompt('Long-Term Goals:', getVal(data, 'long_term'));
      if (lt !== null) await saveMemoryItem('goals', 'long_term', lt.trim());
      loadMemories();
    }

    function renderPreferencesCategoryHtml(data) {
      const length = getVal(data, 'length', 'Balanced');
      const style = getVal(data, 'style', 'Step-by-step');
      const tone = getVal(data, 'tone', 'Friendly');
      const lang = getVal(data, 'programming_language', 'Python');
      const notes = getVal(data, 'additional_notes', '');

      return `
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div>
            <span class="memory-field-label">Response Length</span>
            <div class="pref-option-group">
              ${['Concise', 'Balanced', 'Detailed'].map(opt => `
                <div class="pref-radio-label ${length === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'length', '${opt}')">
                  ${length === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div>
            <span class="memory-field-label">Explanation Style</span>
            <div class="pref-option-group">
              ${['Simple', 'Step-by-step', 'Technical'].map(opt => `
                <div class="pref-radio-label ${style === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'style', '${opt}')">
                  ${style === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div>
            <span class="memory-field-label">Tone</span>
            <div class="pref-option-group">
              ${['Professional', 'Friendly', 'Casual'].map(opt => `
                <div class="pref-radio-label ${tone === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'tone', '${opt}')">
                  ${tone === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div class="memory-field-grid">
            <div class="memory-field-item">
              <span class="memory-field-label">Preferred Programming Language</span>
              <span class="memory-field-val">${escapeHtml(lang)}</span>
            </div>
            <div class="memory-field-item">
              <span class="memory-field-label">Additional Instructions</span>
              <span class="memory-field-val">${escapeHtml(notes || 'None')}</span>
            </div>
          </div>
          <div>
            <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditPreferences()">Edit Preferences</button>
          </div>
        </div>
      `;
    }

    async function promptEditPreferences() {
      const data = currentMemoriesData['preferences'] || {};
      const lang = prompt('Preferred Programming Language:', getVal(data, 'programming_language', 'Python'));
      if (lang !== null) await saveMemoryItem('preferences', 'programming_language', lang.trim());
      const notes = prompt('Additional instructions for NOVAX:', getVal(data, 'additional_notes'));
      if (notes !== null) await saveMemoryItem('preferences', 'additional_notes', notes.trim());
      loadMemories();
    }

    function renderProjectsCategoryHtml(data) {
      let items = Object.keys(data);
      if (items.length === 0) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">No project context stored yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="addCustomMemoryCategoryPrompt('projects')">+ Add Project Memory</button>
        `;
      }
      let html = '<div class="memory-field-grid">';
      items.forEach(k => {
        const itemObj = data[k];
        const val = itemObj.value || itemObj;
        const src = itemObj.source || 'USER';
        html += `
          <div class="memory-field-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="memory-field-label">${escapeHtml(k)}</span>
              <span class="source-badge ${src}">${src}</span>
            </div>
            <span class="memory-field-val">${escapeHtml(val)}</span>
            <div style="margin-top:6px; text-align:right;">
              <button class="btn-logout" style="font-size:11px; padding:2px 6px; color:#FCA5A5;" onclick="deleteMemoryConfirm('projects', '${escapeHtml(k).replace(/'/g, "\\'")}')">Delete</button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      html += `<div style="margin-top:12px;"><button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="addCustomMemoryCategoryPrompt('projects')">+ Add Project Context</button></div>`;
      return html;
    }

    function renderRoutinesCategoryHtml(data) {
      const wakeup = getVal(data, 'wake_up');
      const study = getVal(data, 'study');
      const sleep = getVal(data, 'sleep');
      const workHours = getVal(data, 'working_hours');

      if (!wakeup && !study && !sleep && !workHours) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">No routine schedule stored yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="promptEditRoutines()">+ Add Routine</button>
        `;
      }

      return `
        <div class="memory-field-grid" style="margin-bottom:12px;">
          <div class="memory-field-item"><span class="memory-field-label">Wake-Up Time</span><span class="memory-field-val">${escapeHtml(wakeup || 'Not set')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Study Time</span><span class="memory-field-val">${escapeHtml(study || 'Not set')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Sleep Time</span><span class="memory-field-val">${escapeHtml(sleep || 'Not set')}</span></div>
          <div class="memory-field-item"><span class="memory-field-label">Preferred Working Hours</span><span class="memory-field-val">${escapeHtml(workHours || 'Not set')}</span></div>
        </div>
        <div>
          <button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="promptEditRoutines()">Edit Routines</button>
        </div>
      `;
    }

    async function promptEditRoutines() {
      const data = currentMemoriesData['routines'] || {};
      const wu = prompt('Wake-up time (e.g. 7:00 AM):', getVal(data, 'wake_up'));
      if (wu !== null) await saveMemoryItem('routines', 'wake_up', wu.trim());
      const st = prompt('Study time (e.g. 7:00 PM):', getVal(data, 'study'));
      if (st !== null) await saveMemoryItem('routines', 'study', st.trim());
      const sl = prompt('Sleep time (e.g. 11:00 PM):', getVal(data, 'sleep'));
      if (sl !== null) await saveMemoryItem('routines', 'sleep', sl.trim());
      const wh = prompt('Preferred working hours (e.g. 6 PM - 10 PM):', getVal(data, 'working_hours'));
      if (wh !== null) await saveMemoryItem('routines', 'working_hours', wh.trim());
      loadMemories();
    }

    function renderCustomCategoryHtml(data) {
      let items = Object.keys(data);
      if (items.length === 0) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">No custom memories added yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="addCustomMemoryCategoryPrompt('custom')">+ Add Memory</button>
        `;
      }
      let html = '<div class="memory-field-grid">';
      items.forEach(k => {
        const itemObj = data[k];
        const val = itemObj.value || itemObj;
        const src = itemObj.source || 'USER';
        html += `
          <div class="memory-field-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="memory-field-label">${escapeHtml(k)}</span>
              <span class="source-badge ${src}">${src}</span>
            </div>
            <span class="memory-field-val">${escapeHtml(val)}</span>
            <div style="margin-top:6px; text-align:right;">
              <button class="btn-logout" style="font-size:11px; padding:2px 6px; color:#FCA5A5;" onclick="deleteMemoryConfirm('custom', '${escapeHtml(k).replace(/'/g, "\\'")}')">Delete</button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      html += `<div style="margin-top:12px;"><button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="addCustomMemoryCategoryPrompt('custom')">+ Add Memory</button></div>`;
      return html;
    }

    async function addCustomMemoryCategoryPrompt(category) {
      const k = prompt('Memory Label / Title (e.g. Learning Style):');
      if (!k || !k.trim()) return;
      const v = prompt('Memory Details / Value:');
      if (!v || !v.trim()) return;
      await saveMemoryItem(category, k.trim(), v.trim(), 'USER');
      loadMemories();
    }

    async function saveMemoryItem(category, key, value, source = 'USER') {
      try {
        await fetch('/api/memory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, key, value, source })
        });
      } catch (e) {}
    }

    async function deleteMemoryConfirm(category, key) {
      if (!confirm(`Delete memory "${key}"?\nThis information will no longer be used by NOVAX.`)) return;
      try {
        await fetch('/api/memory/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, key })
        });
        loadMemories();
      } catch (e) {}
    }

    async function clearAllMemoriesConfirm() {
      if (!confirm('Are you sure you want to clear ALL memories?\nThis will permanently remove all your saved personal memories from NOVAX-AI.')) return;
      try {
        await fetch('/api/memory/clear_all', { method: 'POST' });
        loadMemories();
      } catch (e) {}
    }

    function onMemorySearchInput(val) {
      renderMemoryCenter(currentMemoriesData, val);
    }

    function startPersonalizationWizard() {
      wizardCurrentStep = 1;
      showWizardStep(1);
      document.getElementById('wizard-modal').style.display = 'grid';
    }

    function showWizardStep(step) {
      const indicator = document.getElementById('wizard-step-indicator');
      const body = document.getElementById('wizard-step-body');
      const nextBtn = document.getElementById('btn-wizard-next');

      indicator.innerText = `Step ${step} of 6`;

      if (step === 1) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 1: Profile</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-name" class="form-control" placeholder="Full Name (e.g. Sriram Prasath)" />
            <input type="text" id="wiz-country" class="form-control" placeholder="Country (e.g. India)" />
            <input type="text" id="wiz-tz" class="form-control" placeholder="Timezone (e.g. Asia/Kolkata)" />
          </div>
        `;
        nextBtn.innerText = 'Next Step →';
      } else if (step === 2) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 2: Education</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-status" class="form-control" placeholder="Status (e.g. Student)" />
            <input type="text" id="wiz-inst" class="form-control" placeholder="Institution / University" />
            <input type="text" id="wiz-course" class="form-control" placeholder="Course / Degree (e.g. B.Tech CS)" />
          </div>
        `;
        nextBtn.innerText = 'Next Step →';
      } else if (step === 3) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 3: Career & Skills</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-occ" class="form-control" placeholder="Occupation / Role" />
            <input type="text" id="wiz-skills" class="form-control" placeholder="Technical Skills (comma separated: Python, Git, DSA)" />
            <input type="text" id="wiz-goal" class="form-control" placeholder="Target Role / Career Goal" />
          </div>
        `;
        nextBtn.innerText = 'Next Step →';
      } else if (step === 4) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 4: Interests</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-interests" class="form-control" placeholder="Topics & Hobbies (comma separated: AI, Web Dev, Music)" />
          </div>
        `;
        nextBtn.innerText = 'Next Step →';
      } else if (step === 5) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 5: Goals</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-st" class="form-control" placeholder="Short-Term Goal" />
            <input type="text" id="wiz-lt" class="form-control" placeholder="Long-Term Goal" />
          </div>
        `;
        nextBtn.innerText = 'Next Step →';
      } else if (step === 6) {
        body.innerHTML = `
          <h3 style="color:var(--novax-cyan); margin-top:0;">Step 6: Preferences</h3>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <input type="text" id="wiz-lang" class="form-control" placeholder="Preferred Programming Language (e.g. Python)" />
            <textarea id="wiz-notes" class="form-control" placeholder="Additional preference notes for NOVAX..." rows="3"></textarea>
          </div>
        `;
        nextBtn.innerText = 'Finish Personalization';
      }
    }

    async function nextWizardStep() {
      if (wizardCurrentStep === 1) {
        const name = (document.getElementById('wiz-name').value || '').trim();
        const country = (document.getElementById('wiz-country').value || '').trim();
        const tz = (document.getElementById('wiz-tz').value || '').trim();
        if (name) await saveMemoryItem('profile', 'name', name);
        if (country) await saveMemoryItem('profile', 'country', country);
        if (tz) await saveMemoryItem('profile', 'timezone', tz);
      } else if (wizardCurrentStep === 2) {
        const status = (document.getElementById('wiz-status').value || '').trim();
        const inst = (document.getElementById('wiz-inst').value || '').trim();
        const course = (document.getElementById('wiz-course').value || '').trim();
        if (status) await saveMemoryItem('education', 'status', status);
        if (inst) await saveMemoryItem('education', 'institution', inst);
        if (course) await saveMemoryItem('education', 'course', course);
      } else if (wizardCurrentStep === 3) {
        const occ = (document.getElementById('wiz-occ').value || '').trim();
        const skills = (document.getElementById('wiz-skills').value || '').trim();
        const goal = (document.getElementById('wiz-goal').value || '').trim();
        if (occ) await saveMemoryItem('career', 'occupation', occ);
        if (skills) await saveMemoryItem('career', 'tech_skills', skills);
        if (goal) await saveMemoryItem('career', 'career_goal', goal);
      } else if (wizardCurrentStep === 4) {
        const interests = (document.getElementById('wiz-interests').value || '').trim();
        if (interests) await saveMemoryItem('interests', 'interests_list', interests);
      } else if (wizardCurrentStep === 5) {
        const st = (document.getElementById('wiz-st').value || '').trim();
        const lt = (document.getElementById('wiz-lt').value || '').trim();
        if (st) await saveMemoryItem('goals', 'short_term', st);
        if (lt) await saveMemoryItem('goals', 'long_term', lt);
      } else if (wizardCurrentStep === 6) {
        const lang = (document.getElementById('wiz-lang').value || '').trim();
        const notes = (document.getElementById('wiz-notes').value || '').trim();
        if (lang) await saveMemoryItem('preferences', 'programming_language', lang);
        if (notes) await saveMemoryItem('preferences', 'additional_notes', notes);

        document.getElementById('wizard-modal').style.display = 'none';
        loadMemories();
        return;
      }

      wizardCurrentStep++;
      showWizardStep(wizardCurrentStep);
    }

    function skipWizardStep() {
      if (wizardCurrentStep >= 6) {
        document.getElementById('wizard-modal').style.display = 'none';
        loadMemories();
        return;
      }
      wizardCurrentStep++;
      showWizardStep(wizardCurrentStep);
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

        elif parsed.path == "/api/memory":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            memories = self.server.brain.memory.load_memory(user_id=user["id"])
            self._send_json(memories)
            return

        elif parsed.path == "/api/memory/search":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            query = parse_qs(parsed.query).get("q", [""])[0]
            results = self.server.brain.memory.search(query, user_id=user["id"])
            self._send_json(results)
            return

        elif parsed.path == "/api/conversations":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            conversations = db.get_user_conversations(user["id"])
            self._send_json(conversations)
            return

        elif parsed.path == "/api/conversations/messages":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            query = parse_qs(parsed.query)
            conv_id = query.get("id", [None])[0] or query.get("conversation_id", [None])[0]
            if not conv_id:
                self._send_json({"error": "id parameter required"}, status=400)
                return
            conv = db.get_conversation(conv_id, user["id"])
            messages = db.get_conversation_messages(conv_id, user["id"])
            self._send_json({
                "id": conv_id,
                "title": conv["title"] if conv else "Conversation",
                "messages": messages
            })
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
            conv_id = data.get("conversation_id")
            if not message:
                self._send_json({"error": "message is required"}, status=400)
                return

            response = self.server.brain.get_response(message, user_id=user["id"], user_name=user["name"], conversation_id=conv_id)
            conv = db.get_conversation(conv_id, user["id"]) if conv_id else None
            self._send_json({
                "reply": response,
                "conversation_id": conv_id,
                "title": conv["title"] if conv else "New Chat"
            })
            return

        elif parsed.path == "/api/conversations/delete":
            conv_id = data.get("id") or data.get("conversation_id")
            if not conv_id:
                self._send_json({"error": "id is required"}, status=400)
                return
            db.delete_user_conversation(conv_id, user["id"])
            self._send_json({"success": True})
            return

        elif parsed.path == "/api/conversations/rename":
            conv_id = data.get("id") or data.get("conversation_id")
            title = (data.get("title") or "").strip()
            if not conv_id or not title:
                self._send_json({"error": "id and title are required"}, status=400)
                return
            db.update_conversation_title(conv_id, user["id"], title)
            self._send_json({"success": True})
            return

        elif parsed.path == "/api/messages/delete":
            msg_id = data.get("id") or data.get("message_id")
            if not msg_id:
                self._send_json({"error": "id is required"}, status=400)
                return
            db.delete_message(msg_id, user["id"])
            self._send_json({"success": True})
            return

        elif parsed.path == "/api/memory":
            category = data.get("category")
            key = data.get("key")
            value = data.get("value")
            source = data.get("source", "USER")
            is_delete = data.get("delete", False)

            if not category or not key:
                self._send_json({"error": "category and key required"}, status=400)
                return

            if is_delete:
                self.server.brain.memory.delete(category, key, user_id=user["id"])
            else:
                self.server.brain.memory.set(category, key, value, user_id=user["id"], source=source)

            updated = self.server.brain.memory.load_memory(user_id=user["id"])
            self._send_json({"success": True, "memory": updated})
            return

        elif parsed.path == "/api/memory/delete":
            category = data.get("category")
            key = data.get("key")
            if not category or not key:
                self._send_json({"error": "category and key required"}, status=400)
                return
            self.server.brain.memory.delete(category, key, user_id=user["id"])
            updated = self.server.brain.memory.load_memory(user_id=user["id"])
            self._send_json({"success": True, "memory": updated})
            return

        elif parsed.path == "/api/memory/clear_all":
            self.server.brain.memory.clear_all(user_id=user["id"])
            self._send_json({"success": True, "memory": {}})
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
