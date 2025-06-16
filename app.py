import os
import struct
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# (Todas as funções convert_to_wav e parse_audio_mime_type permanecem as mesmas)
def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    # ... código sem alterações ...
def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    # ... código sem alterações ...

@app.route('/')
def home():
    return "Backend do Gerador de Narração está online."

@app.route('/generate-audio', methods=['POST'])
def generate_audio_endpoint():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Configuração do servidor incompleta: Chave da API ausente."}), 500

    data = request.get_json()
    text_to_narrate = data.get('text')
    voice_name = data.get('voice')
    style_instructions_text = data.get('style')

    if not text_to_narrate:
        return jsonify({"error": "O texto não pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        
        # <<<----------- A ÚNICA LINHA ALTERADA PARA O MODELO CORRETO -----------<<<
        model = "gemini-2.5-pro-preview-tts"
        # >>>-------------------------------------------------------------------->>>

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
        
        audio_buffer = bytearray()
        audio_mime_type = "audio/L16;rate=24000"
        
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=generate_content_config):
            if (chunk.candidates and chunk.candidates[0].content and
                chunk.candidates[0].content.parts and chunk.candidates[0].content.parts[0].inline_data and
                chunk.candidates[0].content.parts[0].inline_data.data):
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                audio_buffer.extend(inline_data.data)
                audio_mime_type = inline_data.mime_type

        if not audio_buffer:
            return jsonify({"error": "Não foi possível gerar o áudio."}), 500

        wav_data = convert_to_wav(bytes(audio_buffer), audio_mime_type)
        
        return send_file(io.BytesIO(wav_data), mimetype='audio/wav', as_attachment=False)

    except Exception as e:
        print(f"Ocorreu um erro na API: {e}")
        return jsonify({"error": f"Erro ao contatar a API do Gemini: {e}"}), 500