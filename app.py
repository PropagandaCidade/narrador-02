import os
import struct
import io
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

app = Flask(__name__)
CORS(app, expose_headers=['X-Model-Used']) # 👈 IMPORTANTE: Expor o cabeçalho customizado

# (As funções convert_to_wav e parse_audio_mime_type permanecem as mesmas)
def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    # ... código sem alterações ...
def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    # ... código sem alterações ...

def generate_audio_from_model(client, model_name, contents, config):
    # ... código sem alterações ...

@app.route('/')
def home():
    return "Backend do Gerador de Narração está online."

@app.route('/generate-audio', methods=['POST'])
def generate_audio_endpoint():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Configuração do servidor incompleta"}), 500

    data = request.get_json()
    text_to_narrate = data.get('text')
    voice_name = data.get('voice')
    style_instructions_text = data.get('style')

    if not text_to_narrate:
        return jsonify({"error": "O texto não pode estar vazio."}), 400

    client = genai.Client(api_key=api_key)
    
    parts_list = []
    if style_instructions_text:
        parts_list.append(types.Part.from_text(text=style_instructions_text))
    parts_list.append(types.Part.from_text(text=text_to_narrate))
    contents = [types.Content(role="user", parts=parts_list)]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
    )

    model_to_use = "Pro"
    try:
        # 1. Tenta com o modelo PRO (Premium)
        wav_data = generate_audio_from_model(client, "gemini-2.5-pro-preview-tts", contents, generate_content_config)
        print("Sucesso com o modelo Pro!")
        
    except google_exceptions.ResourceExhausted as e:
        # 2. Se a cota do Pro esgotar, tenta com o modelo FLASH (Failover)
        print(f"Cota do Pro esgotada. Tentando com o modelo Flash. Erro: {e}")
        model_to_use = "Flash"
        try:
            wav_data = generate_audio_from_model(client, "gemini-2.5-flash-preview-tts", contents, generate_content_config)
            print("Sucesso com o modelo Flash (failover)!")
        except Exception as e_flash:
            print(f"Falha também com o modelo Flash. Erro: {e_flash}")
            return jsonify({"error": f"Ambos os modelos de narração estão indisponíveis. Erro: {e_flash}"}), 500
    
    except Exception as e:
        print(f"Ocorreu um erro inesperado com o modelo Pro: {e}")
        return jsonify({"error": f"Erro ao contatar a API do Gemini: {e}"}), 500

    # Cria a resposta de arquivo de áudio
    response = make_response(send_file(io.BytesIO(wav_data), mimetype='audio/wav', as_attachment=False))
    # Adiciona o cabeçalho customizado com o nome do modelo usado
    response.headers['X-Model-Used'] = model_to_use
    
    return response