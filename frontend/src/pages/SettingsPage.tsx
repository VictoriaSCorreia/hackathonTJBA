import { useState, useEffect } from 'react';
import feather from 'feather-icons';
import Modal from '../Components/Modal';

function SettingsPage({ setActivePage }) {
  const [voiceSpeed, setVoiceSpeed] = useState(1);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);


  useEffect(() => {
    feather.replace();
  }, []);

  return (
    <div className="bg-gray-900 text-white min-h-screen">
      {/* Header */}
      <header className="bg-gray-800/80 backdrop-blur-md py-4 px-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button onClick={() => setActivePage('chat')} className="flex items-center space-x-2">
              <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center">
                <i data-feather="arrow-left" className="text-white"></i>
              </div>
              <h1 className="text-xl font-bold text-white">Settings</h1>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-8 px-6">
        <div className="bg-gray-800 rounded-xl shadow-lg p-6 space-y-8">
          <h2 className="text-2xl font-bold text-white">Settings</h2>

          {/* Voice Preferences */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-300">Voice Preferences</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Voice Speed</label>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setVoiceSpeed(0.8)}
                    className={`flex-1 py-2 px-4 rounded-lg border ${voiceSpeed === 0.8 ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-gray-700 text-gray-300 border-gray-600'} hover:bg-gray-600 transition`}
                  >
                    Slow
                  </button>
                  <button
                    onClick={() => setVoiceSpeed(1)}
                    className={`flex-1 py-2 px-4 rounded-lg border ${voiceSpeed === 1 ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-gray-700 text-gray-300 border-gray-600'} hover:bg-gray-600 transition`}
                  >
                    Normal
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-4">
            <button className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition mb-4">
              Save Settings
            </button>
            <button
              onClick={() => setDeleteModalOpen(true)}
              className="w-full py-3 px-4 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg transition"
            >
              Delete Account
            </button>
          </div>
        </div>
      </main>

      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={() => {
          console.log("Account deletion confirmed.");
          setDeleteModalOpen(false);
        }}
        title="Delete Account"
        confirmText="Delete"
      >
        <p>Are you sure you want to delete your account? This action is permanent and cannot be undone.</p>
      </Modal>
    </div>
  );
}

export default SettingsPage;