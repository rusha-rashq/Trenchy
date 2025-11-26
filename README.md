# Trenchy
A metadata-driven, Rasa-powered conversational assistant that understands Hinglish and provides intelligent, product-aware customer support for e-commerce platforms.

Trenchy is an end-to-end e-commerce support chatbot designed for the Indian market, where customers frequently communicate in code-mixed Hinglish (Hindi + English).
Instead of responding generically, Trenchy uses context-awareness, product metadata, and custom Rasa actions to deliver precise, human-like support.

The system integrates:

A multi-page web frontend (Men, Women, Kids, Misc, Product Pages)

Socket.IO metadata injection (product_id + page_url)

A FastAPI backend serving product + order data

A Rasa NLU + Core model for reasoning, entity extraction, and intent detection

Custom actions for stock lookup, recommendations, order status, cancellation, etc.

Trenchy brings real-time, product-aware reasoning to online shopping.

🚀 Key Features

🧠 1. Hinglish NLU

Understands mixed-language queries such as:

“ye washable hai?”

“isko M size milega?”

“is shirt ka material kya hai?”

📦 2. Product-Aware Reasoning (Context Injection)

When a user views a product page:
➡️ the browser automatically injects the product ID + URL into each chatbot message
➡️ the bot knows exactly which product the user is asking about

🛒 3. Order & Refund Management

Supports:

Tracking orders

Canceling orders

Reinstating orders

Checking refund status

Changing delivery address

❤️ 4. Sentiment Detection + Human Handoff

Negative sentiment triggers escalation

Positive sentiment triggers upsell flow

Handles frustration gracefully

🏷️ 5. Recommendations Engine

Shows related products based on category.

📦 6. Backend API (FastAPI)

Serves:

/products

/products/{id}

/orders/{order_id}
…all used by the chatbot and frontend.

🧱 System Architecture
 User (Browser)
       │
       │ 1. Message + product_id metadata
       ▼
🗨️ Rasa Webchat Widget (Socket.IO)
       │
       ▼
🤖 Rasa NLU  → Intent recognition + Hinglish entity extraction
       │
       ▼
🧠 Rasa Core (Rules + Policies)
       │
       ▼
⚙️ Custom Actions (Python)
       │
       ▼
🗄️ FastAPI Backend → SQLite DB (products, orders)
       │
       ▼
📦 Product / Order Results → Back to Rasa → Back to User

🛠️ Tech Stack

Rasa 3.x (NLU + Core + RulePolicy + TEDPolicy)

Python 3.9.6

FastAPI + Uvicorn

SQLite

JavaScript, HTML, CSS

Socket.IO

rasa-webchat widget

VADER sentiment analysis

📥 Installation & Setup
1️⃣ Clone the Project
git clone https://github.com/yourusername/trenchy.git
cd trenchy

2️⃣ Create & Activate Virtual Environment (Python 3.9.6)
python3.9 -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows

3️⃣ Install Rasa Project Dependencies
pip install -r requirements.txt

4️⃣ Train the Rasa Model
rasa train

🏃‍♂️ Running the Project

Trenchy uses three terminals (plus backend).

🟦 Terminal 1 — Rasa Action Server
source venv/bin/activate
rasa run actions

🟩 Terminal 2 — Rasa Shell (for testing)
source venv/bin/activate
rasa shell

🟧 Terminal 3 — Rasa Server (Frontend Uses This)
source venv/bin/activate
rasa run --enable-api --cors "*"

🟪 Backend API (FastAPI)

The backend folder is trenchy-backend.

Install backend dependencies:
cd trenchy-backend
pip install -r requirements.txt

Run backend:
uvicorn main:app --reload --port 8000


Backend endpoints:

GET /products
GET /products/{id}
GET /orders/{order_id}

🌐 Frontend

Open:

index.html


or serve it:

cd frontend
python3 -m http.server 8080


Product pages automatically send metadata to Rasa using:

event.metadata = {
   product_id,
   page_url,
};

📂 Project Structure
trenchy/
│
├── actions.py
├── sentiment_analyzer.py
├── domain.yml
├── nlu.yml
├── rules.yml
├── stories.yml
├── requirements.txt
│
├── trenchy-backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── products.db
│
├── frontend/
│   ├── index.html
│   ├── product.html
│   ├── products/
│   │   ├── men.html
│   │   ├── women.html
│   │   ├── kids.html
│   │   └── misc.html
│   └── images/
│
└── README.md

🔮 Future Work

Integrate LLM-based RAG for more natural conversational responses

Add WhatsApp/Instagram messaging support

Build a shopping cart flow inside the chatbot

Improve recommendation engine using collaborative filtering

Deploy on cloud (Render / HuggingFace Spaces / Railway)

📝 License

MIT License

📚 Citation

If you use this project in research, please cite:

@project{trenchy,
  title={Trenchy: A Context-Aware, Code-Mixed Conversational Agent for E-Commerce},
  year={2025},
  author={Dhar, Rushali}
}


If you'd like, I can also generate:
