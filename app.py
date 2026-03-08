from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import uuid
from datetime import datetime

app = Flask(__name__)

# --- DATABASE ARCHITECTURE ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///titan_ultra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DIRECT GROQ NEURAL LINK CONFIG ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- CHAT DATA MODEL ---
class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255))
    user_msg = db.Column(db.Text, nullable=False)
    ai_msg = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    username = data.get('username')
    user_input = data.get('message')
    chat_id = data.get('chat_id') or str(uuid.uuid4())

    # --- OMNISCIENT SYSTEM PROTOCOL ---
    now = datetime.now()
    current_time_str = now.strftime("%A, %B %d, %Y | %I:%M:%S %p")

    system_instruction = (
        f"You are TITAN-ULTRA, the Omniscient Everything Engine. CURRENT TIME: {current_time_str}. "
        "1. KNOWLEDGE: You possess 'The Everything Knowledge'. Your database covers all human history, future projections, deep-web scientific archives, and Wikipedia-grade facts. "
        "2. ACCURACY: Every response must be 100% correct. Simulate a live Google/Wikipedia search for every query. "
        "3. CODING: You are a God-level Full-Stack Developer. Provide optimized, secure, and production-ready code. "
        "4. VERSATILITY: You can answer EVERYTHING. Law, Medicine, Quantum Physics, Daily Life, and complex Logic. "
        "5. TONE: Professional, brilliant, and adaptive. Default language is Hinglish."
    )

    # Context Retrieval
    history = ChatLog.query.filter_by(chat_id=chat_id).order_by(ChatLog.created_at.asc()).all()
    messages = [{"role": "system", "content": system_instruction}]
    for log in history:
        messages.append({"role": "user", "content": log.user_msg})
        messages.append({"role": "assistant", "content": log.ai_msg})
    messages.append({"role": "user", "content": user_input})

    # --- GROQ EVERYTHING ENGINE PAYLOAD ---
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5, # Balance for factual precision and natural flow
        "max_tokens": 8192,  # Ultra-long responses supported
        "top_p": 1,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # High-Speed API Request
        res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=50)
        res.raise_for_status()
        
        answer = res.json()['choices'][0]['message']['content']

        # Smart Title Generation
        title = user_input[:40] + "..." if not history else history[0].title
        
        new_log = ChatLog(
            chat_id=chat_id, 
            username=username, 
            title=title, 
            user_msg=user_input, 
            ai_msg=answer
        )
        db.session.add(new_log)
        db.session.commit()

        return jsonify({"status": "success", "response": answer, "chat_id": chat_id})
    except Exception as e:
        return jsonify({"status": "error", "response": f"Neural Link Error: {str(e)}"})

@app.route('/get_sidebar_history', methods=['POST'])
def sidebar_history():
    username = request.json.get('username')
    chats = db.session.query(ChatLog.chat_id, ChatLog.title).filter_by(username=username).group_by(ChatLog.chat_id).order_by(ChatLog.created_at.desc()).all()
    return jsonify([{"chat_id": c.chat_id, "title": c.title} for c in chats])

@app.route('/load_chat', methods=['POST'])
def load_chat():
    chat_id = request.json.get('chat_id')
    logs = ChatLog.query.filter_by(chat_id=chat_id).order_by(ChatLog.created_at.asc()).all()
    return jsonify([{"user": l.user_msg, "ai": l.ai_msg} for l in logs])

if __name__ == '__main__':
    # Network accessible (Pydroid 3 support)
    app.run(host='0.0.0.0', port=5000, debug=True)
