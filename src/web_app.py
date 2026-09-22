import json
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from src.brain import Brain
from src.db import db
from src import auth
from src.file_parser import parse_uploaded_file


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

    .chat-footer-wrapper {
      display: flex;
      flex-direction: column;
      background: var(--novax-sidebar);
      border-top: 1px solid var(--novax-border);
    }


    .chat-drop-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(8, 11, 20, 0.94);
      border: 2px dashed var(--novax-cyan);
      border-radius: 16px;
      z-index: 100;
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      pointer-events: none;
      backdrop-filter: blur(8px);
    }

    .chat-drop-overlay.active {
      display: flex;
    }

    .drop-overlay-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--novax-cyan);
      letter-spacing: 0.5px;
    }

    .drop-overlay-subtitle {
      font-size: 13px;
      color: var(--novax-text-secondary);
    }

    .chat-attachment-preview {
      margin: 10px 24px 0 24px;
      padding: 8px 14px;
      background: rgba(0, 240, 255, 0.08);
      border: 1px solid rgba(0, 240, 255, 0.25);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .attachment-info {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
    }

    .attachment-icon {
      font-size: 10px;
      font-weight: 800;
      background: var(--novax-cyan);
      color: #000;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }

    .attachment-name {
      font-size: 13px;
      font-weight: 600;
      color: var(--novax-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 280px;
    }

    .attachment-size {
      font-size: 11px;
      color: var(--novax-text-secondary);
    }

    .btn-remove-attachment {
      background: transparent;
      border: none;
      color: var(--novax-text-secondary);
      font-size: 14px;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .btn-remove-attachment:hover {
      color: #ff5252;
      background: rgba(255, 82, 82, 0.1);
    }

    .user-attached-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: 8px;
      padding: 5px 10px;
      margin-bottom: 8px;
      font-size: 12px;
      width: fit-content;
    }

    .user-badge-icon {
      font-size: 9px;
      font-weight: 800;
      background: var(--novax-cyan);
      color: #000;
      padding: 2px 5px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }

    .user-badge-name {
      font-weight: 600;
      color: var(--novax-text);
      max-width: 240px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .user-badge-size {
      font-size: 11px;
      color: var(--novax-text-secondary);
    }

    .user-message-text {
      line-height: 1.5;
    }

    .chat-input-bar {
      padding: 12px 24px 16px 24px;
      display: flex;
      gap: 12px;
      align-items: center;
      background: transparent;
    }

    .btn-attach {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--novax-border);
      color: var(--novax-text-secondary);
      font-size: 12px;
      font-weight: 600;
      padding: 0 14px;
      border-radius: 12px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      white-space: nowrap;
      height: 46px;
    }

    .btn-attach:hover {
      background: rgba(0, 240, 255, 0.1);
      border-color: var(--novax-cyan);
      color: var(--novax-cyan);
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
      height: 46px;
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

    /* Enhanced Glassmorphism Conversations Panel */
    .conv-header-banner {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.12) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 22px 26px;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }

    .conv-controls-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .conv-filter-group {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .conv-pill-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--novax-border);
      color: var(--novax-text-secondary);
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .conv-pill-btn:hover, .conv-pill-btn.active {
      background: rgba(99, 102, 241, 0.2);
      border-color: var(--novax-primary);
      color: var(--novax-cyan);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
    }

    .view-toggle-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--novax-border);
      color: var(--novax-muted);
      border-radius: 8px;
      padding: 6px 12px;
      cursor: pointer;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }

    .view-toggle-btn.active {
      background: var(--novax-primary);
      color: #fff;
      border-color: var(--novax-primary);
    }

    /* Grid vs List Container */
    .conv-grid-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
    }

    .conv-grid-container.list-mode {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    /* Glassmorphism Card */
    .conv-card {
      background: linear-gradient(135deg, rgba(22, 27, 46, 0.75) 0%, rgba(15, 20, 36, 0.85) 100%);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 18px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      overflow: hidden;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .conv-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--novax-primary), var(--novax-cyan), transparent);
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .conv-card:hover {
      border-color: rgba(99, 102, 241, 0.4);
      transform: translateY(-4px);
      box-shadow: 0 16px 36px -8px rgba(99, 102, 241, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .conv-card:hover::before {
      opacity: 1;
    }

    .conv-card-top {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 10px;
    }

    .conv-card-avatar {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%);
      border: 1px solid rgba(255, 255, 255, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      flex-shrink: 0;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .conv-card-title-group {
      flex: 1;
      min-width: 0;
    }

    .conv-card-title {
      font-size: 16px;
      font-weight: 700;
      color: #F3F4F6;
      margin: 0 0 4px 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      letter-spacing: -0.2px;
    }

    .conv-card-badges {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .conv-badge {
      font-size: 11px;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--novax-text-secondary);
      border: 1px solid rgba(255, 255, 255, 0.05);
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .conv-badge-msg {
      background: rgba(99, 102, 241, 0.15);
      color: #A5B4FC;
      border-color: rgba(99, 102, 241, 0.3);
    }

    .conv-badge-date {
      background: rgba(6, 182, 212, 0.12);
      color: var(--novax-cyan);
      border-color: rgba(6, 182, 212, 0.25);
    }

    /* Message Preview Snippet */
    .conv-snippet-box {
      background: rgba(10, 14, 26, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 10px;
      padding: 10px 12px;
      margin: 10px 0 14px 0;
      font-size: 13px;
      color: var(--novax-text-secondary);
      line-height: 1.45;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .conv-card-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .conv-btn-open {
      flex: 1;
      background: linear-gradient(135deg, var(--novax-primary) 0%, #4F46E5 100%);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 9px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
    }

    .conv-btn-open:hover {
      background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%);
      box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
      transform: translateY(-1px);
    }

    .conv-btn-icon, .conv-btn-text {
      padding: 8px 14px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--novax-text-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }

    .conv-btn-icon:hover, .conv-btn-text:hover {
      background: rgba(255, 255, 255, 0.12);
      color: var(--novax-cyan);
      border-color: rgba(6, 182, 212, 0.4);
      transform: translateY(-1px);
    }

    .conv-btn-icon.delete-btn:hover, .conv-btn-text.delete-btn:hover {
      background: rgba(239, 68, 68, 0.2);
      color: #FCA5A5;
      border-color: rgba(239, 68, 68, 0.4);
      box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
    }

    /* List Mode Card styling */
    .conv-grid-container.list-mode .conv-card {
      flex-direction: row;
      align-items: center;
      gap: 16px;
      padding: 14px 20px;
    }

    .conv-grid-container.list-mode .conv-card-top {
      margin-bottom: 0;
      flex: 1;
      min-width: 0;
    }

    .conv-grid-container.list-mode .conv-snippet-box {
      margin: 0;
      flex: 1.5;
      -webkit-line-clamp: 1;
    }

    .conv-grid-container.list-mode .conv-card-actions {
      margin-top: 0;
      padding-top: 0;
      border-top: none;
      flex: initial;
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
      gap: 6px;
      background: rgba(17, 24, 39, 0.45);
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--novax-border-light);
      position: relative;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .memory-field-item.editable {
      cursor: pointer;
    }

    .memory-field-item.editable:hover {
      border-color: rgba(99, 102, 241, 0.5);
      background: rgba(30, 41, 59, 0.65);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25), 0 0 12px rgba(99, 102, 241, 0.12);
      transform: translateY(-1px);
    }

    .memory-field-item.is-editing {
      cursor: default;
      border-color: var(--novax-primary);
      background: rgba(15, 23, 42, 0.9);
      box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
      transform: none;
    }

    .mem-edit-hint {
      font-size: 10px;
      color: var(--novax-cyan);
      font-weight: 600;
      opacity: 0;
      transform: translateX(4px);
      transition: all 0.2s ease;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .memory-field-item.editable:hover .mem-edit-hint {
      opacity: 0.85;
      transform: translateX(0);
    }

    .memory-field-empty {
      color: var(--novax-muted);
      font-style: italic;
      opacity: 0.7;
      font-weight: 400;
    }

    .memory-inline-form {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 4px;
      width: 100%;
    }

    .memory-inline-input {
      width: 100%;
      background: rgba(10, 15, 29, 0.95);
      border: 1px solid var(--novax-primary);
      border-radius: 8px;
      color: #fff;
      font-size: 13.5px;
      padding: 7px 10px;
      font-family: inherit;
      outline: none;
      box-shadow: 0 0 8px rgba(99, 102, 241, 0.25);
      resize: vertical;
      box-sizing: border-box;
    }

    .memory-inline-input:focus {
      border-color: var(--novax-cyan);
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.35);
    }

    .memory-inline-actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }

    .btn-inline-save {
      background: linear-gradient(135deg, var(--novax-primary), #4F46E5);
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 5px 12px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-inline-save:hover {
      filter: brightness(1.15);
      box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
    }

    .btn-inline-cancel {
      background: rgba(255, 255, 255, 0.08);
      color: var(--novax-muted);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-inline-cancel:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.15);
    }

    .btn-mem-del {
      background: transparent;
      border: none;
      color: var(--novax-muted);
      cursor: pointer;
      font-size: 13px;
      padding: 2px 6px;
      border-radius: 4px;
      transition: all 0.2s ease;
    }

    .btn-mem-del:hover {
      color: #F87171;
      background: rgba(239, 68, 68, 0.15);
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

    /* =========================================================
       TASK CHECKLIST MODULE STYLING
       ========================================================= */
    .task-checklist-wrapper {
      max-width: 950px;
      margin: 0 auto;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding-bottom: 40px;
    }

    .task-header-banner {
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 18px;
      padding: 22px 26px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    .task-stats-bar {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
    }

    .task-stat-card {
      background: rgba(17, 24, 39, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 10px 16px;
      display: flex;
      flex-direction: column;
      min-width: 100px;
    }

    .task-stat-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--novax-muted);
    }

    .task-stat-val {
      font-size: 20px;
      font-weight: 700;
      color: var(--novax-text);
      margin-top: 2px;
    }

    .task-progress-card {
      background: linear-gradient(135deg, rgba(22, 27, 46, 0.7) 0%, rgba(15, 20, 36, 0.8) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .task-progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }

    .task-progress-track {
      width: 100%;
      height: 8px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 999px;
      overflow: hidden;
      position: relative;
    }

    .task-progress-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #6366F1 0%, #22D3EE 60%, #10B981 100%);
      border-radius: 999px;
      transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 0 12px rgba(34, 211, 238, 0.5);
    }

    .task-create-box {
      background: linear-gradient(135deg, rgba(22, 27, 46, 0.85) 0%, rgba(15, 20, 36, 0.95) 100%);
      border: 1px solid rgba(99, 102, 241, 0.3);
      border-radius: 16px;
      padding: 18px 20px;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .task-create-inputs {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }

    .task-tag-select {
      background: rgba(10, 14, 26, 0.85);
      border: 1px solid var(--novax-border);
      border-radius: 12px;
      color: var(--novax-text);
      padding: 10px 14px;
      font-size: 13px;
      outline: none;
      cursor: pointer;
      min-width: 130px;
    }
    .task-tag-select:focus {
      border-color: var(--novax-cyan);
    }

    .task-presets-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--novax-muted);
    }

    .task-preset-chip {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 20px;
      padding: 4px 10px;
      color: var(--novax-text-secondary);
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .task-preset-chip:hover {
      background: rgba(99, 102, 241, 0.18);
      border-color: rgba(99, 102, 241, 0.4);
      color: var(--novax-cyan);
      transform: translateY(-1px);
    }

    .task-filter-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .task-tabs {
      display: flex;
      gap: 6px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--novax-border);
      border-radius: 12px;
      padding: 4px;
    }

    .task-tab-btn {
      background: transparent;
      border: none;
      color: var(--novax-muted);
      border-radius: 8px;
      padding: 6px 14px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .task-tab-btn:hover {
      color: var(--novax-text);
      background: rgba(255, 255, 255, 0.04);
    }

    .task-tab-btn.active {
      background: var(--novax-nav-active-bg);
      border: 1px solid var(--novax-nav-active-border);
      color: var(--novax-cyan);
      font-weight: 600;
    }

    .task-tab-badge {
      background: rgba(255, 255, 255, 0.08);
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 11px;
    }
    .task-tab-btn.active .task-tab-badge {
      background: rgba(34, 211, 238, 0.2);
      color: var(--novax-cyan);
    }

    .task-list-container {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .task-item-card {
      background: rgba(17, 24, 39, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 14px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .task-item-card:hover {
      background: rgba(22, 32, 54, 0.85);
      border-color: rgba(99, 102, 241, 0.35);
      transform: translateY(-1px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    .task-item-card.completed {
      background: rgba(13, 20, 32, 0.5);
      border-color: rgba(16, 185, 129, 0.2);
    }

    .task-tick-btn {
      width: 26px;
      height: 26px;
      min-width: 26px;
      border-radius: 8px;
      border: 2px solid rgba(255, 255, 255, 0.25);
      background: rgba(255, 255, 255, 0.03);
      cursor: pointer;
      display: grid;
      place-items: center;
      transition: all 0.2s ease;
      padding: 0;
      color: transparent;
    }

    .task-tick-btn:hover {
      border-color: var(--novax-cyan);
      background: rgba(34, 211, 238, 0.12);
      transform: scale(1.08);
    }

    .task-item-card.completed .task-tick-btn {
      background: linear-gradient(135deg, #10B981 0%, #059669 100%);
      border-color: #10B981;
      color: white;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }

    .task-content {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .task-title {
      font-size: 15px;
      font-weight: 500;
      color: var(--novax-text);
      word-break: break-word;
      transition: all 0.2s ease;
    }

    .task-item-card.completed .task-title {
      text-decoration: line-through;
      color: var(--novax-muted);
      opacity: 0.75;
    }

    .task-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--novax-muted);
    }

    .task-tag-pill {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 6px;
      text-transform: capitalize;
    }

    .task-tag-urgent {
      background: rgba(239, 68, 68, 0.15);
      color: #FCA5A5;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .task-tag-work {
      background: rgba(99, 102, 241, 0.15);
      color: #A5B4FC;
      border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .task-tag-study {
      background: rgba(34, 211, 238, 0.15);
      color: #67E8F9;
      border: 1px solid rgba(34, 211, 238, 0.3);
    }
    .task-tag-personal {
      background: rgba(16, 185, 129, 0.15);
      color: #6EE7B7;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .task-tag-general {
      background: rgba(148, 163, 184, 0.15);
      color: #CBD5E1;
      border: 1px solid rgba(148, 163, 184, 0.25);
    }

    .task-status-pill {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .task-status-completed {
      background: rgba(16, 185, 129, 0.15);
      color: #34D399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .task-status-pending {
      background: rgba(245, 158, 11, 0.12);
      color: #FBBF24;
      border: 1px solid rgba(245, 158, 11, 0.25);
    }

    .task-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .task-btn-action {
      background: transparent;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      color: var(--novax-muted);
      padding: 5px 10px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .task-btn-action:hover {
      background: rgba(255, 255, 255, 0.06);
      color: var(--novax-text);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .task-btn-action.delete:hover {
      background: rgba(239, 68, 68, 0.15);
      border-color: rgba(239, 68, 68, 0.4);
      color: #FCA5A5;
    }

    /* =========================================================
       SETTINGS MODULE STYLING
       ========================================================= */
    .settings-wrapper {
      max-width: 850px;
      margin: 0 auto;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 24px;
      padding-bottom: 50px;
    }

    .settings-banner {
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 18px;
      padding: 22px 26px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    .settings-card {
      background: var(--novax-surface);
      border: 1px solid var(--novax-border);
      border-radius: 16px;
      padding: 22px 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }

    .settings-card-header {
      border-bottom: 1px solid var(--novax-border-light);
      padding-bottom: 12px;
    }

    .settings-card-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--novax-text);
      margin: 0 0 4px 0;
    }

    .settings-card-desc {
      font-size: 13px;
      color: var(--novax-muted);
      margin: 0;
    }

    .settings-field-group {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .settings-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }

    .settings-label-group {
      display: flex;
      flex-direction: column;
      gap: 3px;
      max-width: 480px;
    }

    .settings-label {
      font-size: 14px;
      font-weight: 600;
      color: var(--novax-text);
    }

    .settings-sublabel {
      font-size: 12px;
      color: var(--novax-muted);
      line-height: 1.4;
    }

    /* Toggle Switch */
    .switch-container {
      display: inline-flex;
      align-items: center;
      cursor: pointer;
      user-select: none;
      gap: 10px;
    }

    .switch-track {
      width: 44px;
      height: 24px;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 999px;
      position: relative;
      transition: background 0.25s ease;
    }

    .switch-track.active {
      background: var(--novax-primary);
    }

    .switch-knob {
      width: 18px;
      height: 18px;
      background: white;
      border-radius: 50%;
      position: absolute;
      top: 3px;
      left: 3px;
      transition: transform 0.25s ease;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }

    .switch-track.active .switch-knob {
      transform: translateX(20px);
    }

    .settings-feedback {
      font-size: 12px;
      padding: 8px 12px;
      border-radius: 8px;
      display: none;
    }
    .settings-feedback.success {
      display: block;
      background: rgba(34, 197, 94, 0.12);
      color: var(--novax-success);
      border: 1px solid rgba(34, 197, 94, 0.25);
    }
    .settings-feedback.error {
      display: block;
      background: rgba(239, 68, 68, 0.12);
      color: #FCA5A5;
      border: 1px solid rgba(239, 68, 68, 0.25);
    }

    /* Themes & Typography Classes */
    body.theme-midnight {
      --novax-bg: #0A0E1A;
      --novax-sidebar: #0F172A;
      --novax-surface: #1E293B;
      --novax-border: #334155;
    }
    body.theme-oled {
      --novax-bg: #000000;
      --novax-sidebar: #050505;
      --novax-surface: #0C0C0C;
      --novax-border: #1F1F1F;
    }
    body.font-large {
      font-size: 16px;
    }
    body.font-large .chat-bubble {
      font-size: 16px;
    }
    body.font-large .task-title {
      font-size: 17px;
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
          <div class="nav-item active" id="nav-item-chat" onclick="showPanel('chat-panel')">
            <span>Active Chat</span>
          </div>
          <div class="nav-item" id="nav-item-conversations-panel" onclick="showPanel('conversations-panel')">
            <span>Conversations</span>
          </div>
          <div class="nav-item" id="nav-item-memory-panel" onclick="showPanel('memory-panel')">
            <span>Memory</span>
          </div>
          <div class="nav-item" id="nav-item-projects-panel" onclick="showPanel('projects-panel')">
            <span>Projects</span>
          </div>
          <div class="nav-item" id="nav-item-tasks-panel" onclick="showPanel('tasks-panel')">
            <span>Tasks</span>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-item" id="nav-item-settings-panel" onclick="showPanel('settings-panel')">
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
        <div id="chat-panel" class="panel-view active" style="position: relative;">
          <!-- Drag and Drop Overlay -->
          <div id="chat-drop-overlay" class="chat-drop-overlay">
            <div class="drop-overlay-title">Drop file to attach & analyze</div>
            <div class="drop-overlay-subtitle">PDF, Word, Code, Data, Text, Markdown, Images</div>
          </div>

          <div id="chat-messages" class="chat-container">
            <div class="chat-bubble-wrapper assistant">
              <div class="chat-bubble assistant">
                Welcome to NOVAX! I am your personal AI assistant. How can I help you today?
              </div>
            </div>
          </div>
          <div class="chat-footer-wrapper">

            <!-- Attachment Preview Bar (hidden by default) -->
            <div id="chat-attachment-preview" class="chat-attachment-preview" style="display: none;">
              <div class="attachment-info">
                <span id="attachment-icon" class="attachment-icon">FILE</span>
                <span id="attachment-name" class="attachment-name"></span>
                <span id="attachment-size" class="attachment-size"></span>
              </div>
              <button type="button" class="btn-remove-attachment" onclick="clearAttachedFile()" title="Remove file">✕</button>
            </div>

            <div class="chat-input-bar">
              <input type="file" id="chat-file-input" style="display: none;" onchange="handleFileSelected(event)" />
              <button type="button" class="btn-attach" onclick="document.getElementById('chat-file-input').click()" title="Attach Document, PDF, Code, or Data File">
                + File
              </button>
              <input type="text" id="user-input" class="chat-input" placeholder="Ask NOVAX anything, manage tasks/projects, or discuss attached files..." onkeydown="if(event.key==='Enter') sendMessage()" />
              <button class="btn-send" onclick="sendMessage()">Send</button>
            </div>
          </div>
        </div>

        <!-- Conversations Panel -->
        <div id="conversations-panel" class="panel-view">
          <!-- Banner Header -->
          <div class="conv-header-banner">
            <div>
              <h2 style="font-size:24px; font-weight:800; color:var(--novax-cyan); margin:0 0 6px 0;">
                Conversations
              </h2>
              <p style="color:var(--novax-text-secondary); font-size:14px; margin:0;">
                All your previous chats are stored here. Reopen, write on, rename, or delete any past conversation.
              </p>
            </div>
            <div style="display:flex; gap:12px; align-items:center;">
              <button class="btn-primary" onclick="startNewChatFromPanel()" style="padding:10px 18px; width:auto; display:inline-flex; align-items:center; gap:6px;">
                + New Chat
              </button>
            </div>
          </div>

          <!-- Controls Bar: Filter Pills, Search, Sort & View Toggles -->
          <div class="conv-controls-bar">
            <div class="conv-filter-group">
              <button class="conv-pill-btn active" id="conv-filter-all" onclick="setConvFilter('all')">All (<span id="conv-count-all">0</span>)</button>
              <button class="conv-pill-btn" id="conv-filter-today" onclick="setConvFilter('today')">Today (<span id="conv-count-today">0</span>)</button>
              <button class="conv-pill-btn" id="conv-filter-week" onclick="setConvFilter('week')">This Week (<span id="conv-count-week">0</span>)</button>
            </div>

            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
              <div style="position:relative; width:240px;">
                <input type="text" id="search-conversations-input" class="form-control" placeholder="Search title or text..." oninput="filterConversations()" />
              </div>

              <select id="conv-sort-select" class="form-control" style="width:130px; cursor:pointer;" onchange="filterConversations()">
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="messages">Most Messages</option>
              </select>

              <div style="display:flex; gap:4px; background:rgba(255,255,255,0.03); border:1px solid var(--novax-border); border-radius:10px; padding:3px;">
                <button class="view-toggle-btn active" id="btn-view-grid" onclick="setConvViewMode('grid')" title="Grid View">
                  <span>Grid</span>
                </button>
                <button class="view-toggle-btn" id="btn-view-list" onclick="setConvViewMode('list')" title="List View">
                  <span>List</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Conversations Grid / List Container -->
          <div id="conversations-grid" class="conv-grid-container"></div>
        </div>

        <!-- Personal Memory Center Panel -->
        <div id="memory-panel" class="panel-view">
          <div class="memory-center-wrapper">

            <!-- Banner Header -->
            <div class="memory-header-banner">
              <div>
                <h1 style="font-size:24px; font-weight:800; color:var(--novax-text); margin:0 0 6px 0;">
                  Personal Memory Center
                </h1>
                <p style="color:var(--novax-text-secondary); font-size:14px; margin:0;">
                  Manage your saved personal profile, preferences, and memories. You control what NOVAX remembers.
                </p>
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



        <!-- Projects Panel -->
        <div id="projects-panel" class="panel-view">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px;">
            <div>
              <h2 style="color:var(--novax-cyan); margin:0;">Projects Workspace</h2>
              <p style="color:var(--novax-muted); font-size:14px; margin:4px 0 0 0;">Create and manage your projects, outlines, and outer view details.</p>
            </div>
            <input type="text" id="search-projects-input" class="form-control" style="width:240px;" placeholder="Search projects..." oninput="filterProjects()" />
          </div>

          <!-- Projects Grid Container -->
          <div id="projects-grid" class="conv-grid-container" style="margin-bottom:24px;"></div>

          <!-- Bottom Add New Project Bar -->
          <div style="background:linear-gradient(135deg, rgba(22, 27, 46, 0.8) 0%, rgba(15, 20, 36, 0.9) 100%); border:1px solid rgba(255, 255, 255, 0.08); border-radius:16px; padding:18px 22px; backdrop-filter:blur(12px); display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
            <div style="flex:1; min-width:240px;">
              <input type="text" id="new-project-name-input" class="form-control" placeholder="Enter new project name (e.g. Hospital Management System)..." onkeydown="if(event.key==='Enter') addQuickProject()" />
            </div>
            <button class="btn-primary" onclick="addQuickProject()" style="padding:10px 22px; width:auto; font-weight:600; font-size:13px; display:inline-flex; align-items:center; gap:6px;">
              + Add Project
            </button>
          </div>
        </div>

        <!-- Tasks Panel -->
        <div id="tasks-panel" class="panel-view">
          <div class="task-checklist-wrapper">

            <!-- Banner Header -->
            <div class="task-header-banner">
              <div>
                <h1 style="font-size:24px; font-weight:800; color:var(--novax-text); margin:0 0 6px 0; display:flex; align-items:center; gap:10px;">
                  <span>Task Checklist</span>
                  <span style="font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px; background:rgba(34,211,238,0.15); color:var(--novax-cyan); border:1px solid rgba(34,211,238,0.3);">Productivity</span>
                </h1>
                <p style="color:var(--novax-text-secondary); font-size:14px; margin:0;">
                  Create items, stay focused, and check off completed tasks.
                </p>
              </div>

              <!-- Stats Cards -->
              <div class="task-stats-bar">
                <div class="task-stat-card">
                  <span class="task-stat-label">Total</span>
                  <span class="task-stat-val" id="task-stat-total">0</span>
                </div>
                <div class="task-stat-card">
                  <span class="task-stat-label">Pending</span>
                  <span class="task-stat-val" id="task-stat-pending" style="color:#FBBF24;">0</span>
                </div>
                <div class="task-stat-card">
                  <span class="task-stat-label">Completed</span>
                  <span class="task-stat-val" id="task-stat-completed" style="color:#34D399;">0</span>
                </div>
              </div>
            </div>

            <!-- Progress Bar Widget -->
            <div class="task-progress-card">
              <div class="task-progress-header">
                <span style="color:var(--novax-text); font-weight:600; display:flex; align-items:center; gap:6px;">
                  <span>Completion Progress</span>
                </span>
                <span id="task-progress-percentage" style="font-weight:700; color:var(--novax-cyan);">0%</span>
              </div>
              <div class="task-progress-track">
                <div id="task-progress-fill" class="task-progress-fill"></div>
              </div>
            </div>

            <!-- Add Task Creator Box -->
            <div class="task-create-box">
              <div class="task-create-inputs">
                <input 
                  type="text" 
                  id="new-task-title-input" 
                  class="form-control" 
                  style="flex:1; min-width:240px;" 
                  placeholder="Enter a new task to do (e.g. Implement data processing pipeline)..." 
                  onkeydown="if(event.key==='Enter') addQuickTask()" 
                />
                <select id="new-task-tag-select" class="task-tag-select">
                  <option value="General">General</option>
                  <option value="Work">Work</option>
                  <option value="Study">Study</option>
                  <option value="Personal">Personal</option>
                  <option value="Urgent">Urgent</option>
                  <option value="Coding">Coding</option>
                </select>
                <button class="btn-primary" onclick="addQuickTask()" style="padding:10px 22px; width:auto; font-weight:600; font-size:13px; display:inline-flex; align-items:center; gap:6px; white-space:nowrap;">
                  + Add Task
                </button>
              </div>

              <!-- Quick Presets -->
              <div class="task-presets-bar">
                <span>Quick add:</span>
                <button class="task-preset-chip" onclick="addPresetTask('Code review & commit changes', 'Coding')">+ Code Review</button>
                <button class="task-preset-chip" onclick="addPresetTask('Read research paper on AI agents', 'Study')">+ AI Paper</button>
                <button class="task-preset-chip" onclick="addPresetTask('Daily team sync & roadmap', 'Work')">+ Daily Sync</button>
                <button class="task-preset-chip" onclick="addPresetTask('Review project architecture', 'Personal')">+ Architecture</button>
              </div>
            </div>

            <!-- Filter & Search Controls -->
            <div class="task-filter-bar">
              <div class="task-tabs">
                <button class="task-tab-btn active" id="task-tab-all" onclick="setTaskFilter('all')">
                  All <span class="task-tab-badge" id="task-count-all">0</span>
                </button>
                <button class="task-tab-btn" id="task-tab-pending" onclick="setTaskFilter('pending')">
                  Active <span class="task-tab-badge" id="task-count-pending">0</span>
                </button>
                <button class="task-tab-btn" id="task-tab-completed" onclick="setTaskFilter('completed')">
                  Completed <span class="task-tab-badge" id="task-count-completed">0</span>
                </button>
              </div>

              <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                <input 
                  type="text" 
                  id="search-tasks-input" 
                  class="form-control" 
                  style="width:220px;" 
                  placeholder="Search checklist..." 
                  oninput="filterTasks()" 
                />
                <button 
                  id="btn-clear-completed-tasks" 
                  class="btn-logout" 
                  onclick="clearCompletedTasksAction()" 
                  style="display:none; color:#FCA5A5; border-color:rgba(239,68,68,0.4); padding:8px 14px; font-weight:500;"
                >
                  Clear Completed
                </button>
              </div>
            </div>

            <!-- Tasks Checklist Container -->
            <div id="tasks-checklist-container" class="task-list-container"></div>

          </div>
        </div>

        <!-- Settings Panel -->
        <div id="settings-panel" class="panel-view">
          <div class="settings-wrapper">

            <!-- Banner Header -->
            <div class="settings-banner">
              <div>
                <h1 style="font-size:24px; font-weight:800; color:var(--novax-text); margin:0 0 6px 0;">
                  Settings
                </h1>
                <p style="color:var(--novax-text-secondary); font-size:14px; margin:0;">
                  Manage your account, AI behavior, appearance, and workspace data.
                </p>
              </div>
            </div>

            <!-- Card 1: Account & Profile -->
            <div class="settings-card">
              <div class="settings-card-header">
                <h2 class="settings-card-title">Account & Profile</h2>
                <p class="settings-card-desc">Your personal identity and login credentials.</p>
              </div>

              <div id="profile-settings-feedback" class="settings-feedback"></div>

              <div class="settings-field-group">
                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Display Name</span>
                    <span class="settings-sublabel">Your name as recognized by NOVAX during conversations.</span>
                  </div>
                  <input type="text" id="settings-name-input" class="form-control" style="width:240px;" placeholder="Your Name" />
                </div>

                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Email Address</span>
                    <span class="settings-sublabel">Registered account email.</span>
                  </div>
                  <span id="settings-email-display" style="font-size:13px; color:var(--novax-muted); background:rgba(255,255,255,0.04); padding:6px 12px; border-radius:8px; border:1px solid var(--novax-border);">email@example.com</span>
                </div>

                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Change Password</span>
                    <span class="settings-sublabel">Leave blank if you do not wish to change your password.</span>
                  </div>
                  <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <input type="password" id="settings-password-input" class="form-control" style="width:240px;" placeholder="New Password" />
                  </div>
                </div>

                <div style="display:flex; justify-content:flex-end; margin-top:8px;">
                  <button class="btn-primary" onclick="saveProfileSettings()" style="width:auto; padding:8px 20px; font-weight:600; font-size:13px;">
                    Save Profile
                  </button>
                </div>
              </div>
            </div>

            <!-- Card 2: AI Response Style -->
            <div class="settings-card">
              <div class="settings-card-header">
                <h2 class="settings-card-title">AI Response Style</h2>
                <p class="settings-card-desc">Control how NOVAX reasons and answers your messages.</p>
              </div>

              <div id="ai-settings-feedback" class="settings-feedback"></div>

              <div class="settings-field-group">
                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Response Mode</span>
                    <span class="settings-sublabel">Choose how concise or detailed answers should be.</span>
                  </div>
                  <select id="settings-response-style-select" class="form-control" style="width:240px; cursor:pointer;" onchange="saveAISettings()">
                    <option value="default">Default (Balanced & Helpful)</option>
                    <option value="concise">Concise (Direct & Short)</option>
                    <option value="code_first">Code-First (Code Centric)</option>
                    <option value="in_depth">In-Depth (Detailed Analysis)</option>
                  </select>
                </div>

                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Live Web Search</span>
                    <span class="settings-sublabel">Allow NOVAX to look up current live facts and news feeds.</span>
                  </div>
                  <div class="switch-container" onclick="toggleWebSearchSetting()">
                    <div id="settings-search-track" class="switch-track active">
                      <div class="switch-knob"></div>
                    </div>
                    <span id="settings-search-status" style="font-size:13px; color:var(--novax-text-secondary); min-width:60px;">Enabled</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Card 3: Appearance -->
            <div class="settings-card">
              <div class="settings-card-header">
                <h2 class="settings-card-title">Appearance</h2>
                <p class="settings-card-desc">Personalize your workspace visual theme and typography.</p>
              </div>

              <div class="settings-field-group">
                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Color Theme</span>
                    <span class="settings-sublabel">Select your preferred background palette.</span>
                  </div>
                  <select id="settings-theme-select" class="form-control" style="width:240px; cursor:pointer;" onchange="applyAndSaveAppearance()">
                    <option value="dark">Dark Theme (Default)</option>
                    <option value="midnight">Midnight Navy</option>
                    <option value="oled">OLED Pure Black</option>
                  </select>
                </div>

                <div class="settings-row">
                  <div class="settings-label-group">
                    <span class="settings-label">Font Size</span>
                    <span class="settings-sublabel">Adjust reading comfort across the interface.</span>
                  </div>
                  <select id="settings-font-size-select" class="form-control" style="width:240px; cursor:pointer;" onchange="applyAndSaveAppearance()">
                    <option value="normal">Normal</option>
                    <option value="large">Large</option>
                  </select>
                </div>
              </div>
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
      } else if (panelId === 'projects-panel') {
        const navItem = document.getElementById('nav-item-projects-panel');
        if (navItem) navItem.classList.add('active');
        loadProjectsList();
      } else if (panelId === 'memory-panel') {
        const navItem = document.getElementById('nav-item-memory-panel');
        if (navItem) navItem.classList.add('active');
        loadMemories();
      } else if (panelId === 'tasks-panel') {
        const navItem = document.getElementById('nav-item-tasks-panel');
        if (navItem) navItem.classList.add('active');
        loadTasksList();
      } else if (panelId === 'settings-panel') {
        const navItem = document.getElementById('nav-item-settings-panel');
        if (navItem) navItem.classList.add('active');
        loadSettings();
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

    let currentConvFilter = 'all';
    let currentConvViewMode = 'grid';

    function setConvViewMode(mode) {
      currentConvViewMode = mode;
      const grid = document.getElementById('conversations-grid');
      const btnGrid = document.getElementById('btn-view-grid');
      const btnList = document.getElementById('btn-view-list');

      if (grid) {
        if (mode === 'list') {
          grid.classList.add('list-mode');
        } else {
          grid.classList.remove('list-mode');
        }
      }
      if (btnGrid) btnGrid.classList.toggle('active', mode === 'grid');
      if (btnList) btnList.classList.toggle('active', mode === 'list');
      filterConversations();
    }

    function setConvFilter(filter) {
      currentConvFilter = filter;
      ['all', 'today', 'week'].forEach(f => {
        const el = document.getElementById('conv-filter-' + f);
        if (el) el.classList.toggle('active', f === filter);
      });
      filterConversations();
    }

    function updateConvCounts(conversations) {
      const now = Math.floor(Date.now() / 1000);
      const oneDay = 86400;
      const oneWeek = 7 * 86400;

      const total = conversations.length;
      const today = conversations.filter(c => (now - (c.last_message_at || c.created_at)) < oneDay).length;
      const week = conversations.filter(c => (now - (c.last_message_at || c.created_at)) < oneWeek).length;

      const elAll = document.getElementById('conv-count-all');
      const elToday = document.getElementById('conv-count-today');
      const elWeek = document.getElementById('conv-count-week');

      if (elAll) elAll.textContent = total;
      if (elToday) elToday.textContent = today;
      if (elWeek) elWeek.textContent = week;
    }

    function formatRelativeTime(timestamp) {
      if (!timestamp) return 'Unknown date';
      const now = Math.floor(Date.now() / 1000);
      const diff = now - timestamp;

      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;

      const date = new Date(timestamp * 1000);
      const isThisYear = date.getFullYear() === new Date().getFullYear();
      return date.toLocaleDateString([], isThisYear ? { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' } : { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function startNewChatFromPanel() {
      startNewChat();
    }

    async function loadConversationsList() {
      try {
        const res = await fetch('/api/conversations');
        if (!res.ok) return;
        const conversations = await res.json();
        allConversationsCache = conversations || [];
        updateConvCounts(allConversationsCache);
        renderSidebarConversations(allConversationsCache);
        filterConversations();
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
        grid.innerHTML = `
          <div style="grid-column: 1 / -1; background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(12px); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 40px 20px; text-align: center;">
            <h3 style="color: var(--novax-text); font-size: 16px; margin: 0 0 6px 0;">No conversations found</h3>
            <p style="color: var(--novax-muted); font-size: 13px; margin: 0 0 16px 0;">Try adjusting your search query or start a brand new conversation.</p>
            <button class="btn-primary" onclick="startNewChatFromPanel()" style="width: auto; padding: 8px 18px;">
              + Start New Chat
            </button>
          </div>
        `;
        return;
      }

      conversations.forEach(conv => {
        const card = document.createElement('div');
        card.className = 'conv-card';

        const lastActive = conv.last_message_at || conv.created_at;
        const timeStr = formatRelativeTime(lastActive);
        const msgCount = conv.message_count || 0;
        const rawSnippet = conv.last_message || 'No messages yet in this conversation.';
        const snippetText = escapeHtml(rawSnippet);

        const initialLetter = (conv.title || 'C').trim().charAt(0).toUpperCase();

        card.innerHTML = `
          <div>
            <div class="conv-card-top">
              <div class="conv-card-avatar" style="font-weight:700; color:var(--novax-cyan); font-size:16px;">${initialLetter}</div>
              <div class="conv-card-title-group">
                <h3 class="conv-card-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</h3>
                <div class="conv-card-badges">
                  <span class="conv-badge conv-badge-date">${timeStr}</span>
                  <span class="conv-badge conv-badge-msg">${msgCount} msg${msgCount === 1 ? '' : 's'}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="conv-card-actions" style="margin-top:14px;">
            <button class="conv-btn-open" onclick="openConversation('${conv.id}')">
              Open & Write
            </button>
            <button class="conv-btn-text" onclick="renameConversationPrompt('${conv.id}', '${escapeHtml(conv.title).replace(/'/g, "\\'")}')" title="Rename Conversation">
              Rename
            </button>
            <button class="conv-btn-text delete-btn" onclick="deleteConversation('${conv.id}')" title="Delete Conversation">
              Delete
            </button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterConversations() {
      const q = (document.getElementById('search-conversations-input')?.value || '').toLowerCase().trim();
      const sortVal = document.getElementById('conv-sort-select')?.value || 'newest';

      const now = Math.floor(Date.now() / 1000);
      const oneDay = 86400;
      const oneWeek = 7 * 86400;

      let filtered = [...allConversationsCache];

      if (currentConvFilter === 'today') {
        filtered = filtered.filter(c => (now - (c.last_message_at || c.created_at)) < oneDay);
      } else if (currentConvFilter === 'week') {
        filtered = filtered.filter(c => (now - (c.last_message_at || c.created_at)) < oneWeek);
      }

      if (q) {
        filtered = filtered.filter(c =>
          (c.title || '').toLowerCase().includes(q) ||
          (c.last_message || '').toLowerCase().includes(q)
        );
      }

      if (sortVal === 'oldest') {
        filtered.sort((a, b) => (a.last_message_at || a.created_at) - (b.last_message_at || b.created_at));
      } else if (sortVal === 'messages') {
        filtered.sort((a, b) => (b.message_count || 0) - (a.message_count || 0));
      } else {
        filtered.sort((a, b) => (b.last_message_at || b.created_at) - (a.last_message_at || a.created_at));
      }

      renderGridConversations(filtered);
    }

    /* --- Projects Workspace JS --- */
    let allProjectsCache = [];

    async function loadProjectsList() {
      try {
        const res = await fetch('/api/projects');
        if (!res.ok) return;
        const projects = await res.json();
        allProjectsCache = projects || [];
        filterProjects();
      } catch (e) {}
    }

    function renderGridProjects(projects) {
      const grid = document.getElementById('projects-grid');
      if (!grid) return;
      grid.innerHTML = '';

      if (!projects || projects.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1 / -1; background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(12px); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 36px 20px; text-align: center;">
            <h3 style="color: var(--novax-text); font-size: 16px; margin: 0 0 6px 0;">No projects added yet</h3>
            <p style="color: var(--novax-muted); font-size: 13px; margin: 0;">Use the "+ Add Project" bar below to enter a new project name.</p>
          </div>
        `;
        return;
      }

      projects.forEach(proj => {
        const card = document.createElement('div');
        card.className = 'conv-card';

        const descText = proj.description ? escapeHtml(proj.description) : 'No details or outline added yet.';
        const initialLetter = (proj.name || 'P').trim().charAt(0).toUpperCase();

        card.innerHTML = `
          <div>
            <div class="conv-card-top">
              <div class="conv-card-avatar" style="font-weight:700; color:var(--novax-cyan); font-size:16px;">${initialLetter}</div>
              <div class="conv-card-title-group">
                <h3 class="conv-card-title" title="${escapeHtml(proj.name)}">${escapeHtml(proj.name)}</h3>
                <div class="conv-card-badges">
                  <span class="conv-badge conv-badge-date">Project</span>
                </div>
              </div>
            </div>

            <div style="font-size:13px; color:var(--novax-text-secondary); margin:12px 0; line-height:1.45; background:rgba(10,14,26,0.5); padding:10px 12px; border-radius:10px; border:1px solid rgba(255,255,255,0.05);">
              <strong>Details / Outline:</strong><br/>
              ${descText}
            </div>
          </div>

          <div class="conv-card-actions" style="margin-top:14px;">
            <button class="conv-btn-open" onclick="editProjectDetailsPrompt('${proj.id}', '${escapeHtml(proj.name).replace(/'/g, "\\'")}', '${escapeHtml(proj.description || '').replace(/'/g, "\\'")}')">
              Edit Details / Outline
            </button>
            <button class="conv-btn-text delete-btn" onclick="deleteProjectAction('${proj.id}')" title="Delete Project">
              Delete
            </button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterProjects() {
      const q = (document.getElementById('search-projects-input')?.value || '').toLowerCase().trim();
      if (!q) {
        renderGridProjects(allProjectsCache);
        return;
      }
      const filtered = allProjectsCache.filter(p =>
        (p.name || '').toLowerCase().includes(q) ||
        (p.description || '').toLowerCase().includes(q)
      );
      renderGridProjects(filtered);
    }

    async function addQuickProject() {
      const input = document.getElementById('new-project-name-input');
      if (!input) return;
      const name = input.value.trim();
      if (!name) {
        alert('Please enter a project name.');
        return;
      }

      try {
        const res = await fetch('/api/projects/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name })
        });
        const data = await res.json();
        if (data.success) {
          input.value = '';
          allProjectsCache = data.projects || [];
          filterProjects();
        } else {
          alert('Failed to add project: ' + (data.error || 'Server error'));
        }
      } catch (e) {
        alert('Failed to add project. Please refresh your browser tab and try again.');
      }
    }

    async function editProjectDetailsPrompt(projId, currentName, currentDesc) {
      const newDesc = prompt(`Update details / outline for project "${currentName}":`, currentDesc);
      if (newDesc === null) return;

      try {
        const res = await fetch('/api/projects/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: projId, name: currentName, description: newDesc.trim() })
        });
        const data = await res.json();
        if (data.success) {
          allProjectsCache = data.projects || [];
          filterProjects();
        }
      } catch (e) {
        alert('Failed to update project details.');
      }
    }

    async function deleteProjectAction(projId) {
      if (!confirm('Are you sure you want to delete this project?')) return;
      try {
        const res = await fetch('/api/projects/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: projId })
        });
        const data = await res.json();
        if (data.success) {
          allProjectsCache = data.projects || [];
          filterProjects();
        }
      } catch (e) {}
    }

    // =========================================================
    // TASK CHECKLIST MODULE JAVASCRIPT
    // =========================================================
    let allTasksCache = [];
    let currentTaskFilter = 'all';

    async function loadTasksList() {
      try {
        const res = await fetch('/api/tasks');
        if (!res.ok) return;
        const tasks = await res.json();
        allTasksCache = tasks || [];
        filterTasks();
      } catch (e) {}
    }

    function setTaskFilter(filter) {
      currentTaskFilter = filter;
      document.querySelectorAll('.task-tab-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('task-tab-' + filter);
      if (activeBtn) activeBtn.classList.add('active');
      filterTasks();
    }

    function filterTasks() {
      const q = (document.getElementById('search-tasks-input')?.value || '').toLowerCase().trim();
      let list = allTasksCache.slice();

      if (currentTaskFilter === 'pending') {
        list = list.filter(t => !t.completed);
      } else if (currentTaskFilter === 'completed') {
        list = list.filter(t => !!t.completed);
      }

      if (q) {
        list = list.filter(t => 
          (t.title || '').toLowerCase().includes(q) ||
          (t.tag || '').toLowerCase().includes(q)
        );
      }

      updateTaskStats(allTasksCache);
      renderTasksChecklist(list);
    }

    function updateTaskStats(tasks) {
      const total = tasks.length;
      const completed = tasks.filter(t => !!t.completed).length;
      const pending = total - completed;
      const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

      const totalEl = document.getElementById('task-stat-total');
      const pendingEl = document.getElementById('task-stat-pending');
      const completedEl = document.getElementById('task-stat-completed');
      const countAll = document.getElementById('task-count-all');
      const countPending = document.getElementById('task-count-pending');
      const countCompleted = document.getElementById('task-count-completed');
      const pctEl = document.getElementById('task-progress-percentage');
      const fillEl = document.getElementById('task-progress-fill');
      const clearBtn = document.getElementById('btn-clear-completed-tasks');

      if (totalEl) totalEl.innerText = total;
      if (pendingEl) pendingEl.innerText = pending;
      if (completedEl) completedEl.innerText = completed;
      if (countAll) countAll.innerText = total;
      if (countPending) countPending.innerText = pending;
      if (countCompleted) countCompleted.innerText = completed;
      if (pctEl) pctEl.innerText = `${pct}%`;
      if (fillEl) fillEl.style.width = `${pct}%`;

      if (clearBtn) {
        clearBtn.style.display = completed > 0 ? 'inline-block' : 'none';
      }
    }

    function getTagPillClass(tag) {
      const lower = (tag || '').toLowerCase();
      if (lower.includes('urgent')) return 'task-tag-urgent';
      if (lower.includes('work')) return 'task-tag-work';
      if (lower.includes('study') || lower.includes('read')) return 'task-tag-study';
      if (lower.includes('personal')) return 'task-tag-personal';
      return 'task-tag-general';
    }

    function renderTasksChecklist(tasks) {
      const container = document.getElementById('tasks-checklist-container');
      if (!container) return;
      container.innerHTML = '';

      if (!tasks || tasks.length === 0) {
        let msg = 'No tasks in this view yet.';
        let sub = 'Type a task above and press Enter or "+ Add Task" to get started!';
        if (currentTaskFilter === 'completed') {
          msg = 'No completed tasks yet';
          sub = 'Check off items in your active tasks list to see them here.';
        } else if (currentTaskFilter === 'pending') {
          msg = 'All caught up!';
          sub = 'No pending tasks right now. Great job!';
        }

        container.innerHTML = `
          <div style="background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(12px); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 36px 20px; text-align: center;">
            <h3 style="color: var(--novax-text); font-size: 16px; margin: 0 0 6px 0;">${msg}</h3>
            <p style="color: var(--novax-muted); font-size: 13px; margin: 0;">${sub}</p>
          </div>
        `;
        return;
      }

      tasks.forEach(task => {
        const isDone = !!task.completed;
        const card = document.createElement('div');
        card.className = `task-item-card ${isDone ? 'completed' : ''}`;
        card.id = `task-card-${task.id}`;

        const createdDate = task.created_at ? new Date(task.created_at * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
        const tagClass = getTagPillClass(task.tag);

        card.innerHTML = `
          <button class="task-tick-btn" onclick="toggleTaskChecklist('${task.id}', ${isDone})" title="${isDone ? 'Mark as Incomplete' : 'Mark as Completed'}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="display:${isDone ? 'block' : 'none'};">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </button>

          <div class="task-content">
            <div class="task-title">${escapeHtml(task.title)}</div>
            <div class="task-meta">
              <span class="task-tag-pill ${tagClass}">${escapeHtml(task.tag || 'General')}</span>
              ${isDone 
                ? '<span class="task-status-pill task-status-completed">✓ Completed</span>' 
                : '<span class="task-status-pill task-status-pending">○ Pending</span>'
              }
              ${createdDate ? `<span>• ${createdDate}</span>` : ''}
            </div>
          </div>

          <div class="task-actions">
            <button class="task-btn-action" onclick="editTaskPrompt('${task.id}', '${escapeHtml(task.title).replace(/'/g, "\\'")}', '${escapeHtml(task.tag || 'General').replace(/'/g, "\\'")}')" title="Edit Task">
              Edit
            </button>
            <button class="task-btn-action delete" onclick="deleteTaskAction('${task.id}')" title="Delete Task">
              Delete
            </button>
          </div>
        `;
        container.appendChild(card);
      });
    }

    async function addQuickTask() {
      const input = document.getElementById('new-task-title-input');
      const tagSelect = document.getElementById('new-task-tag-select');
      if (!input) return;
      const title = input.value.trim();
      if (!title) {
        input.focus();
        return;
      }
      const tag = tagSelect ? tagSelect.value : 'General';

      try {
        const res = await fetch('/api/tasks/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, tag })
        });
        const data = await res.json();
        if (data.success) {
          input.value = '';
          allTasksCache = data.tasks || [];
          filterTasks();
        } else {
          alert('Failed to create task: ' + (data.error || 'Server error'));
        }
      } catch (e) {
        alert('Failed to add task. Please try again.');
      }
    }

    async function addPresetTask(title, tag) {
      try {
        const res = await fetch('/api/tasks/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, tag })
        });
        const data = await res.json();
        if (data.success) {
          allTasksCache = data.tasks || [];
          filterTasks();
        }
      } catch (e) {}
    }

    async function toggleTaskChecklist(taskId, currentCompleted) {
      try {
        const newStatus = !currentCompleted;
        const res = await fetch('/api/tasks/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: taskId, completed: newStatus })
        });
        const data = await res.json();
        if (data.success) {
          allTasksCache = data.tasks || [];
          filterTasks();
        }
      } catch (e) {}
    }

    async function editTaskPrompt(taskId, currentTitle, currentTag) {
      const newTitle = prompt('Edit task name:', currentTitle);
      if (newTitle === null) return;
      const trimmedTitle = newTitle.trim();
      if (!trimmedTitle) {
        alert('Task title cannot be empty.');
        return;
      }
      const newTag = prompt('Edit category/tag (e.g. Work, Study, Personal, Urgent, Coding):', currentTag);
      const trimmedTag = newTag !== null ? newTag.trim() : currentTag;

      try {
        const res = await fetch('/api/tasks/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: taskId, title: trimmedTitle, tag: trimmedTag || 'General' })
        });
        const data = await res.json();
        if (data.success) {
          allTasksCache = data.tasks || [];
          filterTasks();
        }
      } catch (e) {
        alert('Failed to update task.');
      }
    }

    async function deleteTaskAction(taskId) {
      if (!confirm('Are you sure you want to delete this checklist item?')) return;
      try {
        const res = await fetch('/api/tasks/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: taskId })
        });
        const data = await res.json();
        if (data.success) {
          allTasksCache = data.tasks || [];
          filterTasks();
        }
      } catch (e) {
        alert('Failed to delete task.');
      }
    }

    async function clearCompletedTasksAction() {
      if (!confirm('Are you sure you want to remove all completed tasks from your checklist?')) return;
      try {
        const res = await fetch('/api/tasks/clear_completed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
          allTasksCache = data.tasks || [];
          filterTasks();
        }
      } catch (e) {
        alert('Failed to clear completed tasks.');
      }
    }

    // =========================================================
    // SETTINGS MODULE JAVASCRIPT
    // =========================================================
    let currentSettingsData = {
      response_style: 'default',
      web_search: true,
      theme: 'dark',
      font_size: 'normal'
    };

    async function loadSettings() {
      try {
        const res = await fetch('/api/settings');
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) {
          if (data.user) {
            const nameInp = document.getElementById('settings-name-input');
            const emailDisp = document.getElementById('settings-email-display');
            if (nameInp) nameInp.value = data.user.name || '';
            if (emailDisp) emailDisp.innerText = data.user.email || '';
          }
          if (data.settings) {
            currentSettingsData = data.settings;
            const styleSelect = document.getElementById('settings-response-style-select');
            const themeSelect = document.getElementById('settings-theme-select');
            const fontSelect = document.getElementById('settings-font-size-select');
            const searchTrack = document.getElementById('settings-search-track');
            const searchStatus = document.getElementById('settings-search-status');

            if (styleSelect) styleSelect.value = data.settings.response_style || 'default';
            if (themeSelect) themeSelect.value = data.settings.theme || 'dark';
            if (fontSelect) fontSelect.value = data.settings.font_size || 'normal';

            const isSearchOn = data.settings.web_search !== false;
            if (searchTrack) {
              searchTrack.className = 'switch-track ' + (isSearchOn ? 'active' : '');
            }
            if (searchStatus) {
              searchStatus.innerText = isSearchOn ? 'Enabled' : 'Disabled';
            }

            applyAppearance(data.settings.theme, data.settings.font_size);
          }
        }
      } catch (e) {}
    }

    function applyAppearance(theme, fontSize) {
      document.body.classList.remove('theme-midnight', 'theme-oled', 'font-large');
      if (theme === 'midnight') document.body.classList.add('theme-midnight');
      if (theme === 'oled') document.body.classList.add('theme-oled');
      if (fontSize === 'large') document.body.classList.add('font-large');
    }

    async function applyAndSaveAppearance() {
      const themeSelect = document.getElementById('settings-theme-select');
      const fontSelect = document.getElementById('settings-font-size-select');
      const theme = themeSelect ? themeSelect.value : 'dark';
      const fontSize = fontSelect ? fontSelect.value : 'normal';

      applyAppearance(theme, fontSize);

      try {
        await fetch('/api/settings/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ theme: theme, font_size: fontSize })
        });
      } catch (e) {}
    }

    async function toggleWebSearchSetting() {
      const current = currentSettingsData.web_search !== false;
      const next = !current;
      currentSettingsData.web_search = next;

      const searchTrack = document.getElementById('settings-search-track');
      const searchStatus = document.getElementById('settings-search-status');
      if (searchTrack) searchTrack.className = 'switch-track ' + (next ? 'active' : '');
      if (searchStatus) searchStatus.innerText = next ? 'Enabled' : 'Disabled';

      await saveAISettings();
    }

    async function saveAISettings() {
      const styleSelect = document.getElementById('settings-response-style-select');
      const responseStyle = styleSelect ? styleSelect.value : 'default';
      const webSearch = currentSettingsData.web_search !== false;
      const feedback = document.getElementById('ai-settings-feedback');

      try {
        const res = await fetch('/api/settings/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ response_style: responseStyle, web_search: webSearch })
        });
        const data = await res.json();
        if (data.success) {
          currentSettingsData = data.settings;
          if (feedback) {
            feedback.className = 'settings-feedback success';
            feedback.innerText = 'AI preferences saved and active for subsequent responses.';
            setTimeout(() => { feedback.style.display = 'none'; feedback.className = 'settings-feedback'; }, 3000);
          }
        }
      } catch (e) {}
    }

    async function saveProfileSettings() {
      const nameInp = document.getElementById('settings-name-input');
      const pwdInp = document.getElementById('settings-password-input');
      const feedback = document.getElementById('profile-settings-feedback');
      const name = nameInp ? nameInp.value.trim() : '';
      const pwd = pwdInp ? pwdInp.value.trim() : '';

      if (!name) {
        if (feedback) {
          feedback.className = 'settings-feedback error';
          feedback.innerText = 'Display name cannot be empty.';
        }
        return;
      }

      try {
        const payload = { name: name };
        if (pwd) payload.password = pwd;

        const res = await fetch('/api/settings/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          if (currentUser) currentUser.name = name;
          updateUserProfileUI();
          if (pwdInp) pwdInp.value = '';
          if (feedback) {
            feedback.className = 'settings-feedback success';
            feedback.innerText = 'Profile details updated successfully.';
            setTimeout(() => { feedback.style.display = 'none'; feedback.className = 'settings-feedback'; }, 3000);
          }
        } else {
          if (feedback) {
            feedback.className = 'settings-feedback error';
            feedback.innerText = data.error || 'Failed to update profile.';
          }
        }
      } catch (e) {
        if (feedback) {
          feedback.className = 'settings-feedback error';
          feedback.innerText = 'Failed to update profile.';
        }
      }
    }

    async function exportDataAction() {
      try {
        const res = await fetch('/api/settings/export');
        if (!res.ok) return;
        const data = await res.json();
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `novax_workspace_backup_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (e) {
        alert('Failed to export data.');
      }
    }

    async function clearDataAction() {
      if (!confirm('Are you sure you want to permanently clear ALL your workspace data (conversations, memories, projects, tasks)? This action cannot be undone.')) return;
      try {
        const res = await fetch('/api/settings/clear_data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
          alert('Workspace data cleared successfully.');
          loadConversationsList();
          startNewChat();
        }
      } catch (e) {
        alert('Failed to clear workspace data.');
      }
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

    function appendMessageBubble(role, content, msgId, attachedFile) {
      const container = document.getElementById('chat-messages');
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-bubble-wrapper ' + (role === 'user' ? 'user' : 'assistant');
      if (msgId) wrapper.dataset.msgId = msgId;

      const bubble = document.createElement('div');
      bubble.className = 'chat-bubble ' + (role === 'user' ? 'user' : 'assistant');

      if (role === 'user') {
        if (attachedFile) {
          const badge = document.createElement('div');
          badge.className = 'user-attached-badge';
          badge.innerHTML = `
            <span class="user-badge-icon">${attachedFile.badge_type || 'FILE'}</span>
            <span class="user-badge-name">${escapeHtml(attachedFile.filename)}</span>
            <span class="user-badge-size">(${attachedFile.formatted_size})</span>
          `;
          bubble.appendChild(badge);

          const textEl = document.createElement('div');
          textEl.className = 'user-message-text';
          textEl.innerText = content;
          bubble.appendChild(textEl);
        } else {
          bubble.innerText = content;
        }
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

    let currentAttachedFile = null;

    function handleFileSelected(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      processFileUpload(file);
      event.target.value = '';
    }

    async function processFileUpload(file) {
      if (!file) return;

      if (file.size > 25 * 1024 * 1024) {
        alert('File is too large. Please select a file under 25MB.');
        return;
      }

      const preview = document.getElementById('chat-attachment-preview');
      const nameEl = document.getElementById('attachment-name');
      const sizeEl = document.getElementById('attachment-size');
      const iconEl = document.getElementById('attachment-icon');

      // Immediate loading indicator
      if (preview) {
        nameEl.innerText = file.name;
        sizeEl.innerText = '(uploading & parsing...)';
        if (iconEl) iconEl.innerText = '...';
        preview.style.display = 'flex';
      }

      const reader = new FileReader();
      reader.onload = async function(e) {
        const dataUrl = e.target.result;
        try {
          const res = await fetch('/api/files/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              filename: file.name,
              file_data: dataUrl,
              file_size: file.size
            })
          });
          const data = await res.json();
          if (res.ok && data.success) {
            currentAttachedFile = data;
            renderAttachmentPreview();
          } else {
            alert(data.error || 'Failed to parse file.');
            clearAttachedFile();
          }
        } catch (err) {
          // Client-side fallback
          currentAttachedFile = {
            filename: file.name,
            badge_type: 'FILE',
            formatted_size: formatFileSize(file.size),
            text: file.name,
            word_count: 0
          };
          renderAttachmentPreview();
        }
      };
      reader.onerror = function() {
        alert('Failed to read file.');
        clearAttachedFile();
      };
      reader.readAsDataURL(file);
    }

    function setupDragAndDrop() {
      const chatPanel = document.getElementById('chat-panel');
      const dropOverlay = document.getElementById('chat-drop-overlay');
      if (!chatPanel) return;

      let dragCounter = 0;

      chatPanel.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        if (dropOverlay) dropOverlay.classList.add('active');
      }, false);

      chatPanel.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
      }, false);

      chatPanel.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter <= 0) {
          dragCounter = 0;
          if (dropOverlay) dropOverlay.classList.remove('active');
        }
      }, false);

      chatPanel.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter = 0;
        if (dropOverlay) dropOverlay.classList.remove('active');

        const dt = e.dataTransfer;
        const files = dt && dt.files;
        if (files && files.length > 0) {
          processFileUpload(files[0]);
        }
      }, false);
    }

    function formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function renderAttachmentPreview() {
      const preview = document.getElementById('chat-attachment-preview');
      const nameEl = document.getElementById('attachment-name');
      const sizeEl = document.getElementById('attachment-size');
      const iconEl = document.getElementById('attachment-icon');

      if (currentAttachedFile) {
        nameEl.innerText = currentAttachedFile.filename;
        let extra = currentAttachedFile.formatted_size;
        if (currentAttachedFile.page_count) {
          extra += ` • ${currentAttachedFile.page_count} page(s)`;
        } else if (currentAttachedFile.word_count) {
          extra += ` • ${currentAttachedFile.word_count} words`;
        }
        sizeEl.innerText = `(${extra})`;
        if (iconEl) iconEl.innerText = currentAttachedFile.badge_type || 'FILE';
        preview.style.display = 'flex';
      } else {
        preview.style.display = 'none';
      }
    }

    function clearAttachedFile() {
      currentAttachedFile = null;
      const fileInput = document.getElementById('chat-file-input');
      if (fileInput) fileInput.value = '';
      renderAttachmentPreview();
    }


    async function sendMessage() {
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text && !currentAttachedFile) return;

      const fileToSend = currentAttachedFile;
      let userBubbleText = text;
      let promptText = text;

      if (fileToSend) {
        if (!userBubbleText) {
          userBubbleText = "Please analyze this attached document and provide a complete summary and key takeaways.";
          promptText = `[Attached Document: ${fileToSend.filename} (${fileToSend.formatted_size})]\n--- Document Content ---\n${fileToSend.text}\n--- End Document Content ---\n\nPlease analyze this document and provide a complete summary and key takeaways.`;
        } else {
          promptText = `[Attached Document: ${fileToSend.filename} (${fileToSend.formatted_size})]\n--- Document Content ---\n${fileToSend.text}\n--- End Document Content ---\n\nUser Question:\n${text}`;
        }
        clearAttachedFile();
      }

      if (!currentConversationId) {
        currentConversationId = generateConvId();
      }

      const container = document.getElementById('chat-messages');
      appendMessageBubble('user', userBubbleText, null, fileToSend);

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
          body: JSON.stringify({ message: promptText, conversation_id: currentConversationId })
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
          Object.keys(memories[cat]).forEach(k => {
            const v = memories[cat][k];
            const actualVal = (v && typeof v === 'object' && v.value !== undefined) ? v.value : v;
            if (actualVal !== undefined && actualVal !== null && String(actualVal).trim() !== '') {
              totalItems++;
            }
          });
        }
      });
      document.getElementById('total-memory-count').innerText = totalItems;

      const q = filterQuery.toLowerCase().trim();

      categories.forEach(catConfig => {
        const catData = memories[catConfig.id] || memories[catConfig.id.toLowerCase()] || {};
        const itemsCount = Object.keys(catData).filter(k => {
          const v = catData[k];
          const actualVal = (v && typeof v === 'object' && v.value !== undefined) ? v.value : v;
          return actualVal !== undefined && actualVal !== null && String(actualVal).trim() !== '';
        }).length;

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

    function renderEditableField(category, key, label, value, type = 'text', placeholder = 'Not specified') {
      const displayVal = value ? escapeHtml(value) : `<span class="memory-field-empty">${placeholder}</span>`;
      return `
        <div class="memory-field-item editable"
             id="mem-field-${category}-${key}"
             onclick="startInlineEdit('${category}', '${key}', '${label.replace(/'/g, "\\'")}', this, '${type}')"
             title="Click to edit ${label}">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="memory-field-label">${label}</span>
            <span class="mem-edit-hint">✎ Edit</span>
          </div>
          <span class="memory-field-val">${displayVal}</span>
        </div>
      `;
    }

    function startInlineEdit(category, key, label, itemEl, type = 'text') {
      if (itemEl.classList.contains('is-editing')) return;
      itemEl.classList.add('is-editing');

      const catData = currentMemoriesData[category] || {};
      const currentVal = getVal(catData, key, '');
      const isMultiLine = type === 'textarea' || type === 'multiline';

      const inputHtml = isMultiLine
        ? `<textarea class="memory-inline-input" id="inline-input-${category}-${key}" rows="2" placeholder="Enter ${label}...">${escapeHtml(currentVal)}</textarea>`
        : `<input type="text" class="memory-inline-input" id="inline-input-${category}-${key}" value="${escapeHtml(currentVal)}" placeholder="Enter ${label}..." />`;

      itemEl.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span class="memory-field-label">${label}</span>
          <span style="font-size:10px; color:var(--novax-cyan); font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Editing...</span>
        </div>
        <div class="memory-inline-form" onclick="event.stopPropagation();">
          ${inputHtml}
          <div class="memory-inline-actions">
            <button type="button" class="btn-inline-save" onclick="saveInlineEdit('${category}', '${key}', this); event.stopPropagation();">Save</button>
            <button type="button" class="btn-inline-cancel" onclick="cancelInlineEdit('${category}', '${key}', this); event.stopPropagation();">Cancel</button>
          </div>
        </div>
      `;

      const inputEl = document.getElementById(`inline-input-${category}-${key}`);
      if (inputEl) {
        inputEl.focus();
        inputEl.select();

        inputEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !isMultiLine) {
            e.preventDefault();
            e.stopPropagation();
            saveInlineEdit(category, key, inputEl);
          } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && isMultiLine) {
            e.preventDefault();
            e.stopPropagation();
            saveInlineEdit(category, key, inputEl);
          } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            cancelInlineEdit(category, key, inputEl);
          }
        });
      }
    }

    function startCustomInlineEdit(category, key, itemEl) {
      if (itemEl.classList.contains('is-editing')) return;
      itemEl.classList.add('is-editing');

      const catData = currentMemoriesData[category] || {};
      const currentVal = getVal(catData, key, '');
      const safeKeyAttr = key.replace(/[^a-zA-Z0-9_-]/g, '_');

      itemEl.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span class="memory-field-label">${escapeHtml(key)}</span>
          <span style="font-size:10px; color:var(--novax-cyan); font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Editing...</span>
        </div>
        <div class="memory-inline-form" onclick="event.stopPropagation();">
          <textarea class="memory-inline-input" id="inline-input-${category}-${safeKeyAttr}" rows="2" placeholder="Enter value...">${escapeHtml(currentVal)}</textarea>
          <div class="memory-inline-actions">
            <button type="button" class="btn-inline-save" onclick="saveCustomInlineEdit('${category}', '${escapeHtml(key).replace(/'/g, "\\'")}', '${safeKeyAttr}', this); event.stopPropagation();">Save</button>
            <button type="button" class="btn-inline-cancel" onclick="cancelInlineEdit('${category}', '${escapeHtml(key).replace(/'/g, "\\'")}', this); event.stopPropagation();">Cancel</button>
          </div>
        </div>
      `;

      const inputEl = document.getElementById(`inline-input-${category}-${safeKeyAttr}`);
      if (inputEl) {
        inputEl.focus();
        inputEl.select();

        inputEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            e.stopPropagation();
            saveCustomInlineEdit(category, key, safeKeyAttr, inputEl);
          } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            cancelInlineEdit(category, key, inputEl);
          }
        });
      }
    }

    async function saveInlineEdit(category, key, elementInsideItem) {
      const inputEl = document.getElementById(`inline-input-${category}-${key}`);
      if (!inputEl) return;
      const newVal = inputEl.value.trim();

      await saveMemoryItem(category, key, newVal);

      if (category === 'profile' && key === 'name') {
        if (typeof currentUser !== 'undefined' && currentUser) {
          currentUser.name = newVal || 'User';
        }
        const displayNameEl = document.getElementById('user-display-name');
        if (displayNameEl) displayNameEl.innerText = newVal || 'User';
        const avatarEl = document.getElementById('user-avatar');
        if (avatarEl) avatarEl.innerText = (newVal || 'U').charAt(0).toUpperCase();
      }

      await loadMemories();
    }

    async function saveCustomInlineEdit(category, key, safeKeyAttr, elementInsideItem) {
      const inputEl = document.getElementById(`inline-input-${category}-${safeKeyAttr}`);
      if (!inputEl) return;
      const newVal = inputEl.value.trim();

      await saveMemoryItem(category, key, newVal);
      await loadMemories();
    }

    function cancelInlineEdit(category, key, elementInsideItem) {
      renderMemoryCenter(currentMemoriesData);
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

      return `
        <div class="memory-field-grid">
          ${renderEditableField('profile', 'name', 'Full Name', name)}
          ${renderEditableField('profile', 'preferred_name', 'Preferred Name', prefName)}
          ${renderEditableField('profile', 'pronouns', 'Pronouns', pronouns)}
          ${renderEditableField('profile', 'age_range', 'Age Range', ageRange)}
          ${renderEditableField('profile', 'country', 'Country', country)}
          ${renderEditableField('profile', 'city', 'City', city)}
          ${renderEditableField('profile', 'timezone', 'Timezone', timezone)}
          ${renderEditableField('profile', 'language', 'Preferred Language', language)}
        </div>
      `;
    }

    function renderEducationCategoryHtml(data) {
      const status = getVal(data, 'status');
      const institution = getVal(data, 'institution');
      const course = getVal(data, 'course');
      const field = getVal(data, 'field');
      const year = getVal(data, 'year');
      const subjectsStr = getVal(data, 'subjects');

      const subjects = subjectsStr ? subjectsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

      let chipHtml = subjects.map(s => `
        <span class="mem-chip">
          ${escapeHtml(s)}
          <button class="mem-chip-del" onclick="removeSubjectChip('${escapeHtml(s).replace(/'/g, "\\'")}')" title="Remove subject">✕</button>
        </span>
      `).join('');

      return `
        <div class="memory-field-grid" style="margin-bottom:14px;">
          ${renderEditableField('education', 'status', 'Status', status)}
          ${renderEditableField('education', 'institution', 'Institution', institution)}
          ${renderEditableField('education', 'course', 'Degree / Course', course)}
          ${renderEditableField('education', 'field', 'Field of Study', field)}
          ${renderEditableField('education', 'year', 'Current Year', year)}
        </div>
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span class="memory-field-label">Subjects</span>
            <button class="btn-logout" style="color:var(--novax-primary); padding:4px 12px; font-size:12px;" onclick="addSubjectPrompt()">+ Add Subject</button>
          </div>
          <div class="chip-container">${chipHtml || '<span style="font-size:13px; color:var(--novax-muted);">No subjects added yet.</span>'}</div>
        </div>
      `;
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
          <button class="mem-chip-del" onclick="removeTechSkillChip('${escapeHtml(s).replace(/'/g, "\\'")}')" title="Remove skill">✕</button>
        </span>
      `).join('');

      return `
        <div class="memory-field-grid" style="margin-bottom:14px;">
          ${renderEditableField('career', 'occupation', 'Occupation', occupation)}
          ${renderEditableField('career', 'experience', 'Experience Level', experience)}
          ${renderEditableField('career', 'target_role', 'Target Role', targetRole)}
          ${renderEditableField('career', 'career_goal', 'Career Goal', careerGoal, 'textarea')}
        </div>
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span class="memory-field-label">Technical & Soft Skills</span>
            <button class="btn-logout" style="color:var(--novax-primary); padding:4px 12px; font-size:12px;" onclick="addSkillPrompt()">+ Add Skill</button>
          </div>
          <div class="chip-container">${chipsHtml || '<span style="font-size:13px; color:var(--novax-muted);">No skills added yet.</span>'}</div>
        </div>
      `;
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
          <button class="mem-chip-del" onclick="removeInterestChip('${escapeHtml(s).replace(/'/g, "\\'")}')" title="Remove interest">✕</button>
        </span>
      `).join('');

      return `
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span class="memory-field-label">Hobbies, Topics & Technologies</span>
            <button class="btn-logout" style="color:var(--novax-cyan); padding:4px 12px; font-size:12px;" onclick="addInterestPrompt()">+ Add Interest</button>
          </div>
          <div class="chip-container">${chipsHtml || '<span style="font-size:13px; color:var(--novax-muted);">No interests added yet.</span>'}</div>
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
        <div class="memory-field-grid">
          ${renderEditableField('goals', 'short_term', 'Short-Term Goals', shortTerm, 'textarea')}
          ${renderEditableField('goals', 'long_term', 'Long-Term Goals', longTerm, 'textarea')}
        </div>
      `;
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
                <div class="pref-radio-label ${length === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'length', '${opt}'); loadMemories();">
                  ${length === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div>
            <span class="memory-field-label">Explanation Style</span>
            <div class="pref-option-group">
              ${['Simple', 'Step-by-step', 'Technical'].map(opt => `
                <div class="pref-radio-label ${style === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'style', '${opt}'); loadMemories();">
                  ${style === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div>
            <span class="memory-field-label">Tone</span>
            <div class="pref-option-group">
              ${['Professional', 'Friendly', 'Casual'].map(opt => `
                <div class="pref-radio-label ${tone === opt ? 'selected' : ''}" onclick="saveMemoryItem('preferences', 'tone', '${opt}'); loadMemories();">
                  ${tone === opt ? '●' : '○'} ${opt}
                </div>
              `).join('')}
            </div>
          </div>
          <div class="memory-field-grid">
            ${renderEditableField('preferences', 'programming_language', 'Preferred Programming Language', lang)}
            ${renderEditableField('preferences', 'additional_notes', 'Additional Instructions', notes, 'textarea')}
          </div>
        </div>
      `;
    }

    function renderProjectsCategoryHtml(data) {
      let items = Object.keys(data);
      if (items.length === 0) {
        return `
          <p style="color:var(--novax-muted); font-size:14px; margin-bottom:14px;">No project context stored yet.</p>
          <button class="btn-primary" style="padding:6px 14px; font-size:13px; width:auto;" onclick="addCustomMemoryCategoryPrompt('projects')">+ Add Project Context</button>
        `;
      }
      let html = '<div class="memory-field-grid">';
      items.forEach(k => {
        const itemObj = data[k];
        const val = itemObj.value || itemObj;
        const src = itemObj.source || 'USER';
        const safeKey = escapeHtml(k).replace(/'/g, "\\'");
        html += `
          <div class="memory-field-item editable" id="mem-field-projects-${escapeHtml(k)}" onclick="startCustomInlineEdit('projects', '${safeKey}', this)" title="Click to edit ${escapeHtml(k)}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="memory-field-label">${escapeHtml(k)}</span>
                <span class="source-badge ${src}">${src}</span>
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="mem-edit-hint">✎ Edit</span>
                <button class="btn-mem-del" onclick="event.stopPropagation(); deleteMemoryConfirm('projects', '${safeKey}')" title="Delete memory">✕</button>
              </div>
            </div>
            <span class="memory-field-val">${escapeHtml(val)}</span>
          </div>
        `;
      });
      html += '</div>';
      html += `<div style="margin-top:14px;"><button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="addCustomMemoryCategoryPrompt('projects')">+ Add Project Context</button></div>`;
      return html;
    }

    function renderRoutinesCategoryHtml(data) {
      const wakeup = getVal(data, 'wake_up');
      const study = getVal(data, 'study');
      const sleep = getVal(data, 'sleep');
      const workHours = getVal(data, 'working_hours');

      return `
        <div class="memory-field-grid">
          ${renderEditableField('routines', 'wake_up', 'Wake-Up Time', wakeup, 'text', 'Not set')}
          ${renderEditableField('routines', 'study', 'Study Time', study, 'text', 'Not set')}
          ${renderEditableField('routines', 'sleep', 'Sleep Time', sleep, 'text', 'Not set')}
          ${renderEditableField('routines', 'working_hours', 'Preferred Working Hours', workHours, 'text', 'Not set')}
        </div>
      `;
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
        const safeKey = escapeHtml(k).replace(/'/g, "\\'");
        html += `
          <div class="memory-field-item editable" id="mem-field-custom-${escapeHtml(k)}" onclick="startCustomInlineEdit('custom', '${safeKey}', this)" title="Click to edit ${escapeHtml(k)}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="memory-field-label">${escapeHtml(k)}</span>
                <span class="source-badge ${src}">${src}</span>
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="mem-edit-hint">✎ Edit</span>
                <button class="btn-mem-del" onclick="event.stopPropagation(); deleteMemoryConfirm('custom', '${safeKey}')" title="Delete memory">✕</button>
              </div>
            </div>
            <span class="memory-field-val">${escapeHtml(val)}</span>
          </div>
        `;
      });
      html += '</div>';
      html += `<div style="margin-top:14px;"><button class="btn-logout" style="color:var(--novax-cyan); padding:6px 14px; font-size:13px;" onclick="addCustomMemoryCategoryPrompt('custom')">+ Add Memory</button></div>`;
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

    // Initialize Auth state & Drag and Drop on page load
    window.addEventListener('DOMContentLoaded', () => {
      checkAuth();
      setupDragAndDrop();
    });
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

        if session_id:
            session = auth.validate_session(session_id)
            if session:
                return {
                    "id": session["user_id"],
                    "email": session["email"],
                    "name": session["name"],
                    "session_id": session_id
                }

        # Resilient fallback to primary user if available
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, name FROM users ORDER BY created_at ASC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "email": row["email"],
                        "name": row["name"],
                        "session_id": "fallback_session"
                    }
        except Exception:
            pass

        return None

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

        elif parsed.path == "/api/settings":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            settings = db.get_user_settings(user["id"])
            self._send_json({
                "success": True,
                "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
                "settings": settings
            })
            return

        elif parsed.path == "/api/settings/export":
            user = self._get_authenticated_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return
            data = db.export_user_data(user["id"])
            self._send_json(data)
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

        elif parsed.path == "/api/files/upload":
            filename = data.get("filename") or "document.txt"
            base64_data = data.get("file_data")
            raw_text = data.get("raw_text")

            if not base64_data and raw_text is None:
                self._send_json({"error": "No file content provided"}, status=400)
                return

            result = parse_uploaded_file(filename, base64_data=base64_data, raw_text=raw_text)
            self._send_json(result)
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
                if category == "profile" and key == "name" and value:
                    try:
                        db.update_user(user["id"], name=value)
                    except Exception:
                        pass

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

        elif parsed.path == "/api/projects/create":
            name = data.get("name")
            if not name:
                self._send_json({"error": "name is required"}, status=400)
                return
            project_id = "proj_" + str(int(time.time())) + "_" + os.urandom(4).hex()
            description = data.get("description", "")
            db.create_project(project_id, user["id"], name, description)
            projects = db.get_user_projects(user["id"])
            self._send_json({"success": True, "projects": projects})
            return

        elif parsed.path == "/api/projects/update":
            project_id = data.get("id")
            name = data.get("name")
            if not project_id or not name:
                self._send_json({"error": "id and name are required"}, status=400)
                return
            description = data.get("description", "")
            db.update_project(project_id, user["id"], name, description)
            projects = db.get_user_projects(user["id"])
            self._send_json({"success": True, "projects": projects})
            return

        elif parsed.path == "/api/projects/delete":
            project_id = data.get("id")
            if not project_id:
                self._send_json({"error": "id is required"}, status=400)
                return
            db.delete_project(project_id, user["id"])
            projects = db.get_user_projects(user["id"])
            self._send_json({"success": True, "projects": projects})
            return

        elif parsed.path == "/api/tasks/create":
            title = (data.get("title") or "").strip()
            if not title:
                self._send_json({"error": "title is required"}, status=400)
                return
            task_id = "task_" + str(int(time.time())) + "_" + os.urandom(4).hex()
            tag = (data.get("tag") or "General").strip()
            db.create_task(task_id, user["id"], title, tag)
            tasks = db.get_user_tasks(user["id"])
            self._send_json({"success": True, "tasks": tasks})
            return

        elif parsed.path == "/api/tasks/toggle":
            task_id = data.get("id")
            completed = data.get("completed", False)
            if not task_id:
                self._send_json({"error": "id is required"}, status=400)
                return
            db.toggle_task(task_id, user["id"], completed)
            tasks = db.get_user_tasks(user["id"])
            self._send_json({"success": True, "tasks": tasks})
            return

        elif parsed.path == "/api/tasks/update":
            task_id = data.get("id")
            title = (data.get("title") or "").strip()
            tag = data.get("tag")
            if not task_id or not title:
                self._send_json({"error": "id and title are required"}, status=400)
                return
            db.update_task(task_id, user["id"], title, tag)
            tasks = db.get_user_tasks(user["id"])
            self._send_json({"success": True, "tasks": tasks})
            return

        elif parsed.path == "/api/tasks/delete":
            task_id = data.get("id")
            if not task_id:
                self._send_json({"error": "id is required"}, status=400)
                return
            db.delete_task(task_id, user["id"])
            tasks = db.get_user_tasks(user["id"])
            self._send_json({"success": True, "tasks": tasks})
            return

        elif parsed.path == "/api/tasks/clear_completed":
            db.clear_completed_tasks(user["id"])
            tasks = db.get_user_tasks(user["id"])
            self._send_json({"success": True, "tasks": tasks})
            return

        elif parsed.path == "/api/settings/update":
            response_style = data.get("response_style")
            web_search = data.get("web_search")
            theme = data.get("theme")
            font_size = data.get("font_size")
            updated = db.update_user_settings(user["id"], response_style=response_style, web_search=web_search, theme=theme, font_size=font_size)
            self._send_json({"success": True, "settings": updated})
            return

        elif parsed.path == "/api/settings/profile":
            name = (data.get("name") or "").strip()
            password = data.get("password")
            if not name and not password:
                self._send_json({"error": "No updates provided"}, status=400)
                return
            pwd_hash, salt = auth.hash_password(password) if password else (None, None)
            db.update_user_profile(user["id"], name=name or None, password_hash=pwd_hash, salt=salt)
            self._send_json({"success": True, "name": name or user["name"]})
            return

        elif parsed.path == "/api/settings/clear_data":
            db.clear_user_workspace(user["id"])
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
