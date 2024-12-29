'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Source, ChatResponse } from '@/types/chat';
import LoginForm from '../Auth/LoginForm';
import RegisterForm from '../Auth/RegisterForm';
import LogoutButton from '../Auth/LogoutButton';
import Sidebar from './Sidebar';
import { motion } from 'framer-motion';

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
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
    
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
        // Vérifier si un token existe
        const token = localStorage.getItem('token');
        if (!token) {
            setIsAuthenticated(false);
        } else {
            setIsAuthenticated(true);
            // Charger l'historique des messages
            loadChatHistory();
        }
    }, []);

    const loadChatHistory = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/api/chat/history', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                const history = await response.json();
                setMessages(history);
            } else if (response.status === 401) {
                // Si le token est invalide, déconnectez l'utilisateur
                setIsAuthenticated(false);
                localStorage.removeItem('token');
            }
        } catch (error) {
            console.error('Erreur lors du chargement de l\'historique:', error);
        }
    };

    // Fonction pour formater le message avec la source
    const formatMessageWithSource = (content: string, sources: Source[] | undefined) => {
        if (!sources?.length) return content;

        console.log("Sources reçues:", sources); // Debug

        // Vérifier si les sources ont la bonne structure
        if (!sources[0]?.metadata?.score) {
            console.log("Sources mal formatées:", sources);
            return content;
        }

        // Trouver la meilleure source
        const bestSource = sources.reduce((best, current) => {
            if (!best?.metadata?.score) return current;
            if (!current?.metadata?.score) return best;
            return current.metadata.score > best.metadata.score ? current : best;
        }, sources[0]);

        // N'ajouter la source que si le score est supérieur à 50% et si la source existe
        if (bestSource?.metadata?.score > 0.5) {
            const sourceText = ` (source : ${bestSource.metadata.source.replace('data/', '')} - ${(bestSource.metadata.score * 100).toFixed(1)}%)`;
            
            return (
                <>
                    {content}
                    {bestSource.metadata.view_url && (
                        <a
                            href={`http://localhost:8000${bestSource.metadata.view_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-700 underline ml-1"
                        >
                            {sourceText}
                        </a>
                    )}
                </>
            );
        }

        return content;
    };

    // Fonction pour envoyer un message
    const sendMessage = async (message: string) => {
        try {
            setIsLoading(true);
            const token = localStorage.getItem('token');
            
            if (!token) {
                setIsAuthenticated(false);
                throw new Error('Non authentifié');
            }

            // Ajouter le message de l'utilisateur
            const userMessage: ChatMessage = {
                role: 'user',
                content: message
            };
            setMessages(prev => [...prev, userMessage]);
            setCurrentMessage('');

            const response = await fetch('http://localhost:8000/api/chat/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: currentConversationId || conversationId
                })
            });

            if (response.status === 401) {
                setIsAuthenticated(false);
                localStorage.removeItem('token');
                throw new Error('Session expirée');
            }

            if (!response.ok) {
                throw new Error('Erreur de communication');
            }

            const data = await response.json();
            
            // Ajouter la réponse de l'assistant
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: data.content,
                sources: data.source_nodes
            };
            setMessages(prev => [...prev, assistantMessage]);

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

    // Au chargement initial, créer une nouvelle conversation
    useEffect(() => {
        if (isAuthenticated) {
            startNewConversation();
        }
    }, [isAuthenticated]);

    const startNewConversation = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/api/chat/conversation', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setConversationId(data.conversation_id);
                setMessages([{
                    role: 'assistant',
                    content: 'Bonjour ! Je suis votre assistant. Comment puis-je vous aider aujourd\'hui ?'
                }]);
            }
        } catch (error) {
            console.error('Erreur lors de la création de la conversation:', error);
        }
    };

    // Fonction pour charger les messages d'une conversation
    const loadConversationMessages = async (conversationId: string) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:8000/api/chat/history?conversation_id=${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Erreur lors du chargement des messages');
            }

            const data = await response.json();
            console.log("Messages chargés:", data); // Debug

            if (Array.isArray(data)) {
                setMessages(data);
                setCurrentConversationId(conversationId);
            } else {
                console.error("Format de données invalide:", data);
            }
        } catch (error) {
            console.error('Erreur lors du chargement des messages:', error);
            setMessages([{
                role: 'assistant',
                content: "Erreur lors du chargement de la conversation. Veuillez réessayer."
            }]);
        }
    };

    // Gestionnaire de sélection de conversation
    const handleConversationSelect = async (conversationId: string) => {
        setCurrentConversationId(conversationId);
        await loadConversationMessages(conversationId);
    };

    // Afficher le formulaire de connexion/inscription si non authentifié
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
                onLogin={(token) => {
                    localStorage.setItem('token', token);
                    setIsAuthenticated(true);
                }}
                switchToRegister={() => setShowRegister(true)}
            />
        );
    }

    return (
        <div className="flex h-screen bg-[#111111]">
            {isAuthenticated && (
                <Sidebar onConversationSelect={handleConversationSelect} />
            )}
            
            <div className="flex-1 flex flex-col">
                <div className="flex flex-col h-screen">
                    <div className="bg-gradient-to-r from-[#1a1a1a] to-[#2a2a2a] p-4 flex justify-between items-center">
                        <h1 className="text-xl font-bold text-white">Assistant IA</h1>
                        <div className="flex gap-4">
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={startNewConversation}
                                className="bg-[#2a2a2a] text-white px-4 py-2 rounded-lg hover:bg-[#3a3a3a] transition-all duration-200"
                            >
                                Nouvelle conversation
                            </motion.button>
                            <LogoutButton onLogout={() => setIsAuthenticated(false)} />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#111111]">
                        {messages.length <= 1 ? (
                            // Message de bienvenue avec logo
                            <div className="flex justify-center items-center h-full">
                                <motion.div
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    className="text-center"
                                >
                                    <div className="w-32 h-32 mx-auto mb-8 relative">
                                        <div className="absolute inset-0 bg-blue-500 opacity-20 rounded-full animate-pulse"></div>
                                        <div className="relative z-10 w-full h-full rounded-full border-2 border-blue-500 flex items-center justify-center">
                                            <span className="text-2xl text-white">AI</span>
                                        </div>
                                    </div>
                                    <h2 className="text-xl text-white mb-4">Comment puis-je vous aider aujourd'hui ?</h2>
                                </motion.div>
                            </div>
                        ) : (
                            // Messages de la conversation
                            <div className="space-y-4">
                                {messages.map((message, index) => (
                                    <motion.div
                                        key={index}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className="max-w-[80%]">
                                            <div className={`p-4 rounded-lg ${
                                                message.role === 'user'
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-[#2a2a2a] text-white'
                                            }`}>
                                                {message.role === 'assistant' 
                                                    ? formatMessageWithSource(message.content, message.sources)
                                                    : message.content
                                                }
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}

                        {isLoading && (
                            <motion.div 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex justify-start"
                            >
                                <div className="bg-[#2a2a2a] p-4 rounded-lg text-white flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="bg-[#1a1a1a] p-6 border-t border-[#2a2a2a]">
                        <div className="max-w-4xl mx-auto flex gap-4">
                            <motion.input
                                whileFocus={{ scale: 1.01 }}
                                type="text"
                                value={currentMessage}
                                onChange={(e) => setCurrentMessage(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage(currentMessage)}
                                placeholder="Tapez votre message..."
                                className="flex-1 p-4 bg-[#2a2a2a] text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                            />
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => sendMessage(currentMessage)}
                                disabled={isLoading}
                                className="px-6 py-4 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-all duration-200 disabled:opacity-50"
                            >
                                Envoyer
                            </motion.button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
} 