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

        console.log("Sources reçues détaillées:", JSON.stringify(sources, null, 2)); // Log détaillé

        // Vérifier si les sources ont la bonne structure
        const bestSource = sources[0];
        console.log("Meilleure source:", bestSource); // Log de la source

        if (bestSource && bestSource.metadata) {
            const fileName = bestSource.metadata.file_name || 
                            bestSource.metadata.source?.replace('data/', '') ||
                            'document';
            const score = bestSource.metadata.score || 0;

            if (score > 0.5) {
                const sourceText = ` (source : ${fileName} - ${(score * 100).toFixed(1)}%)`;
                
                return (
                    <>
                        {content}
                        <a
                            href={`http://localhost:8000/api/folder/view/${fileName}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-700 underline ml-1"
                        >
                            {sourceText}
                        </a>
                    </>
                );
            }
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

            let activeConversationId = currentConversationId;

            // Si pas de conversation active, en créer une nouvelle
            if (!activeConversationId) {
                const convResponse = await fetch('http://localhost:8000/api/chat/conversation', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (convResponse.ok) {
                    const data = await convResponse.json();
                    activeConversationId = data.conversation_id;
                    setConversationId(data.conversation_id);
                    setCurrentConversationId(data.conversation_id);
                } else {
                    throw new Error('Erreur lors de la création de la conversation');
                }
            }

            // Ajouter le message de l'utilisateur
            const userMessage: ChatMessage = {
                role: 'user',
                content: message
            };
            setMessages(prev => [...prev, userMessage]);
            setCurrentMessage('');

            // S'assurer qu'on a un ID de conversation valide
            if (!activeConversationId) {
                throw new Error('ID de conversation non valide');
            }

            const response = await fetch('http://localhost:8000/api/chat/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: activeConversationId
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
            // Ne plus créer de conversation automatiquement
            // startNewConversation();
            
            // À la place, juste afficher le message de bienvenue
            setMessages([{
                role: 'assistant',
                content: 'Bonjour ! Je suis votre assistant. Comment puis-je vous aider aujourd\'hui ?'
            }]);
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
                setCurrentConversationId(data.conversation_id);
                // Réinitialiser les messages avec le message de bienvenue
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
        if (!conversationId) {
            // Réinitialiser pour une nouvelle conversation
            setCurrentConversationId(null);
            setMessages([{
                role: 'assistant',
                content: 'Bonjour ! Je suis votre assistant. Comment puis-je vous aider aujourd\'hui ?'
            }]);
            return;
        }

        // Charger une conversation existante
        setCurrentConversationId(conversationId);
        await loadConversationMessages(conversationId);
    };

    // Ajouter la fonction handleFileUpload
    const handleFileUpload = async (file: File) => {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('token');
            
            console.log("Début de l'upload du fichier:", file.name);

            const response = await fetch('http://localhost:8000/api/folder/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            console.log("Réponse du serveur:", response.status);

            if (!response.ok) {
                const errorData = await response.text();
                console.error("Erreur détaillée:", errorData);
                throw new Error(`Erreur lors de l'upload: ${errorData}`);
            }

            const data = await response.json();
            console.log("Données reçues:", data);

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Le fichier ${data.filename} a été uploadé avec succès et est en cours d'indexation.`
            }]);

        } catch (error) {
            console.error('Erreur upload:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Désolé, une erreur s'est produite lors de l'upload du fichier."
            }]);
        }
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
                            <LogoutButton onLogout={() => setIsAuthenticated(false)} />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#111111]">
                        {!currentConversationId ? (
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
                            <motion.label
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="p-4 rounded-lg bg-[#2a2a2a] text-white cursor-pointer hover:bg-[#3a3a3a] transition-all duration-200"
                            >
                                <input
                                    type="file"
                                    className="hidden"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) {
                                            handleFileUpload(file);
                                        }
                                    }}
                                    accept=".pdf,.txt,.docx,.csv,.xlsx" // Limiter aux extensions supportées
                                />
                                <svg 
                                    xmlns="http://www.w3.org/2000/svg" 
                                    className="h-6 w-6" 
                                    fill="none" 
                                    viewBox="0 0 24 24" 
                                    stroke="currentColor"
                                >
                                    <path 
                                        strokeLinecap="round" 
                                        strokeLinejoin="round" 
                                        strokeWidth={2} 
                                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" 
                                    />
                                </svg>
                            </motion.label>

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