<<<<<<< HEAD
## **Trenchy: A Context-Aware Code-Mixed E-Commerce Chatbot**

Trenchy is a Hinglish-aware, product-contextual customer-support chatbot built with  Rasa 3.x , a  custom FastAPI backend , and a frontend website integrated via rasa-webchat.

It supports:

* Code-mixed Hinglish understanding
* Product-aware reasoning (auto-context from product pages)
* Order + refund workflow support
* Sentiment handling + human handoff
* SQLite product/order DB
* Full e-commerce QA flow

This README explains exactly how to install, run, and test the entire system.

# **1. Installation & Virtual Environment Setup**

**Python version required: `3.9.6`**

Rasa does **NOT** work with Python 3.10 or above.

### **Create virtual environment**

```bash
python3.9 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### **Install project dependencies**

Your project contains:

* `requirements.txt` → **main Rasa project**
* `backend/requirements.txt` → **backend API**

Install main dependencies:

```bash
pip install -r requirements.txt
```

# **2. Training the Rasa Model**

Before running anything:

```bash
rasa train
```

This creates the latest conversational model under `/models`.

# **3. Running the Project (3-terminal setup)**

Trenchy uses  **three terminals** :

## **Terminal 1 — Run the Rasa Action Server**

Run from the  *project root* , where `actions.py` is located:

```bash
source venv/bin/activate
rasa run actions
```

You should see:

```
Action server is up and running.
```

## **Terminal 2 — Run the Rasa Assistant (interactive shell)**

If you want to test the bot  *inside the terminal* :

```bash
source venv/bin/activate
rasa shell
```

You can use this for debugging, intent tests, policy tests, etc.

## **Terminal 3 — Run Rasa for Web Integration**

This is required for the  **frontend HTML pages** :

```bash
source venv/bin/activate
rasa run --enable-api --cors "*"
```

This opens:

```
http://localhost:5005
```

and allows:

* rasa-webchat widget
* metadata sending
* socket.io communication
* frontend product context injection

# **4. Running the Backend API (Product + Order Database)**

Your backend lives in:

```
trenchy-backend/
```

### **Install backend dependencies**

```bash
cd trenchy-backend
pip install -r requirements.txt
```

### **Run the backend API**

```bash
uvicorn main:app --reload --port 8000
```

This serves endpoints like:

```
GET http://localhost:8000/products
GET http://localhost:8000/product?id=TS017
GET http://localhost:8000/orders/OD12345
```

These endpoints are used by:

* **Frontend product pages**
* **Custom Rasa actions** for stock & order queries
* **Context-aware reasoning logic**

# 5. Running the Frontend (Website)

Open:

```
index.html
```

Then right-click to open with Live Server on VS Code.

### Product pages automatically pass metadata:

* `product_id`
* `page_url`

to Rasa through:

```js
event.metadata = {
   product_id: pid,
   page_url: url
};
```

# **6. Testing the System**

Try queries like:

### **Product reasoning**

* “Tell me about this product”
* “Give me details about this”
* “Can you describe this item?”

### **Order tracking**

* “Track order OD90001”
* “Cancel my order”
* “Refund status kya hai?”

### **Hinglish queries**

* “refund policy kya hai”
* “shipping options kya hai”

### **Sentiment**

* “Awesome”
* “Perfect, thank you!”

### **Out of scope**

* “What’s the weather?”

Everything should respond correctly if metadata + backend + Rasa are running.

# **7. Troubleshooting**

### **Metadata is missing**

Check the frontend's:

```js
onSocketEvent.user_uttered
```

### **Backend not responding**

Ensure:

```bash
uvicorn main:app --reload --port 8000
```

is running.

### **Model isn’t updating**

Retrain:

```bash
rasa train
```

### **Rasa won’t start**

Ensure Python is  **3.9.6** .

# **8. Summary of Commands**

### Train model

```bash
rasa train
```

### Terminal 1

```bash
rasa run actions
```

### Terminal 2 (Optional)

```bash
rasa shell
```

### Terminal 3

```bash
rasa run --enable-api --cors "*"
```

### Backend API

```bash
cd trenchy-backend
uvicorn main:app --reload --port 8000
```

**Then start index.html using Live Server.**
--
---
 b677ecd998a71bbbb01b67c876f88c39251f2eb2
