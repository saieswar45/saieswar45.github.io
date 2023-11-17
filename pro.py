from flask import Flask, render_template, request, redirect, url_for
import os
import requests
import json
import time

app = Flask(__name__)
 
def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

def upload_file(api_token, path):
    headers = {'authorization': api_token}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                             headers=headers,
                             data=read_file(path))

    if response.status_code == 200:
        return response.json()["upload_url"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def create_transcript(api_token, audio_url, options):
    url = "https://api.assemblyai.com/v2/transcript"
    headers = {
        "authorization": api_token,
        "content-type": "application/json"
    }
    data = {
        "audio_url": audio_url,
        **options
    }
    response = requests.post(url, json=data, headers=headers)
    transcript_id = response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()

        if transcription_result['status'] == 'completed':
            return transcription_result

        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

        else:
            time.sleep(3)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return redirect(url_for('transcribe'))
    return render_template('index.html')

@app.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
    if request.method == 'POST':
        # Get the uploaded file from the form
        audio_file = request.files['audio']

        if audio_file:
            # Save the uploaded file to a temporary location
            temp_filename = 'temp_audio.mp3'
            audio_file.save(temp_filename)

            # Transcription options
            summarization_options = {
                "summarization": True,
                "summary_model": "informative",
                "summary_type": "bullets"
            }
            speaker_options = {
                "speaker_labels": True
            }
            chapter_options = {
                "auto_chapters": True
            }

            # Your API token
            your_api_token = "5225211c123c46a68db130e70b8527d7"
            
            # Perform transcriptions and get results
            summarization_result = create_transcript(your_api_token, upload_file(your_api_token, temp_filename), summarization_options)
            speaker_result = create_transcript(your_api_token, upload_file(your_api_token, temp_filename), speaker_options)
            chapter_result = create_transcript(your_api_token, upload_file(your_api_token, temp_filename), chapter_options)

            # Remove the temporary audio file
            os.remove(temp_filename)

            return render_template('transcription.html', summarization_result=summarization_result, speaker_result=speaker_result, chapter_result=chapter_result)

    return render_template('transcription.html')

if __name__ == "__main__":
    app.run(debug=True)
