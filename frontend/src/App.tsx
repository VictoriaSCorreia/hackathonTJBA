import { useEffect, useState } from 'react';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import { ensureGuestSession } from './api';

function App() {
  const [activePage, setActivePage] = useState('chat');

  // Inicializa sessão de convidado na primeira carga do app
  useEffect(() => {
    ensureGuestSession();
  }, []);

  return (
    <>
      {activePage === 'chat' && <ChatPage setActivePage={setActivePage} />}
      {activePage === 'settings' && <SettingsPage setActivePage={setActivePage} />}
    </>
  );
};

export default App;
