import feather from 'feather-icons';
import { useEffect } from 'react';

interface ChatHeaderProps {
  onClearHistory: () => void;
  onGoToSettings: () => void;
}

const ChatHeader = ({ onClearHistory, onGoToSettings }: ChatHeaderProps) => {
  useEffect(() => {
    feather.replace();
  });

  return (
    <header className="absolute top-0 left-0 right-0 z-10">
      <div className="py-4 px-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-end space-x-2">
          <button onClick={onClearHistory} className="p-2 rounded-full bg-black/5 hover:bg-black/10 transition" title="Clear History">
            <i data-feather="trash-2" className="text-gray-600 w-5 h-5"></i>
          </button>
          <button onClick={onGoToSettings} className="p-2 rounded-full bg-black/5 hover:bg-black/10 transition" title="Settings">
            <i data-feather="settings" className="text-gray-600 w-5 h-5"></i>
          </button>
        </div>
      </div>
    </header>
  );
};

export default ChatHeader;