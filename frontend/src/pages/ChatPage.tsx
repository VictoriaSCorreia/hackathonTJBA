import { useState, useRef, useEffect } from 'react';
// Todas as chamadas devem passar por `api` (com proxy do Vite)
import feather from 'feather-icons';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import Modal from '../Components/Modal';
import api, { ensureGuestSession } from '../api';

interface Message {
  text: string;
  sender: 'user' | 'ai';
}

const INITIAL_MESSAGE: Message = {
  text: "Hi assistant. You can talk to me by typing or using the microphone button below. How can I help you today?",
  sender: 'ai'
};

function ChatPage({ setActivePage }) {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const savedMessages = localStorage.getItem('chatHistory');
      // If there are saved messages, parse and return them, otherwise return the initial message.
      return savedMessages ? JSON.parse(savedMessages) : [INITIAL_MESSAGE];
    } catch (error) {
      console.error("Failed to load messages from local storage", error);
      return [INITIAL_MESSAGE];
    }
  });
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isClearHistoryModalOpen, setClearHistoryModalOpen] = useState(false);
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(null);
  const [isTranscriptVisible, setIsTranscriptVisible] = useState(false);
  const [isTranscriptionActive, setIsTranscriptionActive] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [waitingClarification, setWaitingClarification] = useState(false);
  const transcriptionIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const chatContainerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
    feather.replace();
  }, [messages]);

  // Effect to save messages to local storage whenever they change.
  useEffect(() => {
    try {
      localStorage.setItem('chatHistory', JSON.stringify(messages));
    } catch (error) {
      console.error("Failed to save messages to local storage", error);
    }
  }, [messages]);

  // Ensure guest session exists so backend accepts requests
  useEffect(() => {
    void ensureGuestSession();
  }, []);

  useEffect(() => {
    if (isTranscriptionActive) {
      // Simulate receiving transcribed text every 3 seconds
      transcriptionIntervalRef.current = setInterval(() => {
        const transcribedText = [
          "This is a simulated transcribed message.",
          "The system is now actively listening and transcribing.",
          "Here is another piece of transcribed audio.",
          "Okay, I've got that down."
        ][Math.floor(Math.random() * 4)];

        const newMessage = { text: transcribedText, sender: 'user' as const };
        setMessages(prev => [...prev, newMessage]);
      }, 3000);
    } else {
      if (transcriptionIntervalRef.current) {
        clearInterval(transcriptionIntervalRef.current);
      }
    }
    return () => { if (transcriptionIntervalRef.current) clearInterval(transcriptionIntervalRef.current) };
  }, [isTranscriptionActive]);

  const playAudioResponse = async (text: string) => {
    // Recurso opcional: habilite via VITE_TTS_ENABLED=true
    if (import.meta.env.VITE_TTS_ENABLED !== 'true') return;
    try {
      const response = await api.post('/text-to-speech', { text }, { responseType: 'blob' });
      if (response.data) {
        const audioUrl = URL.createObjectURL(response.data as unknown as Blob);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    } catch (error) {
      console.error('Error fetching TTS audio:', error);
    }
  };

  // Helper: extract Q1/Q2/Q3 from a <clarify> block
  const extractClarifyQuestions = (text: string): string[] | null => {
    if (!text || !text.includes('<clarify')) return null;
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const qs: string[] = [];
    for (const ln of lines) {
      const m = ln.match(/^Q[123]\s*:\s*(.+)$/i);
      if (m) qs.push(m[1].trim());
    }
    if (qs.length) return qs.slice(0, 3);
    return null;
  };

  const handleSendMessage = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed) return;

    const userMessage: Message = { text: trimmed, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsAiTyping(true);

    try {
      // Ensure we have a guest session and a conversation
      await ensureGuestSession();
      let convId = conversationId;
      if (!convId) {
        const convResp = await api.post('/conversations', {});
        convId = convResp?.data?.id;
        setConversationId(convId);
      }

      // Send user message to conversation
      const msgResp = await api.post(
        `/conversations/${convId}/messages`,
        {
          role: 'user',
          content: trimmed,
        },
        {
          // Garante timeout estendido especificamente para o passo de análise final
          timeout: 180_000,
        }
      );

      const assistantText: string | undefined = msgResp?.data?.content;
      if (assistantText) {
        // Detect two-step clarify flow
        const qs = extractClarifyQuestions(assistantText);
        if (qs && qs.length) {
          const display = `Precisamos de alguns detalhes:\n\n1) ${qs[0]}\n2) ${qs[1]}\n3) ${qs[2]}\n\nResponda acima para continuar.`;
          setMessages(prev => [...prev, { text: display, sender: 'ai' }]);
          // Auto-open transcript to make the questions visible
          setIsTranscriptVisible(true);
          setWaitingClarification(true);
        } else {
          setMessages(prev => [...prev, { text: assistantText, sender: 'ai' }]);
          // Auto-open transcript to show the assistant reply
          setIsTranscriptVisible(true);
          setWaitingClarification(false);
          await playAudioResponse(assistantText);
        }
      }
    } catch (error) {
      console.error('Error sending message to backend:', error);
      const errorMessage: Message = { text: "Sorry, I'm having trouble connecting. Please try again later.", sender: 'ai' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputMessage);
    }
  };

  const handleSendAudio = async (audioBlob: Blob) => {
    setIsAiTyping(true);

    try {
      if (import.meta.env.VITE_STS_ENABLED !== 'true') {
        const errorMessage: Message = { text: "Voice input is disabled.", sender: 'ai' };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await api.post('/speech-to-speech', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'json',
      });

      if (response.data && response.data.audioUrl && response.data.userTranscript && response.data.aiTranscript) {
        // Add the actual transcripts to the chat
        const userMessage: Message = { text: response.data.userTranscript, sender: 'user' };
        const aiMessage: Message = { text: response.data.aiTranscript, sender: 'ai' };
        setMessages(prev => [...prev, userMessage, aiMessage]);

        // Play the audio
        const audioUrl = response.data.audioUrl.startsWith('http')
          ? response.data.audioUrl
          : response.data.audioUrl.startsWith('/')
            ? response.data.audioUrl
            : `/api${response.data.audioUrl}`; // melhor esforço
        const audio = new Audio(audioUrl);
        audio.play();
      } else {
        // Handle cases where the backend might not return all expected data
        const errorMessage: Message = { text: "Sorry, there was an issue with the response.", sender: 'ai' };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending audio to backend:', error);
      const errorMessage: Message = { text: "Sorry, I couldn't process the audio. Please try again.", sender: 'ai' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // We set isAiTyping to false, but a true "is playing" state would be better
      setIsAiTyping(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];

        mediaRecorderRef.current.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          handleSendAudio(audioBlob);
          stream.getTracks().forEach(track => track.stop()); // Stop the microphone track
        };

        mediaRecorderRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Failed to get microphone access:", err);
        alert("Microphone access is required for voice input. Please allow access and try again.");
      }
    }
  };

  const handleClearHistory = () => {
    setClearHistoryModalOpen(true);
  };

  const handleCopyMessage = async (text: string, index: number) => {
    if (!navigator.clipboard) {
      // Fallback for browsers that don't support the Clipboard API
      alert("Sorry, your browser does not support copying to clipboard.");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageIndex(index);
      setTimeout(() => {
        setCopiedMessageIndex(null);
      }, 2000); // Reset the icon after 2 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <>
      <Modal
        isOpen={isClearHistoryModalOpen}
        onClose={() => setClearHistoryModalOpen(false)} // This was missing
        onConfirm={() => { 
          setMessages([INITIAL_MESSAGE]); 
          setConversationId(null);
          setWaitingClarification(false);
          setClearHistoryModalOpen(false); 
        }} // Reset chat + conversation state
        title="Clear Chat History"
        confirmText="Delete"
      >
        <p>Are you sure you want to delete the entire chat history? This action cannot be undone.</p>
      </Modal>
      <div className="bg-gray-900 text-white h-screen flex flex-col">
        {/* Header */}
        <header className="absolute top-0 left-0 right-0 z-10">
          <div className="py-4 px-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-end">
              <button onClick={() => setActivePage('settings')} className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition">
                <i data-feather="settings" className="text-white w-5 h-5"></i>
              </button>
            </div>
          </div>
        </header>

        {/* Main Call Area */}
        <main className="flex-1 flex flex-col items-center justify-center text-center p-4">
          <div className="relative w-32 h-32 md:w-40 md:h-40">
            <div className={`absolute inset-0 rounded-full bg-indigo-500 transition-transform transform ${isRecording ? 'scale-110' : 'scale-100'}`}></div>
            <div className={`absolute inset-0 rounded-full bg-indigo-400 animate-pulse-slow ${isRecording ? 'scale-125' : 'scale-100'} transition-transform`}></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-indigo-600 flex items-center justify-center shadow-lg">
                <i data-feather="mic" className="text-white w-12 h-12 md:w-16 md:h-16"></i>
              </div>
            </div>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold mt-6 md:mt-8">judi</h1>
          <p className="text-gray-400 mt-2 text-sm md:text-base">{isRecording ? "Listening..." : "Tap the mic to talk"}</p>
        </main>

        {/* Footer / Input Area */}
        <footer className="w-full p-4 bg-gray-900">
          <div className="max-w-4xl mx-auto flex items-center justify-center space-x-2 md:space-x-4">
            <button
              onClick={() => setIsTranscriptVisible(prev => !prev)}
              className="p-2 md:p-3 rounded-full text-white bg-gray-700 hover:bg-gray-600 transition"
              title={isTranscriptVisible ? "Hide Transcript" : "Show Transcript"}
            >
              <i data-feather="message-square" className="w-5 h-5 md:w-6 md:h-6"></i>
            </button>
            <div className="relative flex-1 max-w-xl">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full px-4 py-2 md:px-5 md:py-3 bg-gray-800 border border-gray-700 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white"
                placeholder="Or type a message..."
              />
              <button
                onClick={() => handleSendMessage(inputMessage)}
                className="absolute right-1.5 top-1/2 transform -translate-y-1/2 p-1.5 md:p-2 rounded-full bg-indigo-500 hover:bg-indigo-600 transition"
              >
                <i data-feather="send" className="text-white w-4 h-4 md:w-5 md:h-5"></i>
              </button>
            </div>
            <button
              onClick={toggleRecording}
              className={`p-4 md:p-5 rounded-full text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${isRecording ? 'bg-red-500 hover:bg-red-600 scale-110' : 'bg-indigo-500 hover:bg-indigo-600'}`}
            >
              {isRecording ? <i data-feather="square" className="w-6 h-6 md:w-8 md:h-8"></i> : <i data-feather="mic" className="w-6 h-6 md:w-8 md:h-8"></i>}
            </button>
          </div>
        </footer>

        {/* Transcript / Chat History (side drawer) */}
        {isTranscriptVisible && (
          <div className="absolute top-0 right-0 bottom-0 z-20">
            <div
              className="ml-auto h-full w-full sm:w-5/6 md:w-[420px] lg:w-[480px] bg-gray-800/90 backdrop-blur-md transition-transform duration-300 ease-in-out shadow-xl rounded-none md:rounded-l-2xl flex flex-col"
              style={{ transform: `translateX(${isTranscriptVisible ? '0%' : '100%'})` }}
            >
              <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
                <span className="text-sm text-gray-300">Transcript</span>
                <button onClick={() => setIsTranscriptVisible(false)} className="p-1.5 rounded hover:bg-white/10">
                  <i data-feather="x" className="w-4 h-4"></i>
                </button>
              </div>
              <div ref={chatContainerRef} className="flex-1 overflow-y-auto space-y-4 p-4 pr-2">
                {messages.map((message, index) => (
                  <div key={index} className={`group flex items-end gap-2 animate-fade-in-up ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {message.sender === 'ai' && (
                      <button
                        onClick={() => handleCopyMessage(message.text, index)}
                        className="p-1 rounded-full text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy message"
                      >
                        {copiedMessageIndex === index ? <i data-feather="check" className="w-3.5 h-3.5 text-green-500" /> : <i data-feather="copy" className="w-3.5 h-3.5" />}
                      </button>
                    )}
                    <div className={`max-w-[80%] rounded-xl p-3 ${message.sender === 'user' ? 'bg-indigo-500 text-white' : 'bg-gray-700 text-gray-200'}`}>
                      {message.sender === 'ai' ? (
                        <div
                          className="prose prose-sm prose-invert max-w-none"
                          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(message.text) as string) }}
                        />
                      ) : (
                        <p>{message.text}</p>
                      )}
                    </div>
                    {message.sender === 'user' && (
                      <button
                        onClick={() => handleCopyMessage(message.text, index)}
                        className="p-1 rounded-full text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy message"
                      >
                        {copiedMessageIndex === index ? <i data-feather="check" className="w-3.5 h-3.5 text-green-500" /> : <i data-feather="copy" className="w-3.5 h-3.5" />}
                      </button>
                    )}
                  </div>
                ))}
                {isAiTyping && (
                  <div className="flex items-end gap-2 animate-fade-in-up justify-start">
                    <div className="max-w-[80%] rounded-xl p-3 bg-gray-700 text-gray-200">
                      <div className="flex items-center space-x-1">
                        <span className="typing-dot animate-pulse-fast"></span>
                        <span className="typing-dot animate-pulse-fast animation-delay-200"></span>
                        <span className="typing-dot animate-pulse-fast animation-delay-400"></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default ChatPage;
