import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Conversation {
    id: string;
    created_at: string;
}

interface SidebarProps {
    onConversationSelect: (conversationId: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onConversationSelect }) => {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);
    
    // Attendre que le composant soit monté
    useEffect(() => {
        setMounted(true);
    }, []);

    // Charger les conversations
    const loadConversations = async () => {
        try {
            setIsLoading(true);
            const response = await fetch('http://localhost:8000/api/conversations', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Erreur lors du chargement des conversations');
            }

            const data = await response.json();
            setConversations(data);
        } catch (err: any) { // Typage explicite de err
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (mounted) {
            loadConversations();
        }
    }, [mounted]); // Dépendance au montage

    // Créer une nouvelle conversation
    const createNewConversation = async () => {
        if (!mounted) return; // Ne rien faire si non monté
        
        try {
            const response = await fetch('http://localhost:8000/api/chat/conversation', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Erreur lors de la création de la conversation');
            }

            const data = await response.json();
            onConversationSelect(data.conversation_id);
            loadConversations(); // Recharger la liste
        } catch (err: any) { // Typage explicite de err
            setError(err.message);
        }
    };

    // Ne rien rendre tant que le composant n'est pas monté
    if (!mounted) {
        return null;
    }

    return (
        <motion.div 
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-64 h-screen bg-gradient-to-b from-gray-800 to-gray-900 text-white p-4 shadow-xl"
        >
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={createNewConversation}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg mb-4 transition-all duration-200 shadow-lg"
            >
                Nouvelle conversation
            </motion.button>

            <div className="space-y-2">
                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-center p-4"
                    >
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                    </motion.div>
                )}
                
                <AnimatePresence>
                    {conversations.map((conv, index) => (
                        <motion.div
                            key={conv.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ delay: index * 0.1 }}
                            onClick={() => onConversationSelect(conv.id)}
                            className="cursor-pointer p-3 hover:bg-gray-700 rounded-lg transition-all duration-200 backdrop-blur-sm bg-opacity-50 shadow-md"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                <span>Conversation {conv.id.slice(0, 8)}...</span>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default Sidebar; 