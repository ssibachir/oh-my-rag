'use client';

import { useRouter } from 'next/navigation';

interface LogoutButtonProps {
    onLogout: () => void;
}

export default function LogoutButton({ onLogout }: LogoutButtonProps) {
    const router = useRouter();

    const handleLogout = () => {
        // Supprimer le token du localStorage
        localStorage.removeItem('token');
        
        // Appeler le callback
        onLogout();
        
        // Rediriger vers la page de login
        router.push('/');
        router.refresh();
    };

    return (
        <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
        >
            Déconnexion
        </button>
    );
} 