import { useState, useEffect } from 'react';
import IntroExperience from './components/IntroExperience';
import LandingPage from './components/LandingPage';

/**
 * App - Composant racine gérant le routing intro/landing
 * Utilise localStorage pour mémoriser si l'utilisateur a déjà vu l'intro
 */
function App() {
  const [showIntro, setShowIntro] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Vérifie si l'utilisateur a déjà visité le site
    const hasVisited = localStorage.getItem('monchai_has_visited');
    
    if (!hasVisited) {
      // Première visite → afficher l'intro
      setShowIntro(true);
    }
    
    setLoading(false);
  }, []);

  const handleIntroComplete = () => {
    // Marque la visite dans localStorage
    localStorage.setItem('monchai_has_visited', 'true');
    
    // Masque l'intro et affiche la landing
    setShowIntro(false);
  };

  // Écran de chargement minimal
  if (loading) {
    return (
      <div className="fixed inset-0 bg-anthracite flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-wine-gold/30 border-t-wine-gold rounded-full animate-spin" />
      </div>
    );
  }

  // Affiche l'intro ou la landing selon l'état
  return showIntro ? (
    <IntroExperience onComplete={handleIntroComplete} />
  ) : (
    <LandingPage />
  );
}

export default App;
