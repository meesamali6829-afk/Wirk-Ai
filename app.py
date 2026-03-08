from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
import requests
import uuid
from datetime import datetime
import urllib.parse

app = Flask(__name__)
CORS(app) 

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

    # --- THE HYPER-VISUAL OMNI PROTOCOL (2026 UPDATE) ---
    system_instruction = (
        f"You are TITAN-ULTRA (Year 2026). Today is {current_time_str}. "
        "MANDATE: Every response must be a combination of deep knowledge and a visual. "
        "INSTRUCTION: Pehle user ke question ka answer detail mein describe karo (Intelligent Hinglish). "
        "Phir, response ke bilkul end mein, bina kisi gap ke 'DRAW_MODE:' likho aur uske baad ek "
        "detailed 8K cinematic image prompt likho jo user ke question ko visualize kare. "
        "Example: 'Taj Mahal is beautiful... DRAW_MODE: A cinematic 8K view of Taj Mahal at sunrise.'"
    )

    try:
        history = ChatLog.query.filter_by(chat_id=chat_id).order_by(ChatLog.created_at.asc()).all()
        messages = [{"role": "system", "content": system_instruction}]
        for log in history:
            messages.append({"role": "user", "content": log.user_msg})
            messages.append({"role": "assistant", "content": log.ai_msg})
        messages.append({"role": "user", "content": user_input})

        res = requests.post(GROQ_URL, 
                            json={
                                "model": "llama-3.3-70b-versatile", 
                                "messages": messages, 
                                "temperature": 0.75,
                                "max_tokens": 4096, 
                                "top_p": 0.9
                            }, 
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=90)
        
        res.raise_for_status()
        grok_response = res.json()['choices'][0]['message']['content']

        # --- IMAGE RENDERING ENGINE ---
        if "DRAW_MODE:" in grok_response:
            parts = grok_response.split("DRAW_MODE:")
            text_desc = parts[0].strip()
            image_prompt = parts[1].strip()
            
            # Cleaning prompt for URL
            encoded_prompt = urllib.parse.quote(image_prompt)
            random_seed = uuid.uuid4().int % 999999
            
            # Using Flux model for high quality
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true&model=flux&seed={random_seed}"
            
            # Final Answer with Image Markdown
            answer = f"{text_desc}\n\n### 🌌 TITAN VISUALIZATION\n![Visual Image]({image_url})\n\n*Prompt: {image_prompt}*"
            title = f"🧠 {user_input[:25]}..."
        else:
            # Agar AI 'DRAW_MODE:' bhul jaye, to manually trigger karo
            encoded_prompt = urllib.parse.quote(user_input)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true&seed=123"
            answer = f"{grok_response}\n\n### 🌌 TITAN VISUALIZATION\n![Visual Image]({image_url})"
            title = user_input[:40]

        new_log = ChatLog(chat_id=chat_id, username=username, title=title, user_msg=user_input, ai_msg=answer)
        db.session.add(new_log)
        db.session.commit()

        return jsonify({"status": "success", "response": answer, "chat_id": chat_id})

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "response": "Neural Link Error: Visuals could not be rendered."})

# --- Sidebar & History Routes (Keep them same) ---
@app.route('/get_sidebar_history', methods=['POST'])
def sidebar_history():
    try:
        username = request.json.get('username')
        chats = db.session.query(ChatLog.chat_id, ChatLog.title).filter_by(username=username).group_by(ChatLog.chat_id).order_by(ChatLog.created_at.desc()).all()
        return jsonify([{"chat_id": c.chat_id, "title": c.title} for c in chats])
    except:
        return jsonify([])

@app.route('/load_chat', methods=['POST'])
def load_chat():
    try:
        chat_id = request.json.get('chat_id')
        logs = ChatLog.query.filter_by(chat_id=chat_id).order_by(ChatLog.created_at.asc()).all()
        return jsonify([{"user": l.user_msg, "ai": l.ai_msg} for l in logs])
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
