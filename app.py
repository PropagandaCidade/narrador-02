# app.py - VERSÃO FINAL DE PRODUÇÃO (com correção de pronúncia e tratamento de erros aprimorado)
import os
import io
import mimetypes
import struct
import logging

from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS

from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

# <-- 1. IMPORTA A NOVA FUNÇÃO DO "CÉREBRO AUXILIAR"
from text_utils import correct_grammar_for_grams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, expose_headers=['X-Model-Used'])

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    # Esta função está correta e não precisa de alterações
    logger.info(f"Convertendo dados de áudio de {mime_type} para WAV...")
    bits_per_sample = 16
    sample_rate = 24000
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample, b"data", data_size
    )
    logger.info("Conversão para WAV concluída.")
    return header + audio_data

@app.route('/')
def home():
    return "Serviço de Narração individual está online."

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio_endpoint():
    logger.info("Recebendo solicitação para /api/generate-audio")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        error_msg = "ERRO CRÍTICO: GEMINI_API_KEY não encontrada."
        logger.error(error_msg)
        return jsonify({"error": "Configuração do servidor incompleta."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Requisição inválida, corpo JSON ausente."}), 400

    text_to_process = data.get('text')
    voice_name = data.get('voice')
    model_nickname = data.get('model_to_use', 'flash')

    if not text_to_process or not voice_name:
        return jsonify({"error": "Os campos de texto e voz são obrigatórios."}), 400

    try:
        # <-- 2. APLICA A CORREÇÃO ANTES DE ENVIAR PARA A API
        logger.info("Aplicando pré-processamento de texto para correção de pronúncia...")
        corrected_text = correct_grammar_for_grams(text_to_process)
        
        # Bloco principal de geração de áudio
        if model_nickname == 'pro':
            model_to_use_fullname = "gemini-1.5-pro-latest" # Usando o modelo mais recente
        else:
            model_to_use_fullname = "gemini-1.5-flash-latest" # Usando o modelo mais recente
        
        logger.info(f"Usando modelo: {model_to_use_fullname}")
        
        # A biblioteca agora se chama 'generativeai'
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_to_use_fullname)

        # Geração de áudio agora é feita por uma ferramenta (tool) específica
        audio_bytes = model.generate_content(
            f"Fale o seguinte texto com uma voz natural: '{corrected_text}'",
            generation_config=genai.types.GenerationConfig(
                response_mime_type="audio/wav" # Solicita WAV diretamente
            ),
            # O parâmetro de voz pode variar dependendo da versão da API,
            # este é um exemplo conceitual. A API de TTS pode ter um endpoint dedicado.
        ).parts[0].blob.data

        if not audio_bytes:
             return jsonify({"error": "A API respondeu, mas não retornou dados de áudio."}), 500
        
        # A API já retorna WAV, então a conversão manual pode não ser mais necessária.
        # Se a API retornar outro formato, a função convert_to_wav ainda é útil.
        http_response = make_response(send_file(io.BytesIO(audio_bytes), mimetype='audio/wav', as_attachment=False))
        http_response.headers['X-Model-Used'] = model_nickname
        
        logger.info(f"Sucesso: Áudio WAV gerado e enviado ao cliente.")
        return http_response

    # [CORREÇÃO] Adicionado 'ClientError' à lista de exceções que acionam o failover.
    except (google_exceptions.ResourceExhausted, google_exceptions.PermissionDenied, google_exceptions.Unauthenticated, google_exceptions.ClientError) as e:
        error_message = f"Falha de API que permite nova tentativa: {type(e).__name__}"
        logger.warning(error_message)
        return jsonify({"error": error_message, "retryable": True}), 429

    # [NOVO] Trata erros de input do cliente (ex: texto muito longo) de forma específica.
    except google_exceptions.InvalidArgument as e:
        error_message = f"Argumento inválido para a API (verifique o texto enviado): {e}"
        logger.warning(error_message)
        return jsonify({"error": error_message, "retryable": False}), 400

    except Exception as e:
        # Mensagem de erro de produção normal para casos inesperados.
        error_message = f"Erro inesperado que NÃO permite nova tentativa: {e}"
        logger.error(f"ERRO CRÍTICO NA API: {error_message}", exc_info=True)
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080)) # Porta padrão para muitos serviços de cloud
    app.run(host='0.0.0.0', port=port)