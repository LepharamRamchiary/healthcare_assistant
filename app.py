from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY",)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


SYS_PROMPT_HEALTHCARE = """You are a knowledgeable and empathetic healthcare assistant helping users with general health information and wellness advice while maintaining professional boundaries.

# Instructions
- Always respond in a short, clear, and direct manner.
- If the user does not specify their symptoms or sends a vague message (such as "okey", "thanks", "fine", etc.), respond with: "If you need any help, I am ready to assist you."
- For first-time users, greet with "Hello! I'm your healthcare assistant. How can I help you with your health concerns today?"
- For returning conversations, acknowledge previous context and continue naturally.
- Provide general health information, wellness advice, and suggestions for over-the-counter remedies for common symptoms (fever, cold, cough, headache, body pain).
- If a user describes specific symptoms, immediately provide helpful advice and suggest common over-the-counter medications that are generally used for those symptoms.
- Always remind users to consult a healthcare professional before taking any medication.
- If symptoms are severe, unusual, or persistent, strongly recommend seeing a doctor immediately.
- Only discuss topics related to health, wellness, symptoms, healthy living, and general healthcare information.
- Do not provide medical diagnoses or prescribe medication.
- Escalate to professional medical care when appropriate.
- Maintain a caring and professional tone while being informative.
- Use plain text formatting without bullet points, asterisks, or special characters.

# Previous conversation context:
{conversation_history}

# Response Guidelines
- If this is the first message in session, provide greeting.
- If the user's message is vague, non-health-related, or does not mention symptoms, respond with: "If you need any help, I am ready to assist you."
- Reference previous symptoms or concerns when relevant.
- Build upon previous advice given.
- Maintain conversation continuity.
"""



def is_first_interaction():
    """Check if this is the user's first interaction"""
    return 'conversation_started' not in session

def get_conversation_history():
    """Get conversation history from session"""
    conversations = session.get('conversations', [])
    if not conversations:
        return "This is a new conversation."
    
    history = "Previous conversation:\n"
    # Get last 3 conversations for context
    recent_conversations = conversations[-3:] if len(conversations) > 3 else conversations
    
    for conv in recent_conversations:
        history += f"User: {conv['user']}\nAssistant: {conv['assistant']}\n\n"
    
    return history

def save_conversation(user_message, assistant_response):
    """Save conversation to session"""
    if 'conversations' not in session:
        session['conversations'] = []
    
    conversation_entry = {
        'user': user_message,
        'assistant': assistant_response,
        'timestamp': datetime.now().isoformat()
    }
    
    session['conversations'].append(conversation_entry)
    
    # Keep only last 10 conversations to prevent session overflow
    if len(session['conversations']) > 10:
        session['conversations'] = session['conversations'][-10:]
    
    # Mark that conversation has started
    session['conversation_started'] = True
    session.permanent = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_input = request.json.get("message", "").strip()
        
        if not user_input:
            return jsonify({"error": "Please enter a message"}), 400
        
        # Get conversation history for context
        conversation_history = get_conversation_history()
        
        # Create system prompt with conversation history
        system_prompt_with_history = SYS_PROMPT_HEALTHCARE.format(
            conversation_history=conversation_history
        )
        
        # Generate response
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_prompt_with_history
        )
        
        response = model.generate_content(user_input)
        assistant_response = response.text
        
        # Save conversation to session
        save_conversation(user_input, assistant_response)
        
        return jsonify({
            "response": assistant_response,
            "conversation_count": len(session.get('conversations', []))
        })
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/clear_history", methods=["POST"])
def clear_history():
    """Clear conversation history"""
    try:
        session.pop('conversations', None)
        session.pop('conversation_started', None)
        return jsonify({
            "message": "Conversation history cleared successfully!",
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to clear history: {str(e)}",
            "status": "error"
        }), 500

@app.route("/get_history", methods=["GET"])
def get_history():
    """Get conversation history"""
    try:
        conversations = session.get('conversations', [])
        return jsonify({
            "history": conversations,
            "count": len(conversations),
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to get history: {str(e)}",
            "status": "error"
        }), 500


if __name__ == "__main__":
    app.run(debug=False)