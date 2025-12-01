import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * IntroExperience - Animation d'intro immersive en 5 étapes
 * Affichée uniquement lors de la première visite
 */
const IntroExperience = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(-1); // -1 = ligne horizontale
  const [showButton, setShowButton] = useState(false);

  const steps = [
    {
      icon: (
        <svg className="w-16 h-16 stroke-ivoire" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M3 12h18M8 8l4-4 4 4M8 16l4 4 4-4" />
        </svg>
      ),
      title: "Gestion de la vigne",
      description: "Parcelles, traitements et suivi terrain"
    },
    {
      icon: (
        <svg className="w-16 h-16 stroke-ivoire" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7v10c0 5.5 4.5 10 10 10s10-4.5 10-10V7L12 2z" />
        </svg>
      ),
      title: "Vendanges",
      description: "Entrées de récolte et traçabilité"
    },
    {
      icon: (
        <svg className="w-16 h-16 stroke-ivoire" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v20M6 8h12v12a2 2 0 01-2 2H8a2 2 0 01-2-2V8z" />
        </svg>
      ),
      title: "Encuvage",
      description: "Suivi des cuves et opérations"
    },
    {
      icon: (
        <svg className="w-16 h-16 stroke-ivoire" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L8 8v14h8V8l-4-6zM8 8h8M8 14h8" />
        </svg>
      ),
      title: "Mise en bouteilles",
      description: "Lots, étiquettes et conditionnement"
    },
    {
      icon: (
        <svg className="w-16 h-16 stroke-ivoire" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Ventes",
      description: "Du stock au client, direct et pro"
    }
  ];

  useEffect(() => {
    // Animation séquence: ligne horizontale puis étapes
    const timer1 = setTimeout(() => setCurrentStep(0), 800);
    const timer2 = setTimeout(() => setCurrentStep(1), 1600);
    const timer3 = setTimeout(() => setCurrentStep(2), 2400);
    const timer4 = setTimeout(() => setCurrentStep(3), 3200);
    const timer5 = setTimeout(() => setCurrentStep(4), 4000);
    const timer6 = setTimeout(() => setShowButton(true), 5000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);
      clearTimeout(timer6);
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-anthracite flex items-center justify-center overflow-hidden">
      {/* Ligne horizontale traversante */}
      <motion.div
        className="absolute top-1/2 left-0 h-px bg-wine-gold"
        initial={{ width: 0 }}
        animate={{ width: '100%' }}
        transition={{ duration: 0.8, ease: 'easeInOut' }}
      />

      {/* Conteneur des étapes */}
      <div className="relative w-full max-w-6xl px-8 flex justify-around items-center">
        <AnimatePresence>
          {steps.map((step, index) => (
            currentStep >= index && (
              <motion.div
                key={index}
                className="flex flex-col items-center text-center space-y-4"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              >
                <div className="mb-2">
                  {step.icon}
                </div>
                <h3 className="text-xl font-playfair text-ivoire">
                  {step.title}
                </h3>
                <p className="text-sm text-ivoire/70 max-w-[180px]">
                  {step.description}
                </p>
              </motion.div>
            )
          ))}
        </AnimatePresence>
      </div>

      {/* Bouton d'entrée */}
      <AnimatePresence>
        {showButton && (
          <motion.div
            className="absolute bottom-20"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <button
              onClick={onComplete}
              className="px-8 py-4 bg-bordeaux hover:bg-bordeaux/90 text-ivoire font-inter 
                         rounded-sm transition-all duration-300 shadow-lg hover:shadow-xl
                         border border-wine-gold/30 hover:border-wine-gold/50"
            >
              Entrer dans Mon Chai
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default IntroExperience;
