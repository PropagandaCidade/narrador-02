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

// Variáveis de estado da aplicação
let selectedVoiceId = voices[0].id;
let audioSample = new Audio();

// --- FUNÇÕES ---

// Função para popular os menus <select> dinamicamente
function populateSelectOptions() {
    formatOptions.forEach(opt => {
        const option = new Option(opt.text, opt.value);
        formatSelect.add(option);
    });

    styleOptions.forEach(opt => {
        const option = new Option(opt.text, opt.value);
        styleSelect.add(option);
    });
}

// Função para atualizar a caixa de preview do prompt
function updatePromptPreview() {
    const text = textInput.value.trim();
    const format = formatSelect.value;
    const style = styleSelect.value;
    
    // Tenta encontrar o prompt. Se não encontrar uma combinação específica, usa o padrão do spot comercial.
    const stylePrompt = (prompts[format] && prompts[format][style]) 
        ? prompts[format][style] 
        : "A standard, professional voice with a clear tone:";

    if (text) {
        promptPreviewBox.innerText = `${stylePrompt}\n\n${text}`;
    } else {
        promptPreviewBox.innerText = "Digite um texto para ver o prompt final aqui.";
    }
}

// Função para renderizar os cards dos locutores nas grades corretas
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
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayer.src = audioUrl;
        audioPlayer.style.display = 'block';
        audioPlayer.play();
        statusMessage.textContent = 'Áudio gerado com sucesso!';
        statusMessage.style.color = '#2ecc71';
    } catch (error) {
        console.error('Erro:', error);
        statusMessage.textContent = `Erro ao gerar áudio: ${error.message}`;
        statusMessage.style.color = '#e74c3c';
    } finally {
        generateBtn.disabled = false;
    }
}

// --- EVENT LISTENERS ---

// Adiciona os gatilhos para atualizar o preview
textInput.addEventListener('input', updatePromptPreview);
formatSelect.addEventListener('change', updatePromptPreview);
styleSelect.addEventListener('change', updatePromptPreview);
generateBtn.addEventListener('click', generateAudio);

// --- INICIALIZAÇÃO DA PÁGINA ---

// Quando o DOM estiver pronto, popular os selects e renderizar os cards
document.addEventListener('DOMContentLoaded', () => {
    populateSelectOptions();
    renderVoiceCards();
    updatePromptPreview();
});