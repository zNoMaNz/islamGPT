from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = "sk-qbepeVm_VAGBKoMadOvxJMPAnd7v6cMnSzFqHHi14nT3BlbkFJyjC7QPjNA1H2sYO0L2LnL-P1a5IrFwyr_I5svHeCgA"

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json  # Get JSON data from the POST request
    question = data.get('question')  # Extract the question from the JSON

    # Define the messages with system and user inputs
    messages = [
        {"role": "system", "content": "You are an AI assistant knowledgeable in authentic Islamic teachings. Answer all questions by referencing the Quran and authentic Hadiths only."},
        {"role": "user", "content": question}
    ]

    # Call OpenAI API with the messages
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=150,  # Adjust as needed
            temperature=0.7  # Adjust as needed
        )
        answer = response.choices[0].message.content.strip()
        return jsonify({'answer': answer})  # Return the answer as JSON
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Return an error if something goes wrong

if __name__ == "__main__":
    app.run(debug=True)
