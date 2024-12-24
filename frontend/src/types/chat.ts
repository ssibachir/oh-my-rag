/**
 * Interface représentant la structure d'un message dans le chat
 * ce fichier joue un rôle fondamental pour structurer et formaliser
 *  la communication entre le front-end et l'API, tout en assurant
 *  que les données sont utilisées de manière cohérente dans l'application.
 */
export interface Message {
    /**
     * Le rôle de l'émetteur du message
     * - 'user' : message envoyé par l'utilisateur
     * - 'assistant' : message envoyé par l'assistant IA
     */
    role: 'user' | 'assistant';

    /**
     * Le contenu textuel du message
     */
    content: string;
}

/**
 * Interface pour les métadonnées des sources
 */
export interface SourceMetadata {
    /**
     * Nom du fichier source
     */
    source: string;
    /**
     * URL pour visualiser la source
     */
    view_url: string;
    /**
     * Score de pertinence de la source
     */
    score: number;
}

/**
 * Interface pour une source individuelle
 */
export interface Source {
    /**
     * Texte extrait de la source
     */
    text: string;
    /**
     * Métadonnées de la source
     */
    metadata: SourceMetadata;
}

/**
 * Interface représentant la structure de la réponse de l'API
 */
export interface ChatResponse {
    /**
     * La réponse textuelle générée par l'assistant
     */
    response: string;

    /**
     * Les sources utilisées pour générer la réponse
     */
    source_nodes: Source[];
} 