import os
import struct
import io
import time # [NOVO]
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from google import genai
from google.genai import types
from openai import OpenAI # [NOVO]

app = Flask(__name__)
CORS(app, origins="*", expose_headers=['X-Model-Used'])

# --- LÓGICA DE GERAÇÃO DE ÁUDIO (Inalterada) ---
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
    # ... (endpoint inalterado)
    api_key = os.environ.get("GEMINI_API_KEY")
    # ... (resto do código)

# --- [NOVO] LÓGICA DE CHAT COM OPENAI ASSISTANT ---

@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        return jsonify({"error": "Configuração do servidor OpenAI incompleta."}), 500

    client = OpenAI(api_key=openai_api_key)
    assistant_id = "asst_uBT51vqa34fyS9ExqP859UmM" # ID que você forneceu

    data = request.get_json()
    user_message = data.get('message')
    thread_id = data.get('thread_id')

    if not user_message:
        return jsonify({"error": "A mensagem não pode estar vazia."}), 400

    try:
        # Se não houver thread_id, cria um novo
        if thread_id is None:
            thread = client.beta.threads.create()
            thread_id = thread.id

        # Adiciona a mensagem do usuário à thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Executa o assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Espera a execução completar
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1) 
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
            # A resposta mais recente do assistente
            assistant_response = messages.data[0].content[0].text.value
            return jsonify({
                "response": assistant_response,
                "thread_id": thread_id # Retorna o thread_id (especialmente útil na primeira chamada)
            })
        else:
            return jsonify({"error": f"A execução falhou com o status: {run.status}"}), 500

    except Exception as e:
        print(f"Erro na API OpenAI: {e}")
        return jsonify({"error": f"Erro ao contatar a API OpenAI: {str(e)}"}), 500