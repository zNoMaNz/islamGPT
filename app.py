import os
import uuid
import datetime
from flask import Flask, request, Response, render_template, stream_with_context
import openai

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

openai.api_key = os.getenv("OPENAI_API_KEY")

# We'll store a minimal context + log file info for each thread.
# Structure example:
# {
#   "192.168.1.100": {
#       "threads": {
#           "thread1": {
#               "last_user": "previous user question",
#               "last_assistant": "previous assistant reply",
#               "log_file": "logs/thread1.log"
#           },
#           "thread2": {
#               ...
#           }
#       }
#   }
# }
user_threads = {}

# Ensure a logs/ directory exists
os.makedirs("logs", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask_stream", methods=["POST"])
def ask_stream():
    """
    Handle user messages and respond with OpenAI ChatCompletion in streaming mode.
    Support multiple threads per user.
    """
    user_ip = request.remote_addr or "unknown_ip"
    data = request.get_json()
    thread_id = data.get("thread_id", "default")  # Default thread if no ID provided
    new_user_message = data.get("question", "").strip()

    # Initialize user context if not already present
    if user_ip not in user_threads:
        user_threads[user_ip] = {"threads": {}}

    # Initialize thread context if not already present
    if thread_id not in user_threads[user_ip]["threads"]:
        log_file_name = f"{uuid.uuid4()}_{thread_id}.log"
        user_threads[user_ip]["threads"][thread_id] = {
            "last_user": None,
            "last_assistant": None,
            "log_file": os.path.join("logs", log_file_name),
        }

        # Optional: Write a header to the new thread log file
        with open(user_threads[user_ip]["threads"][thread_id]["log_file"], "a", encoding="utf-8") as f:
            f.write(f"--- New thread '{thread_id}' started for IP {user_ip} ---\n")

    # Get the thread context
    thread_context = user_threads[user_ip]["threads"][thread_id]

    # Build the message array:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant knowledgeable in authentic Islamic teachings, Quran, and Hadiths. "
                "If the user asks in English, respond in English. If the user asks in Bangla, respond in Bnagla. And use references from Quran and Hadith where appropriate."
            ),
        }
    ]

    if thread_context["last_user"]:
        messages.append({"role": "user", "content": thread_context["last_user"]})

    if thread_context["last_assistant"]:
        messages.append({"role": "assistant", "content": thread_context["last_assistant"]})

    messages.append({"role": "user", "content": new_user_message})

    # Log the user's new message
    log_file_path = thread_context["log_file"]
    log_to_file(log_file_path, "user", new_user_message)

    def generate():
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                stream=True,
            )

            assistant_response = ""

            for chunk in response:
                content = chunk["choices"][0]["delta"].get("content", "")
                if content:
                    assistant_response += content
                    yield content  # Stream chunk back to the client

            # Update thread context
            thread_context["last_user"] = new_user_message
            thread_context["last_assistant"] = assistant_response

            # Log the assistant's response
            log_to_file(log_file_path, "assistant", assistant_response)

        except Exception as e:
            error_msg = f"[Error]: {str(e)}"
            yield error_msg
            # Log the error
            log_to_file(log_file_path, "assistant", error_msg)

    return Response(stream_with_context(generate()), mimetype="text/plain")

def log_to_file(filepath, role, content):
    """
    Append a line with a timestamp and the role/content to the specified log file.
    Format: [YYYY-MM-DD HH:MM:SS] ROLE: content
    """
    with open(filepath, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {role.upper()}: {content}\n")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
