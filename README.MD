# NOVAX-AI 🚀

**NOVAX-AI** is a privacy-first, local personal AI assistant designed to run locally on your own machine.

> ⚠️ **Note on Scope**: This project is built specifically as a **Local Personal AI Assistant** powered by local models (via Ollama). Unlike cloud-hosted services like ChatGPT, NOVAX-AI runs locally on your device to keep your data private and accessible offline.

---

## ✨ Features

- 🏠 **Local Execution**: Uses local LLMs (such as `gemma3` via Ollama) without requiring external paid API subscriptions.
- 🎨 **ChatGPT-style Web Interface**: Clean, dark-mode web UI with smooth auto-scrolling, pinned input tab, and interactive web links.
- 💻 **CLI & Web Modes**: Run in your terminal or in your web browser (`http://localhost:8000`).
- 🧠 **Local Memory**: Remembers user details and conversations locally.
- ⚡ **Offline Fallback**: Remains responsive with smart fallback assistance even when offline or when model services are paused.

---

## 🛠️ How to Run Locally

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed on your computer with `gemma3` model pulled:
  ```bash
  ollama pull gemma3
  ```

### 2. Setup & Installation
Clone the repository and activate your virtual environment:
```bash
cd NOVAX-AI
source .venv/bin/activate
```

### 3. Launching the App

* **Web UI Mode** (Recommended):
  ```bash
  python3 main.py web
  ```
  Open **`http://localhost:8000`** in your browser.

* **Terminal CLI Mode**:
  ```bash
  python3 main.py
  ```

---

## 📄 License
Open source and built for personal AI assistance.
