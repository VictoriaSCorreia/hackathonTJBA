
import { useState, useRef, useEffect } from 'react';
import feather from 'feather-icons';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import ChatHeader from '../Components/chat/ChatHeader.tsx';
import ChatFooter from '../Components/chat/ChatFooter.tsx';

import Modal from '../Components/Modal';
import api, { ensureGuestSession } from '../api.ts';
import { SetActivePageProps } from '../App';

export interface Message {
  text: string;
  sender: 'user' | 'ai';
}

const INITIAL_MESSAGE: Message = {
  text: "Olá! Sou a Judi, sua assistente virtual dedicada a promover a educação antirracista. Estou aqui para ouvir suas experiências, oferecer suporte e compartilhar informações que possam ajudar na construção de um ambiente mais inclusivo e respeitoso. Sinta-se à vontade para conversar comigo sobre qualquer situação ou dúvida que você tenha. Juntos, podemos aprender e crescer em direção a uma sociedade mais justa e igualitária. Como posso ajudar você hoje?",
  sender: 'ai'
};

function ChatPage({ setActivePage }: SetActivePageProps) {
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
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [, setWaitingClarification] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null); // This was missing
  const audioChunksRef = useRef<Blob[]>([]); // This was missing
  const chatContainerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  // Effect to save messages to local storage whenever they change.
  useEffect(() => {
    try {
      localStorage.setItem('chatHistory', JSON.stringify(messages));
    } catch (error) {
      console.error("Falha em persistir mensagens na memória", error);
    }
  }, [messages]);

  // Ensure guest session exists so backend accepts requests
  useEffect(() => {
    void ensureGuestSession();
    feather.replace();
  }, []);

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
      await ensureGuestSession();
      let convId = conversationId;
      if (!convId) {
        const convResp = await api.post('/conversations', {});
        convId = convResp?.data?.id;
        setConversationId(convId);
      }

      const msgResp = await api.post(`/conversations/${convId}/messages`, {
        role: 'user',
        content: trimmed,
      });

      const assistantText: string | undefined = msgResp?.data?.content;
      if (assistantText) {
        const qs = extractClarifyQuestions(assistantText);
        if (qs && qs.length) {
          const display = `Precisamos de alguns detalhes:\n\n1) ${qs[0]}\n2) ${qs[1]}\n3) ${qs[2]}\n\nResponda acima para continuar.`;
          setMessages(prev => [...prev, { text: display, sender: 'ai' }]);
          // Auto-open transcript to make the questions visible
          setIsTranscriptVisible(true);
          setWaitingClarification(true);
        } else {
          setMessages(prev => [...prev, { text: assistantText, sender: 'ai' }]);
          setIsTranscriptVisible(true);
          setWaitingClarification(false);
          await playAudioResponse(assistantText);
        }
      }
    } catch (error) {
      console.error('Error sending message to backend:', error);
      const errorMessage: Message = { text: "Estaoms com problemas ao conectar com o servidor. Por favor, tente novamente", sender: 'ai' };
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
        const errorMessage: Message = { text: "Não conseguimos acessar seu microfone. Por favor, tente novamente", sender: 'ai' };
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

        const audioUrl = response.data.audioUrl.startsWith('http')
          ? response.data.audioUrl
          : response.data.audioUrl.startsWith('/')
            ? response.data.audioUrl
            : `/api${response.data.audioUrl}`; // melhor esforço
        const audio = new Audio(audioUrl);
        audio.play();
      } else {
        const errorMessage: Message = { text: "Sorry, there was an issue with the response.", sender: 'ai' };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending audio to backend:', error);
      const errorMessage: Message = { text: "Sorry, I couldn't process the audio. Please try again.", sender: 'ai' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
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
        alert("Precisamos do acesso ao seu microfone.");
      }
    }
  };

  const handleClearHistory = () => {
    setClearHistoryModalOpen(true);
  };

  const handleCopyMessage = async (text: string, index: number) => {
    if (!navigator.clipboard) {
      alert("Não conseguimos copiar o texto para a área de transferência.");
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
        onClose={() => setClearHistoryModalOpen(false)}
        onConfirm={() => {
          setMessages([INITIAL_MESSAGE]);
          setConversationId(null);
          setWaitingClarification(false);
          setClearHistoryModalOpen(false);
        }} // Reset chat + conversation state
        title="Apagar histórico do chat"
        confirmText="Deletar"
      >
        <p>Você tem certeza que deseja apagar o histórico do chat? Essa ação é irreversível.</p>
      </Modal>
      <div className="bg-gray-50 text-gray-800 h-screen flex flex-col">
        <ChatHeader
          onClearHistory={handleClearHistory} 
          onGoToSettings={() => setActivePage('settings')} 
        />

        {!isTranscriptVisible ? (
          <main className="flex-1 flex flex-col items-center justify-center text-center p-4">
            <button onClick={toggleRecording} className="relative w-32 h-32 md:w-40 md:h-40 focus:outline-none focus:ring-4 focus:ring-[#175289]/50 rounded-full transition-transform transform hover:scale-105 active:scale-95">
              <div className="relative w-full h-full">
                <div className={`absolute inset-0 rounded-full transition-transform transform ${isRecording ? 'bg-[#e7232e]/20 scale-110 animate-pulse-slow' : 'bg-[#175289]/20 scale-100'}`}></div>
                <div className={`absolute inset-0 rounded-full transition-transform duration-300 ${isRecording ? 'bg-[#e7232e]/10 animate-pulse-slow scale-125' : 'bg-[#175289]/10 scale-100'}`}></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className={`w-24 h-24 md:w-32 md:h-32 rounded-full flex items-center justify-center shadow-lg transition-colors ${isRecording ? 'bg-[#e7232e]' : 'bg-[#175289]'}`}>
                    <i data-feather="mic" className={`text-white w-12 h-12 md:w-16 md:h-16 transition-transform duration-300 ${isRecording ? 'scale-110' : 'scale-100'}`}></i>
                  </div>
                </div>
              </div>
            </button>
            <h1 className="text-2xl md:text-3xl font-bold mt-6 md:mt-8">judi</h1>
            <p className={`mt-2 text-sm md:text-base transition-colors ${isRecording ? 'text-[#e7232e] font-medium' : 'text-gray-500'}`}>{isRecording ? "Listening..." : "Tap mic to start"}</p>
          </main>
        ) : (
          <main ref={chatContainerRef} className="flex-1 overflow-y-auto space-y-4 p-4 pt-20 pb-4">
            {messages.map((message, index) => (
              <div key={index} className={`group flex items-end gap-2 animate-fade-in-up ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                {message.sender === 'ai' && (
                  <button onClick={() => handleCopyMessage(message.text, index)} className="p-1 rounded-full text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" title="Copy message">
                    {copiedMessageIndex === index ? <i data-feather="check" className="w-3.5 h-3.5 text-green-500" /> : <i data-feather="copy" className="w-3.5 h-3.5" />}
                  </button>
                )}
                <div className={`max-w-[80%] rounded-xl p-3 ${message.sender === 'user' ? 'bg-[#175289] text-white' : 'bg-gray-100 text-gray-800'}`}>
                  {message.sender === 'ai' ? <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(message.text) as string) }} /> : <p>{message.text}</p>}
                </div>
                {message.sender === 'user' && (
                  <button onClick={() => handleCopyMessage(message.text, index)} className="p-1 rounded-full text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" title="Copy message">
                    {copiedMessageIndex === index ? <i data-feather="check" className="w-3.5 h-3.5 text-green-500" /> : <i data-feather="copy" className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
            ))}
            {isAiTyping && <div className="flex items-end gap-2 animate-fade-in-up justify-start"><div className="max-w-[80%] rounded-xl p-3 bg-gray-100 text-gray-800"><div className="flex items-center space-x-1"><span className="typing-dot animate-pulse-fast"></span><span className="typing-dot animate-pulse-fast animation-delay-200"></span><span className="typing-dot animate-pulse-fast animation-delay-400"></span></div></div></div>}
          </main>
        )}

        <ChatFooter
          isTranscriptVisible={isTranscriptVisible}
          setIsTranscriptVisible={setIsTranscriptVisible}
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          handleSendMessage={handleSendMessage}
          handleKeyDown={handleKeyDown}
          isSending={isAiTyping} 
          isRecording={isRecording}
          toggleRecording={toggleRecording}
        />
      </div>
    </>
  );
}

export default ChatPage;