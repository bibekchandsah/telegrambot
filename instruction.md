Build a fully functional **Telegram Random Chat Bot** that anonymously connects two random users for 1-to-1 chatting. Users should be able to enter a queue, get paired with another stranger, chat anonymously, skip/end chat, and rejoin the queue.

The bot must handle:

* Queue system
* Pairing system
* Message routing
* Chat termination
* Optional user filters

This bot must work **exactly like RandomMeetBot** (Telegram) but with cleaner code and scalable architecture.

---

## 🎯 **Core Requirements**

1. Create a Telegram bot using BotFather and use the Bot API token.
2. Users should be able to start with `/start`.
3. Users can join the waiting queue using `/chat`.
4. When two users are available, match them and start a private anonymous chat.
5. Bot must relay text, images, stickers, videos, voice notes — any message — between paired users.
6. Provide `/stop` to end the current chat.
7. Provide `/next` to skip current partner and find a new one.
8. If a partner leaves, notify the other user.
9. Use a **fast queue + pairing system** (Redis recommended).
10. No user identity or profile should be revealed at any point.

---

## 📂 **Features to Implement**

### ✔ **1. Commands**

* `/start` — show welcome message and bot info
* `/chat` — join queue
* `/stop` — end chat
* `/next` — end chat and auto-search new partner
* `/help` — show usage instructions
* `/report` — optional for reporting abuse

---

### ✔ **2. Matching Engine**

* When a user enters the queue, check if someone else is waiting.
* If yes → pair both and notify them.
* If no → put the user into waiting queue.
* Store pairs in Redis or database like:

  * `active_pairs[user_id] = partner_id`

---

### ✔ **3. Message Routing Engine**

Any message (text/media/sticker/emoji) sent by one user should be forwarded to the paired user using:

```
partner_id = active_pairs[sender_id]
```

If the message cannot be routed (no partner), show a "You are not in a chat" message.

---

### ✔ **4. Chat Termination**

* On `/stop`, delete the pair from storage.
* Notify the other partner that the chat has ended.
* If user uses `/next`, end current chat and immediately search for a new one.

---

## 🛠 **Technical Requirements**

### **Backend Language**

Choose **Python (recommended)** or Node.js.

### **Python Libraries:**

* `python-telegram-bot`
* `redis` (for queue)
* `asyncio`

### **Node.js Libraries (optional choice):**

* `node-telegram-bot-api`
* `ioredis`

### **Database / Queue**

* **Redis** for:

  * waiting queue
  * active pairs
  * reports
  * chat state

### **Optional Storage:**

* PostgreSQL or MongoDB for advanced features.

---

## 💡 **Advanced / Optional Features**

The AI agent must allow implementing these later:

* Gender filter system (male/female/any)
* Age filter
* Country filter
* Spam detection & rate limiting
* Inactivity timeout auto-disconnect
* AI message moderation (OpenAI/DeepSeek)

---

## 🌐 **Deployment Requirements**

Provide deployment instructions for:

* Railway.app / Render.com / Heroku
* Docker setup
* PM2 or systemd on Linux VPS

Include `.env` file support for:

```
BOT_TOKEN=
REDIS_URL=
```

---

## 📦 **Output Expected from AI Agent**

The AI must generate:

### ✔ **1. Complete Folder Structure**

```
/project
   /src
      bot.py
      handlers.py
      queue.py
      router.py
      database.py
   Dockerfile
   requirements.txt
   README.md
```

### ✔ **2. Fully Working Production-Ready Code**

### ✔ **3. Instructions for Running Locally**

```
pip install -r requirements.txt
python bot.py
```

### ✔ **4. Deployment instructions**

### ✔ **5. Troubleshooting + logs**

---

## 📑 **Bot Flow Example**

**User 1** → `/chat` → goes to queue
**User 2** → `/chat` → matched
Bot → “Partner found! Say hi 👋”

Messages exchange via bot.

**User 1** → `/next`
Chat ends → User 1 auto-searches again
Bot → “Looking for new partner…”

---

## 🧭 **Goal**

Create a **clean, scalable, stable** Telegram bot system that:

* can handle **1,000+ active users**
* avoids crashes
* prevents duplicate pairing
* ensures messages are reliably forwarded
* supports future feature expansion

