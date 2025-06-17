// --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

// Pega os elementos do DOM
const textInput = document.getElementById('text-input');
const formatSelect = document.getElementById('format-select');
const styleSelect = document.getElementById('style-select');
const speedSelect = document.getElementById('speed-select');
const femaleVoiceGrid = document.getElementById('female-voice-grid');
const maleVoiceGrid = document.getElementById('male-voice-grid');
const generateBtn = document.getElementById('generate-btn');
const statusMessage = document.getElementById('status-message');
const audioPlayer = document.getElementById('audio-player');
const promptPreviewBox = document.getElementById('prompt-preview-box');
const modelInfoDiv = document.getElementById('model-info');

// Variáveis de estado da aplicação
// A variável 'voices' é lida do arquivo voices.js
let selectedVoiceId = voices[0].id;
let audioSample = new Audio();

// --- FUNÇÕES ---

// Função para popular os menus <select> dinamicamente
// Ela usa 'formatOptions', 'styleOptions' e 'speedOptions' do arquivo prompts.js
function populateSelectOptions() {
    formatOptions.forEach(opt => {
        formatSelect.add(new Option(opt.text, opt.value));
    });

    styleOptions.forEach(opt => {
        styleSelect.add(new Option(opt.text, opt.value));
    });

    speedOptions.forEach(opt => {
        speedSelect.add(new Option(opt.text, opt.value));
    });
    
    speedSelect.value = '2'; // Define a velocidade padrão como "2. Normal"
}

// Função para atualizar a caixa de preview do prompt
function updatePromptPreview() {
    const text = textInput.value.trim();
    const format = formatSelect.value;
    const style = styleSelect.value;
    const speed = speedSelect.value;
    
    let finalStylePrompt = (prompts[format] && prompts[format][style]) 
        ? prompts[format][style] 
        : "A standard, professional voice with a clear tone:";

    const speedInstruction = (speed !== '2' && speedPrompts[speed]) ? speedPrompts[speed] : "";

    if (speedInstruction) {
        finalStylePrompt = finalStylePrompt.replace(/:$/, `. ${speedInstruction}`);
    }

    if (text) {
        promptPreviewBox.innerText = `${finalStylePrompt}\n\n${text}`;
    } else {
        promptPreviewBox.innerText = "Digite um texto para ver o prompt final aqui.";
    }
}

// Função para renderizar os cards dos locutores nas grades corretas
// Ela usa a variável 'voices' do arquivo voices.js
function renderVoiceCards() {
    femaleVoiceGrid.innerHTML = '';
    maleVoiceGrid.innerHTML = '';

    const femaleVoices = voices.filter(v => v.gender === 'F');
    const maleVoices = voices.filter(v => v.gender === 'M');
    
    const createCard = (voice, grid) => {
        const isSelected = voice.id === selectedVoiceId;
        const card = document.createElement('div');
        card.className = `voice-card ${isSelected ? 'selected' : ''}`;
        card.setAttribute('data-voice-id', voice.id);
        card.innerHTML = `
            <img src="${voice.imageUrl}" alt="Locutor(a) ${voice.name}">
            <div class="voice-name">${voice.name}</div>
            <div class="voice-specialty">${voice.specialty}</div>
        `;
        card.addEventListener('click', () => handleVoiceSelection(voice));
        grid.appendChild(card);
    };

    femaleVoices.forEach(voice => createCard(voice, femaleVoiceGrid));
    maleVoices.forEach(voice => createCard(voice, maleVoiceGrid));
}

// Função que lida com a seleção de uma voz
function handleVoiceSelection(voice) {
    selectedVoiceId = voice.id;
    audioSample.src = voice.audioUrl;
    audioSample.play().catch(e => console.error("Erro ao tocar amostra:", e));
    renderVoiceCards();
}

// Função principal de geração de áudio
async function generateAudio() {
    const text = textInput.value.trim();
    const format = formatSelect.value;
    const style = styleSelect.value;
    const speed = speedSelect.value;

    let finalStylePrompt = (prompts[format] && prompts[format][style]) 
        ? prompts[format][style] 
        : "A standard, professional voice with a clear tone:";

    const speedInstruction = (speed !== '2' && speedPrompts[speed]) ? speedPrompts[speed] : "";

    if (speedInstruction) {
        finalStylePrompt = finalStylePrompt.replace(/:$/, `. ${speedInstruction}`);
    }

    if (!text) {
        statusMessage.textContent = 'Por favor, digite um texto para gerar o áudio.';
        statusMessage.style.color = '#e74c3c'; 
        return;
    }

    generateBtn.disabled = true;
    statusMessage.textContent = 'Gerando áudio, por favor aguarde...';
    modelInfoDiv.style.opacity = 0;
    statusMessage.style.color = 'var(--accent-color)';
    audioPlayer.style.display = 'none';

    try {
        const response = await fetch('https://meu-narrador-virtual.onrender.com/generate-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, voice: selectedVoiceId, style: finalStylePrompt }),
        });

        if (!response.ok) {
            const errorData = await response.json(); 
            throw new Error(errorData.error || 'Ocorreu um erro no servidor.');
        }

        const modelUsed = response.headers.get('X-Model-Used');
        statusMessage.textContent = 'Áudio gerado com sucesso!';
        statusMessage.style.color = '#2ecc71';
        
        if (modelUsed) {
            modelInfoDiv.textContent = `(Modelo Utilizado: Gemini 2.5 ${modelUsed})`;
            modelInfoDiv.style.opacity = 1;
        }
        
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

// --- EVENT LISTENERS ---
textInput.addEventListener('input', updatePromptPreview);
formatSelect.addEventListener('change', updatePromptPreview);
styleSelect.addEventListener('change', updatePromptPreview);
speedSelect.addEventListener('change', updatePromptPreview);
generateBtn.addEventListener('click', generateAudio);

// --- INICIALIZAÇÃO DA PÁGINA ---
document.addEventListener('DOMContentLoaded', () => {
    populateSelectOptions();
    renderVoiceCards();
    updatePromptPreview();
});