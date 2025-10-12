import { Dispatch, SetStateAction } from 'react';
import Icon from '../Icon';

interface ChatFooterProps {
  isTranscriptVisible: boolean;
  setIsTranscriptVisible: Dispatch<SetStateAction<boolean>>;
  inputMessage: string;
  setInputMessage: (message: string) => void;
  handleSendMessage: () => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  isSending: boolean;
  isRecording: boolean;
  toggleRecording: () => void;
}

const ChatFooter = ({
  isTranscriptVisible,
  setIsTranscriptVisible,
  inputMessage,
  setInputMessage,
  handleSendMessage,
  handleKeyDown,
  isSending,
  isRecording,
  toggleRecording,
}: ChatFooterProps) => {
  return (
    <footer className="w-full p-4 bg-gray-50">
      <div className="max-w-4xl mx-auto flex items-center justify-center space-x-2 md:space-x-4">
        <button onClick={() => setIsTranscriptVisible(!isTranscriptVisible)} className="p-2 md:p-3 rounded-full text-gray-500 bg-gray-200 hover:bg-gray-300 transition" title={isTranscriptVisible ? "Hide Transcript" : "Show Transcript"}>
          <Icon name={isTranscriptVisible ? "mic" : "message-square"} className="w-5 h-5 md:w-6 md:h-6" />
        </button>
        <div className="relative flex-1 max-w-xl">
          <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyDown={handleKeyDown} className="w-full px-4 py-2 md:px-5 md:py-3 bg-white border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-[#175289] focus:border-transparent text-gray-800" placeholder="Or type a message..." />
          <button onClick={handleSendMessage} disabled={isSending || !inputMessage.trim()} className="absolute right-1.5 top-1/2 transform -translate-y-1/2 p-1.5 md:p-2 rounded-full bg-[#175289] hover:bg-[#0e2a47] transition disabled:bg-gray-400 disabled:cursor-not-allowed">
            {isSending ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Icon name="send" className="text-white w-4 h-4 md:w-5 md:h-5" />
            )}
          </button>
        </div>
        <button onClick={toggleRecording} className={`p-4 md:p-5 rounded-full text-white transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-50 ${isRecording ? 'bg-[#e7232e] hover:bg-opacity-90 scale-110 animate-pulse focus:ring-[#e7232e]' : 'bg-[#175289] hover:bg-[#0e2a47] focus:ring-[#175289]'}`}>
          {isRecording ? <Icon name="square" className="w-6 h-6 md:w-8 md:h-8" /> : <Icon name="mic" className="w-6 h-6 md:w-8 md:h-8" />}
        </button>
      </div>
    </footer>
  );
};

export default ChatFooter;