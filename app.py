import os
import struct
import io
import time
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
# [ALTERADO] Importações do Google para serem mais explícitas
import google.generativeai as genai
from google.generativeai import types
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins="*", expose_headers=['X-Model-Used'])

# --- LÓGICA DE GERAÇÃO DE ÁUDIO (Inalterada, mas a chamada do cliente será ajustada) ---
def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    # ... (código inalterado)
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters.get("bits_per_sample", 16)
    sample_rate = parameters.get("rate", 24000)
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1,
        num_channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b"data", data_size
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    # ... (código inalterado)
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError): pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError): pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}

@app.route('/')
def home():
    return "Backend do Gerador de Narração e Chat está online."

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio_endpoint():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Configuração do servidor incompleta: Chave da API Gemini ausente."}), 500

    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "Requisição inválida, texto ausente."}), 400
        
    text_to_narrate = data.get('text')
    voice_name = data.get('voice')
    # O 'style' aqui é o prompt final, já montado pelo PHP
    final_prompt = data.get('style') 

    try:
        # [ALTERADO] A API Key agora é configurada aqui
        genai.configure(api_key=api_key)
        
        # Modelo para TTS
        model_tts = "models/text-to-speech"
        
        # Gera o áudio
        response = genai.speech.generate_content(
            model=model_tts,
            voice=voice_name,
            content=final_prompt,
        )

        # Converte para WAV
        wav_data = convert_to_wav(response.audio_data, response.mime_type)
        
        # Cria a resposta e adiciona o cabeçalho
        resp = make_response(send_file(io.BytesIO(wav_data), mimetype='audio/wav', as_attachment=False))
        resp.headers['X-Model-Used'] = 'Gemini-TTS'
        return resp

    except Exception as e:
        print(f"Ocorreu um erro na API Gemini: {e}")
        return jsonify({"error": f"Erro ao contatar a API do Gemini: {e}"}), 500

# --- LÓGICA DE CHAT COM OPENAI ASSISTANT (Inalterada) ---

@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        return jsonify({"error": "Configuração do servidor OpenAI incompleta."}), 500

    client = OpenAI(api_key=openai_api_key)
    assistant_id = "asst_uBT51vqa34fyS9ExqP859UmM"

    data = request.get_json()
    user_message = data.get('message')
    thread_id = data.get('thread_id')

    if not user_message:
        return jsonify({"error": "A mensagem não pode estar vazia."}), 400

    try:
        if thread_id is None:
            thread = client.beta.threads.create()
            thread_id = thread.id

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1) 
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
            assistant_response = messages.data[0].content[0].text.value
            return jsonify({
                "response": assistant_response,
                "thread_id": thread_id
            })
        else:
            return jsonify({"error": f"A execução falhou com o status: {run.status}"}), 500

    except Exception as e:
        print(f"Erro na API OpenAI: {e}")
        return jsonify({"error": f"Erro ao contatar a API OpenAI: {str(e)}"}), 500