# NOVAX-AI

**NOVAX-AI** is a privacy-first personal AI assistant featuring multi-user authentication, strict user data isolation, local AI execution (via Ollama), memory, and deep space web UI.

---

## Features

- **Multi-User Authentication**: Complete Sign In, Sign Up, Google OAuth 2.0, session management, and logout flows.
- **User Data Isolation**: Every user gets their own private workspace. Memories, conversations, projects, and tasks are strictly isolated per user ID.
- **Deep Space Visual Interface**: Dark-mode web UI matching NOVAX design language with dark space background, radial indigo glow, subtle cyan accents, and active user profile.
- **Local Execution**: Uses local LLMs (`gemma3` via Ollama) with smart offline fallback notifications.
- **NOVAX Personal Memory Center**: User-controlled personal memory management. Organize memories across 9 structured categories with source tracking (`USER`, `CONVERSATION`, `SYSTEM`), response preferences customization, real-time memory search, explicit natural language commands, and clear-all safety controls.

---

## Personal Memory Center

The **NOVAX Personal Memory Center** transforms raw context storage into a transparent, user-controlled personalization system:

### Memory Categories
1. **Profile**: Full name, Preferred name, Pronouns, Age range, Country, City, Timezone, Preferred language.
2. **Education**: Status, Institution, Course/Degree, Field of study, Current year, Subject chips, Graduation year, Learning goals.
3. **Career & Skills**: Occupation, Experience level, Company/organization, Technical & Soft skill chips, Career goal, Target role.
4. **Interests**: Hobbies, Topics, Technologies, Favorite activities as interactive chips.
5. **Goals**: Short-term, Long-term, Learning, Career, Personal, and Project goals.
6. **Response Preferences**: Response length (Concise/Balanced/Detailed), Explanation style (Simple/Step-by-step/Technical), Tone (Professional/Friendly/Casual), Preferred programming language, and additional instructions.
7. **Projects**: Personal project context connected to NOVAX workspace projects.
8. **Routines**: Daily wake-up time, study time, sleep schedule, and preferred working hours.
9. **Custom Memories**: Freeform facts and notes learned with source tracking (`USER`, `CONVERSATION`, `SYSTEM`).

### Explicit Memory Commands
- `"Remember my name is <name>"`
- `"Remember that <key> is <value>"`
- `"Show me what you remember"`
- `"Forget my name"` / `"Forget that <item>"`
- `"Delete all my memories"` / `"Clear all my memories"`

---

## Authentication & User Isolation

NOVAX-AI enforces strict user boundary separation (**ONE USER = ONE PRIVATE WORKSPACE**):
- **User Identity**: Tracks the authenticated user's name, email, memories, and chat history.
- **Product Identity**: Remembers that NOVAX-AI was created by Sriram Prasath.

### Database Schema (`data/novax.db`)
- `users`: User profiles, hashed passwords with unique salts (PBKDF2), and Google OAuth IDs.
- `sessions`: Secure session tokens and expiration timestamps.
- `memories`: Per-user category/key/value memory store with `source`, `created_at`, and `updated_at` metadata.
- `conversations` & `messages`: Per-user chat history and message logs.
- `projects` & `tasks`: Per-user project management and task items.

---

## Environment Variables

Create a `.env` file or export the following environment variables:

```env
PORT=8000
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## How to Run Locally

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) with `gemma3`:
  ```bash
  ollama pull gemma3
  ```

### 2. Setup
```bash
cd NOVAX-AI
source .venv/bin/activate
```

### 3. Launch Application
* **Web UI Mode** (Recommended):
  ```bash
  python3 main.py web
  ```
  Navigate to **`http://localhost:8000`** in your browser.

* **CLI Mode**:
  ```bash
  python3 main.py
  ```

---

## Running Tests

Run the full test suite (including user isolation, memory center, and fallback tests):
```bash
python3 -m unittest discover -s tests
```

---

## License
Open source and built for personal AI assistance.
