from flask import Flask, request, jsonify, make_response, render_template
import openai

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Set your OpenAI API key
openai.api_key = "sk-qbepeVm_VAGBKoMadOvxJMPAnd7v6cMnSzFqHHi14nT3BlbkFJyjC7QPjNA1H2sYO0L2LnL-P1a5IrFwyr_I5svHeCgA"

@app.route("/")
def index():
    """
    Returns the HTML page (index.html) from the 'templates' folder.
    """
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant knowledgeable in authentic Islamic teachings. "
                "If the user asks a question in Bangla, respond with Bangla text "
                "using references from the Quran and authentic Hadiths only. "
                "If the user’s question is in another language, you may respond in that language, "
                "but prefer Bangla whenever possible."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # or "gpt-3.5-turbo"
            messages=messages,
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()

        resp = make_response(jsonify({'answer': answer}))
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp
    except Exception as e:
        error_resp = make_response(jsonify({'error': str(e)}))
        error_resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_resp, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

