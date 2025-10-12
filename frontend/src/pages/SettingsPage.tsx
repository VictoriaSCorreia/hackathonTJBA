import { useState, useEffect } from 'react';
import feather from 'feather-icons';
import { SetActivePageProps } from '../App';


function SettingsPage({ setActivePage }: SetActivePageProps) {
  const [voiceSpeed, setVoiceSpeed] = useState(() => {
    try {
      const savedSettings = localStorage.getItem('userSettings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        return settings.voiceSpeed || 1;
      }
    } catch (error) {
      console.error("Failed to load settings from local storage", error);
    }
    return 1; // Default value
  });
  const [saveStatus, setSaveStatus] = useState('');

  useEffect(() => {
    feather.replace();
  }, []);

  const handleSaveSettings = () => {
    const settings = { voiceSpeed };
    localStorage.setItem('userSettings', JSON.stringify(settings));
    setSaveStatus('Saved!');
    // Reset the status message after a couple of seconds
    setTimeout(() => setSaveStatus(''), 2000);
  };

  return (
    <div className="bg-gray-50 text-gray-800 min-h-screen">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md py-4 px-6 shadow-sm">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button onClick={() => setActivePage('chat')} className="flex items-center space-x-2">
              <div className="w-10 h-10 rounded-full bg-[#175289] flex items-center justify-center">
                <i data-feather="arrow-left" className="text-white"></i>
              </div>
              <h1 className="text-xl font-bold text-gray-800">Settings</h1>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-8 px-6">
        <div className="bg-white rounded-xl shadow-lg p-6 space-y-8">
          <h2 className="text-2xl font-bold text-gray-800">Settings</h2>

          {/* Voice Preferences */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-300">Voice Preferences</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Voice Speed</label>
                <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
                  <button
                    onClick={() => setVoiceSpeed(0.8)}
                    className={`flex-1 py-2 px-4 rounded-md transition-colors ${voiceSpeed === 0.8 ? 'bg-white text-[#175289] shadow' : 'text-gray-600 hover:bg-gray-200'}`}
                  >
                    Slow
                  </button>
                  <button
                    onClick={() => setVoiceSpeed(1)}
                    className={`flex-1 py-2 px-4 rounded-md transition-colors ${voiceSpeed === 1 ? 'bg-white text-[#175289] shadow' : 'text-gray-600 hover:bg-gray-200'}`}
                  >
                    Normal
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-4">
            <button
              onClick={handleSaveSettings}
              className="w-full py-3 px-4 bg-[#175289] hover:bg-[#0e2a47] text-white font-medium rounded-lg transition mb-4"
            >
              {saveStatus || 'Save Settings'}
            </button>
          </div>
        </div>
      </main>

    </div>
  );
}

export default SettingsPage;