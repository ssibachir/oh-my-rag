import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

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
    const [selectedId, setSelectedId] = useState<string | null>(null);
    
    useEffect(() => {
        setMounted(true);
    }, []);

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
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (mounted) {
            loadConversations();
        }
    }, [mounted]);

    const handleConversationClick = (id: string) => {
        setSelectedId(id);
        onConversationSelect(id);
    };

    if (!mounted) return null;

    return (
        <motion.div 
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-80 h-screen bg-[#1a1a1a] text-white p-4 border-r border-[#2a2a2a] overflow-hidden"
        >
            <div className="space-y-4">
                {/* En-tête */}
                <div className="flex items-center justify-between mb-6">
                    <motion.h2 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-lg font-semibold text-gray-300"
                    >
                        Conversations
                    </motion.h2>
                </div>

                {/* Liste des conversations */}
                <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-8rem)]">
                    <AnimatePresence>
                        {isLoading ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="flex justify-center py-4"
                            >
                                <div className="flex space-x-2">
                                    {[0, 1, 2].map((i) => (
                                        <div
                                            key={i}
                                            className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                                            style={{ animationDelay: `${i * 0.15}s` }}
                                        />
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            conversations.map((conv, index) => (
                                <motion.div
                                    key={conv.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ delay: index * 0.1 }}
                                    onClick={() => handleConversationClick(conv.id)}
                                    className={`
                                        group cursor-pointer p-3 rounded-lg
                                        ${selectedId === conv.id ? 'bg-[#2a2a2a]' : 'hover:bg-[#222222]'}
                                        transition-all duration-200 relative overflow-hidden
                                    `}
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className={`
                                            w-2 h-2 rounded-full
                                            ${selectedId === conv.id ? 'bg-blue-500' : 'bg-gray-500'}
                                            group-hover:bg-blue-500 transition-colors
                                        `}/>
                                        <div className="flex-1">
                                            <p className="text-sm text-gray-300 font-medium truncate">
                                                Conversation {conv.id.slice(0, 8)}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {format(new Date(conv.created_at), 'dd MMM yyyy, HH:mm', { locale: fr })}
                                            </p>
                                        </div>
                                    </div>
                                    
                                    {/* Effet de survol */}
                                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"/>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
};

export default Sidebar; 