/**
 * RuralCare AI - Voice Assistant (STT & TTS)
 * Powered by Web Speech API with regional Indian locale mapping.
 */

const VoiceAssistant = {
    recognition: null,
    isRecording: false,
    synth: window.speechSynthesis,
    activeUtterance: null,

    // Indian locale codes for Web Speech API
    localeMap: {
        en: "en-IN",
        kn: "kn-IN",
        hi: "hi-IN",
        ta: "ta-IN",
        te: "te-IN"
    },

    init: function() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Web Speech API not supported in this browser. Falling back to text input.");
            return false;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;

        this.recognition.onstart = () => {
            this.isRecording = true;
            this.updateVoiceUI(true);
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const inputElem = document.getElementById("symptomInput");
            if (inputElem) {
                if (finalTranscript) {
                    inputElem.value = (inputElem.value ? inputElem.value + " " : "") + finalTranscript;
                } else if (interimTranscript) {
                    // Show live interim in status or preview
                    const statusElem = document.getElementById("voiceStatusText");
                    if (statusElem) statusElem.innerText = interimTranscript;
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.stopRecording();
            const statusElem = document.getElementById("voiceStatusText");
            if (statusElem) {
                if (event.error === 'not-allowed') {
                    statusElem.innerText = "Microphone access blocked. Please allow mic permission.";
                } else {
                    statusElem.innerText = `Voice error: ${event.error}`;
                }
            }
        };

        this.recognition.onend = () => {
            this.isRecording = false;
            this.updateVoiceUI(false);
        };

        return true;
    },

    toggleRecording: function() {
        if (!this.recognition) {
            if (!this.init()) {
                alert("Voice recognition is not supported in this browser. Please use Google Chrome, Edge, or Android Browser.");
                return;
            }
        }

        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    },

    startRecording: function() {
        if (!this.recognition) return;
        const targetLocale = this.localeMap[currentLanguage] || "en-IN";
        this.recognition.lang = targetLocale;
        try {
            this.recognition.start();
        } catch (e) {
            console.warn("Recognition already started or error:", e);
        }
    },

    stopRecording: function() {
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
        this.isRecording = false;
        this.updateVoiceUI(false);
    },

    updateVoiceUI: function(active) {
        const btn = document.getElementById("voiceRecordBtn");
        const statusBox = document.getElementById("voiceStatusIndicator");
        const statusText = document.getElementById("voiceStatusText");

        if (btn) {
            if (active) {
                btn.classList.add("recording");
                btn.innerHTML = `<i class="fa-solid fa-stop text-danger"></i> <span data-i18n="stopListening">${t("stopListening")}</span>`;
            } else {
                btn.classList.remove("recording");
                btn.innerHTML = `<i class="fa-solid fa-microphone text-primary"></i> <span data-i18n="speakBtn">${t("speakBtn")}</span>`;
            }
        }

        if (statusBox) {
            if (active) {
                statusBox.classList.remove("d-none");
                if (statusText) statusText.innerText = `${t("listening")} (${this.localeMap[currentLanguage] || "en-IN"})...`;
            } else {
                setTimeout(() => {
                    statusBox.classList.add("d-none");
                }, 2000);
            }
        }
    },

    speak: function(text) {
        if (!this.synth) {
            console.warn("SpeechSynthesis not supported.");
            return;
        }

        this.stopSpeaking();

        const utterance = new SpeechSynthesisUtterance(text);
        const targetLocale = this.localeMap[currentLanguage] || "en-IN";
        utterance.lang = targetLocale;
        utterance.rate = 0.95; // Slightly slower for clarity in rural health advice
        utterance.pitch = 1.0;

        // Try selecting a matching voice
        const voices = this.synth.getVoices();
        const matchingVoice = voices.find(v => v.lang.startsWith(currentLanguage) || v.lang === targetLocale);
        if (matchingVoice) {
            utterance.voice = matchingVoice;
        }

        const speakBtn = document.getElementById("listenAudioBtn");
        utterance.onstart = () => {
            if (speakBtn) {
                speakBtn.innerHTML = `<i class="fa-solid fa-volume-xmark"></i> ${t("stopAudio")}`;
                speakBtn.classList.add("btn-danger");
                speakBtn.classList.remove("btn-outline-primary");
            }
        };

        utterance.onend = () => {
            if (speakBtn) {
                speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> ${t("listenResult")}`;
                speakBtn.classList.remove("btn-danger");
                speakBtn.classList.add("btn-outline-primary");
            }
            this.activeUtterance = null;
        };

        utterance.onerror = () => {
            if (speakBtn) {
                speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> ${t("listenResult")}`;
                speakBtn.classList.remove("btn-danger");
                speakBtn.classList.add("btn-outline-primary");
            }
            this.activeUtterance = null;
        };

        this.activeUtterance = utterance;
        this.synth.speak(utterance);
    },

    stopSpeaking: function() {
        if (this.synth && this.synth.speaking) {
            this.synth.cancel();
        }
        const speakBtn = document.getElementById("listenAudioBtn");
        if (speakBtn) {
            speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> ${t("listenResult")}`;
            speakBtn.classList.remove("btn-danger");
            speakBtn.classList.add("btn-outline-primary");
        }
        this.activeUtterance = null;
    },

    toggleSpeech: function(text) {
        if (this.synth && this.synth.speaking) {
            this.stopSpeaking();
        } else {
            this.speak(text);
        }
    }
};

window.addEventListener("DOMContentLoaded", () => {
    VoiceAssistant.init();
});
