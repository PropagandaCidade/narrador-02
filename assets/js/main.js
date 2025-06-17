// --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

// Pega os elementos do DOM
const textInput = document.getElementById('text-input');
const formatSelect = document.getElementById('format-select');
const styleSelect = document.getElementById('style-select');
const femaleVoiceGrid = document.getElementById('female-voice-grid');
const maleVoiceGrid = document.getElementById('male-voice-grid');
const generateBtn = document.getElementById('generate-btn');
const statusMessage = document.getElementById('status-message');
const audioPlayer = document.getElementById('audio-player');
const promptPreviewBox = document.getElementById('prompt-preview-box');
const modelInfoDiv = document.getElementById('model-info'); // 👈 Pega o novo div

// ... (O resto das variáveis de estado permanecem as mesmas) ...
let selectedVoiceId = voices[0].id;
let audioSample = new Audio();

// ... (As funções populateSelectOptions, updatePromptPreview, renderVoiceCards, handleVoiceSelection permanecem as mesmas) ...

// Função principal de geração de áudio (ATUALIZADA)
async function generateAudio() {
    const text = textInput.value.trim();
    const format = formatSelect.value;
    const style = styleSelect.value;
    const stylePrompt = (prompts[format] && prompts[format][style]) 
        ? prompts[format][style] 
        : "A standard, professional voice with a clear tone:";

    if (!text) {
        statusMessage.textContent = 'Por favor, digite um texto para gerar o áudio.';
        statusMessage.style.color = '#e74c3c'; 
        return;
    }

    generateBtn.disabled = true;
    statusMessage.textContent = 'Gerando áudio, por favor aguarde...';
    modelInfoDiv.style.opacity = 0; // 👈 Esconde a informação do modelo anterior
    statusMessage.style.color = 'var(--accent-color)';
    audioPlayer.style.display = 'none';

    try {
        const response = await fetch('https://meu-narrador-virtual.onrender.com/generate-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, voice: selectedVoiceId, style: stylePrompt }),
        });

        if (!response.ok) {
            const errorData = await response.json(); 
            throw new Error(errorData.error || 'Ocorreu um erro no servidor.');
        }

        // --- LÓGICA PARA LER O CABEÇALHO ---
        // 1. Pega o valor do cabeçalho customizado 'X-Model-Used'
        const modelUsed = response.headers.get('X-Model-Used');
        
        // 2. Exibe a mensagem de sucesso e a informação do modelo
        statusMessage.textContent = 'Áudio gerado com sucesso!';
        statusMessage.style.color = '#2ecc71';
        
        if (modelUsed) {
            modelInfoDiv.textContent = `(Modelo Utilizado: Gemini 2.5 ${modelUsed})`;
            modelInfoDiv.style.opacity = 1; // 👈 Mostra a informação com um fade-in
        }
        // ------------------------------------
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayer.src = audioUrl;
        audioPlayer.style.display = 'block';
        audioPlayer.play();

    } catch (error) {
        console.error('Erro:', error);
        statusMessage.textContent = `Erro ao gerar áudio: ${error.message}`;
        statusMessage.style.color = '#e74c3c';
    } finally {
        generateBtn.disabled = false;
    }
}


// (O resto do arquivo main.js, com os Event Listeners e a Inicialização, permanece o mesmo)
textInput.addEventListener('input', updatePromptPreview);
// ... etc ...