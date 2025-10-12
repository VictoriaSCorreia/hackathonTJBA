import { useState, Dispatch, SetStateAction } from 'react';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import LandingPage from './pages/LandingPage';
import ErrorBoundary from './Components/ErrorBoundary';

export interface SetActivePageProps {
  setActivePage: Dispatch<SetStateAction<string>>;
}

function App() {
  
const [activePage, setActivePage] = useState<string>('landing');

  return (
    <>
      <ErrorBoundary>
        {activePage === 'landing' && <LandingPage setActivePage={setActivePage} />}
      </ErrorBoundary>
      <ErrorBoundary>
        {activePage === 'chat' && <ChatPage setActivePage={setActivePage} />}
      </ErrorBoundary>
      <ErrorBoundary>
        {activePage === 'settings' && <SettingsPage setActivePage={setActivePage} />}
      </ErrorBoundary>
    </>
  );
};

export default App;