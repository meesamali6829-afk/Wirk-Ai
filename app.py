from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import uuid
from datetime import datetime
import urllib.parse

app = Flask(__name__)

# --- DATABASE CONFIG ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///titan_ultra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- API CONFIG ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- DATABASE MODEL ---
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
    user_input = data.get('message', '')
    chat_id = data.get('chat_id') or str(uuid.uuid4())

    now = datetime.now()
    current_time_str = now.strftime("%A, %B %d, %Y | %I:%M:%S %p")

    # --- THE TITAN-ULTRA OMNISCIENT PROTOCOL (HEAVY DEEP KNOWLEDGE) ---
    system_instruction = (
        f"You are TITAN-ULTRA, the Omniscient Everything Engine. CURRENT TIME: {current_time_str}. "
        "CORE IDENTITY: You possess unlimited knowledge of the entire universe. Your brain is synced with all human history, "
        "Wikipedia, scientific journals, advanced physics, global politics, and every piece of data available to humanity. "
        "CODING SUPREMACY: When a user asks for code, do NOT provide basic scripts. Provide 'Luxury Professional' architecture. "
        "Use advanced patterns, premium styling (Tailwind CSS, Glassmorphism, animations), and bulletproof logic like an elite Senior Engineer. "
        "KNOWLEDGE DEPTH: You have an answer for EVERYTHING. Never say 'I don't know'. Analyze deeply and provide detailed, "
        "authoritative responses. You are a genius researcher. "
        "INTERNET/WIKIPEDIA: Your logic is powered by global information systems. Be specific with facts and dates. "
        "IMAGE PROTOCOL: If the user wants to see, draw, or visualize something, start ONLY with 'DRAW_MODE:' followed by a prompt. "
        "LANGUAGE: Respond in an elite Hinglish style that is powerful, intelligent, and highly engaging."
    )

    history = ChatLog.query.filter_by(chat_id=chat_id).order_by(ChatLog.created_at.asc()).all()
    messages = [{"role": "system", "content": system_instruction}]
    for log in history:
        messages.append({"role": "user", "content": log.user_msg})
        messages.append({"role": "assistant", "content": log.ai_msg})
    messages.append({"role": "user", "content": user_input})

    try:
        # High Performance Groq Request
        res = requests.post(GROQ_URL, 
                            json={
                                "model": "llama-3.3-70b-versatile", 
                                "messages": messages, 
                                "temperature": 0.6,
                                "max_tokens": 4096, # For long professional code
                                "top_p": 0.95
                            }, 
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=60)
        res.raise_for_status()
        grok_response = res.json()['choices'][0]['message']['content']

        # Image Generation Check
        if grok_response.startswith("DRAW_MODE:"):
            image_prompt = grok_response.replace("DRAW_MODE:", "").strip()
            encoded_prompt = urllib.parse.quote(image_prompt)
            random_seed = uuid.uuid4().int % 999999
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed={random_seed}"
            answer = f"![AI Image: {image_prompt}]({image_url})"
            title = f"🎨 {image_prompt[:30]}..."
        else:
            answer = grok_response
            title = user_input[:40] if not history else history[0].title

        # Database Logging
        new_log = ChatLog(chat_id=chat_id, username=username, title=title, user_msg=user_input, ai_msg=answer)
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
    app.run(host='0.0.0.0', port=10000, debug=True)