import { useState } from 'react';


export const Header = () => {
      const [, setActivePage] = useState('chat');



    return (
        <div className="bg-gray-50 min-h-screen flex flex-col">
            {/* Header */}
            <header className="bg-white shadow-sm py-4 px-6">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center">
                            <i data-feather="mic" className="text-white"></i>
                        </div>
                        <h1 className="text-xl font-bold text-gray-800">SonicMind</h1>
                    </div>
                    <div className="flex items-center space-x-4">
                        <button onClick={() => setActivePage('settings')} className="p-2 rounded-full hover:bg-gray-100 transition">
                            <i data-feather="settings" className="text-gray-600"></i>
                        </button>
                        <button className="p-2 rounded-full hover:bg-gray-100 transition">
                            <i data-feather="user" className="text-gray-600"></i>
                        </button>
                    </div>
                </div>
            </header>
        </div>
    )
}   