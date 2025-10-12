import { useEffect } from 'react';
import feather from 'feather-icons';
import logo from '../assets/logo.png';
import logotipo from '../assets/logotipo.png';
import FeatureCard from '../Components/FeatureCard';
import { SetActivePageProps } from '../App';


function LandingPage({ setActivePage }: SetActivePageProps) {
    useEffect(() => {
        // This needs to be called anytime new icons are rendered.
        feather.replace();
    }, []);

    return (
        <div className="bg-white text-gray-800 min-h-screen flex flex-col font-sans">
            <header className="py-2 px-6">
                <div className="max-w-6xl mx-auto flex justify-between items-center">
                    <div className="flex items-center gap-0">
                        <img src={logo} className='h-35 w-35' alt="fala justa logo" />
                        <img src={logotipo} className='h-35 w-35' alt="" />
                    </div>
                </div>
            </header>

            <main className="flex-1 flex items-center justify-center px-4 py-9 md:py-1">
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                    <div className="text-center md:text-left">
                        <h2 className="text-3xl md:text-5xl lg:text-4xl font-extrabold leading-tight mb-4 animate-fade-in-up duration-1000">
                            Um chatbot que escuta para educar e educa para transformar.
                        </h2>
                        <div className="text-lg md:text-xl text-gray-600 mb-10 animate-fade-in-up animation-delay-300 space-y-4">
                            <p>
                                Sou um espaço de escuta, aprendizado e diálogo. Aqui, cada conversa é uma oportunidade de reconhecer atitudes, refletir sobre comportamentos e fortalecer a educação antirracista.
                            </p>
                        </div>
                        <button
                            onClick={() => setActivePage('chat')}
                            className="bg-[#175289] hover:bg-[#0e2a47] text-white font-bold py-4 px-8 rounded-lg text-lg transition-transform transform hover:scale-105 animate-fade-in-up animation-delay-500"
                        >
                            Começar Agora
                        </button>
                    </div>

                    <div className="hidden md:flex justify-center items-center animate-fade-in-up animation-delay-300">
                        <div className="w-full max-w-sm mx-auto">
                            <div className="bg-white rounded-3xl border-4 border-gray-200 shadow-2xl p-4 transform rotate-3">
                                <div className="h-[450px] flex flex-col space-y-4 overflow-hidden">
                                    <div className="flex justify-between items-center px-2">
                                        <span className="text-sm font-bold text-gray-800">Judi</span>
                                        <i data-feather="settings" className="w-4 h-4 text-gray-400"></i>
                                    </div>
                                    <div className="flex-1 space-y-3 p-2">
                                        <div className="w-3/4 bg-gray-200 rounded-lg p-2 text-xs text-gray-700">Olá! Como posso ajudar hoje?</div>
                                        <div className="flex justify-end">
                                            <div className="w-2/3 bg-[#175289] rounded-lg p-2 text-xs text-white">Eu gostaria de falar sobre uma situação...</div>
                                        </div>
                                        <div className="w-4/5 bg-gray-200 rounded-lg p-2 text-xs text-gray-700">Claro, estou aqui para ouvir. Pode me contar o que aconteceu.</div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <div className="flex-1 h-10 bg-gray-400 rounded-full"></div>
                                        <div className="w-10 h-10 bg-[#175289] rounded-full"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <section className="py-20 bg-white text-gray-700">
                <div className="max-w-5xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
                    <FeatureCard
                        icon="mic"
                        title="Escuta Ativa"
                        description="Converse por voz de forma natural e sinta-se em um espaço seguro para dialogar."
                        delay="200"
                    />
                    <FeatureCard
                        icon="message-circle"
                        title="Diálogo Construtivo"
                        description="Receba respostas que promovem a reflexão e o entendimento sobre o racismo."
                        delay="400"
                    />
                    <FeatureCard
                        icon="book-open"
                        title="Aprendizado Contínuo"
                        description="Acesse informações e caminhos para combater o racismo com empatia e respeito."
                        delay="600"
                    />
                </div>
            </section>

            {/* Footer */}
            <footer className="py-6 px-6 bg-white">
                <div className="max-w-6xl mx-auto text-center text-gray-500">
                    <p>&copy; {new Date().getFullYear()} Hádrons Team. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

export default LandingPage;