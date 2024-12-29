import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

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
        <div className="w-64 h-screen bg-gray-800 text-white p-4">
            <button
                onClick={createNewConversation}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4"
            >
                Nouvelle conversation
            </button>

            <div className="space-y-2">
                {isLoading && <div>Chargement...</div>}
                {error && <div className="text-red-500">{error}</div>}
                
                {conversations.map((conv) => (
                    <div
                        key={conv.id}
                        onClick={() => onConversationSelect(conv.id)}
                        className="cursor-pointer p-2 hover:bg-gray-700 rounded"
                    >
                        Conversation {conv.id.slice(0, 8)}...
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Sidebar; 