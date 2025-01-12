import os
import uuid
import datetime
from flask import Flask, request, Response, render_template, stream_with_context
import openai

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

openai.api_key = "sk-qbepeVm_VAGBKoMadOvxJMPAnd7v6cMnSzFqHHi14nT3BlbkFJyjC7QPjNA1H2sYO0L2LnL-P1a5IrFwyr_I5svHeCgA"

# We'll store a minimal context + log file info for each IP.
# Structure example:
# {
#   "192.168.1.100": {
#       "last_user": "previous user question",
#       "last_assistant": "previous assistant reply",
#       "log_file": "logs/some-unique-file.log"
#   }
# }
ip_contexts = {}

# Ensure a logs/ directory exists
os.makedirs("logs", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask_stream", methods=["POST"])
def ask_stream():
    """
    1) If this IP is new, create a log file for them.
    2) Send only the last user message + last assistant + new user message to OpenAI.
    3) Log every user/assistant message with timestamps to the file.
    """
    user_ip = request.remote_addr or "unknown_ip"

    # If we haven't seen this IP, initialize their context and create a new log file.
    if user_ip not in ip_contexts:
        session_filename = f"{uuid.uuid4()}.log"  # Unique file name
        ip_contexts[user_ip] = {
            "last_user": None,
            "last_assistant": None,
            "log_file": os.path.join("logs", session_filename),
        }

        # Optional: Write a header to the new log file
        with open(ip_contexts[user_ip]["log_file"], "a", encoding="utf-8") as f:
            f.write(f"--- New session started for IP {user_ip} ---\n")

    data = request.get_json()
    new_user_message = data.get("question", "").strip()

    # Build the minimal message array:
    # 1) system, 2) last user, 3) last assistant, 4) new user
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant knowledgeable in authentic Islamic teachings, Quran, and Hadiths. Use English when English is used."
                "Whatever language the user uses, respond in the same language. Use references from Quran and Hadith when needed to bolster your statements"
            ),
        }
    ]

    if ip_contexts[user_ip]["last_user"]:
        messages.append({"role": "user", "content": ip_contexts[user_ip]["last_user"]})

    if ip_contexts[user_ip]["last_assistant"]:
        messages.append({"role": "assistant", "content": ip_contexts[user_ip]["last_assistant"]})

    messages.append({"role": "user", "content": new_user_message})

    # Log the user's new message
    log_file_path = ip_contexts[user_ip]["log_file"]
    log_to_file(log_file_path, "user", new_user_message)

    def generate():
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # or gpt-4
                messages=messages,
                temperature=0.7,
                stream=True
            )

            assistant_response = ""

            for chunk in response:
                content = chunk["choices"][0]["delta"].get("content", "")
                if content:
                    assistant_response += content
                    yield content  # Stream chunk back to the client

            # Update minimal context
            ip_contexts[user_ip]["last_user"] = new_user_message
            ip_contexts[user_ip]["last_assistant"] = assistant_response

            # Log the final assistant reply
            log_to_file(log_file_path, "assistant", assistant_response)

        except Exception as e:
            error_msg = f"[Error]: {str(e)}"
            yield error_msg
            # Log the error, too
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
