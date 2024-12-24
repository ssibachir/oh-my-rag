'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Source, ChatResponse } from '@/types/chat';
import LoginForm from '../Auth/LoginForm';
import RegisterForm from '../Auth/RegisterForm';

interface ChatMessage extends Message {
    sources?: Source[];
}

export default function ChatContainer() {
    // États pour la gestion des messages et du chargement
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [currentMessage, setCurrentMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showRegister, setShowRegister] = useState(false);
    
    // Référence pour le scroll automatique
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fonction pour scroll automatique vers le dernier message
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // Effet pour scroller automatiquement à chaque nouveau message
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Message de bienvenue au chargement
    useEffect(() => {
        setMessages([
            {
                role: 'assistant',
                content: 'Bonjour ! Je suis votre assistant. Comment puis-je vous aider aujourd\'hui ?'
            }
        ]);
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            setIsAuthenticated(true);
            // Charger l'historique des messages
            loadChatHistory();
        }
    }, []);

    const loadChatHistory = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/history', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            if (response.ok) {
                const history = await response.json();
                setMessages(history);
            }
        } catch (error) {
            console.error('Erreur lors du chargement de l\'historique:', error);
        }
    };

    const handleLogin = (token: string) => {
        setIsAuthenticated(true);
        loadChatHistory();
    };

    if (!isAuthenticated) {
        if (showRegister) {
            return (
                <RegisterForm 
                    onRegisterSuccess={() => setShowRegister(false)}
                    switchToLogin={() => setShowRegister(false)}
                />
            );
        }
        return (
            <LoginForm 
                onLogin={handleLogin}
                switchToRegister={() => setShowRegister(true)}
            />
        );
    }

    // Fonction pour formater le message avec la source
    const formatMessageWithSource = (content: string, sources: Source[] | undefined) => {
        if (!sources?.length) return content;

        // Trouver la meilleure source
        const bestSource = sources.reduce((best, current) => 
            (current.metadata.score > (best?.metadata.score || 0)) ? current : best
        , sources[0]);

        // N'ajouter la source que si le score est supérieur à 50%
        if (bestSource && bestSource.metadata.score > 0.5) {
            const sourceText = ` (source : ${bestSource.metadata.source.replace('data/', '')} - ${(bestSource.metadata.score * 100).toFixed(1)}%)`;
            return (
                <>
                    {content.replace(/\(source : [^)]+\)/, '')}
                    <a
                        href={`http://localhost:8000${bestSource.metadata.view_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:text-blue-700 underline ml-1"
                        onClick={(e) => {
                            e.preventDefault();
                            window.open(
                                `http://localhost:8000${bestSource.metadata.view_url}`,
                                '_blank',
                                'noopener,noreferrer'
                            );
                        }}
                    >
                        {sourceText}
                    </a>
                </>
            );
        }

        return content.replace(/\(source : [^)]+\)/, '');
    };

    // Fonction pour envoyer un message
    const sendMessage = async () => {
        if (!currentMessage.trim()) return;

        try {
            setIsLoading(true);
            // Créer le message utilisateur
            const userMessage: ChatMessage = {
                role: 'user',
                content: currentMessage
            };
            
            // Ajouter le message à l'historique
            setMessages(prev => [...prev, userMessage]);
            setCurrentMessage('');

            const response = await fetch('http://localhost:8000/api/chat/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: [{
                        role: userMessage.role,
                        content: userMessage.content
                    }]
                })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data: ChatResponse = await response.json();
            
            // Ajouter la réponse de l'assistant
            if (data.response) {
                const assistantMessage: ChatMessage = {
                    role: 'assistant',
                    content: data.response,
                    sources: data.source_nodes
                };
                console.log('Message assistant avec sources:', assistantMessage); // Pour debug
                setMessages(prev => [...prev, assistantMessage]);
            }

        } catch (error) {
            console.error('Erreur:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Désolé, une erreur s'est produite. Veuillez réessayer."
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            {/* Header */}
            <div className="bg-white shadow p-4">
                <h1 className="text-xl font-bold text-center">Assistant IA</h1>
            </div>

            {/* Zone des messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className="max-w-[80%]">
                            <div
                                className={`p-4 rounded-lg ${
                                    message.role === 'user'
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-white shadow-md'
                                }`}
                            >
                                {message.role === 'assistant' 
                                    ? formatMessageWithSource(message.content, message.sources)
                                    : message.content
                                }
                            </div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-200 p-4 rounded-lg animate-pulse">
                            En train d'écrire...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Zone de saisie */}
            <div className="bg-white p-4 shadow-lg">
                <div className="max-w-4xl mx-auto flex gap-4">
                    <input
                        type="text"
                        value={currentMessage}
                        onChange={(e) => setCurrentMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                        placeholder="Tapez votre message..."
                        className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isLoading}
                    />
                    <button
                        onClick={sendMessage}
                        disabled={isLoading}
                        className={`px-6 py-2 rounded-lg font-medium ${
                            isLoading
                                ? 'bg-gray-300 cursor-not-allowed'
                                : 'bg-blue-500 hover:bg-blue-600 text-white'
                        }`}
                    >
                        Envoyer
                    </button>
                </div>
            </div>
        </div>
    );
} 