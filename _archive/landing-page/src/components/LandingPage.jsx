import { motion } from 'framer-motion';
import { useState } from 'react';

/**
 * LandingPage - Page principale avec toutes les sections
 */
const LandingPage = () => {
  const [activeStep, setActiveStep] = useState(null);

  // Animation variants
  const fadeInUp = {
    initial: { opacity: 0, y: 40 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 }
  };

  const staggerContainer = {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  // Données des 5 étapes
  const steps = [
    {
      number: "1",
      title: "Vigne – Traitements & suivi parcellaire",
      description: "Visualisez vos parcelles, planifiez et tracez vos traitements sans vous perdre dans les lignes.",
      points: [
        "Vue parcellaire simple et lisible",
        "Historique des traitements par parcelle",
        "Préparation facilitée des obligations réglementaires"
      ],
      icon: (
        <svg className="w-8 h-8 stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M3 12h18M8 8l4-4 4 4M8 16l4 4 4-4" />
        </svg>
      )
    },
    {
      number: "2",
      title: "Vendanges – Entrées de récolte",
      description: "Chaque kilo vendangé est tracé dès son arrivée au chai.",
      points: [
        "Saisie rapide des apports",
        "Lien direct avec parcelles et cuvées",
        "Gestion des écarts et ajustements"
      ],
      icon: (
        <svg className="w-8 h-8 stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7v10c0 5.5 4.5 10 10 10s10-4.5 10-10V7L12 2z" />
        </svg>
      )
    },
    {
      number: "3",
      title: "Encuvage – Suivi des cuves & opérations",
      description: "De la vendange brute à la cuve, chaque mouvement est tracé.",
      points: [
        "Historique des opérations",
        "Gestion des volumes et pertes",
        "Traçabilité prête pour audit"
      ],
      icon: (
        <svg className="w-8 h-8 stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v20M6 8h12v12a2 2 0 01-2 2H8a2 2 0 01-2-2V8z" />
        </svg>
      )
    },
    {
      number: "4",
      title: "Mises en bouteilles – Lots & étiquettes",
      description: "Des cuves aux bouteilles, vos lots sont clairs et cohérents.",
      points: [
        "Création et suivi des lots",
        "Gestion des consommables",
        "Documents légaux prêts"
      ],
      icon: (
        <svg className="w-8 h-8 stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L8 8v14h8V8l-4-6zM8 8h8M8 14h8" />
        </svg>
      )
    },
    {
      number: "5",
      title: "Ventes – Du stock au client",
      description: "Vendez en direct, aux pros ou en vrac, sans perdre la cohérence avec votre chai.",
      points: [
        "Ventes directes, pro et vrac",
        "Stock à jour",
        "Base pour e-commerce et blockchain"
      ],
      icon: (
        <svg className="w-8 h-8 stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  ];

  // Données "Pourquoi Mon Chai"
  const features = [
    {
      title: "Clair et sobre",
      description: "Interface épurée, sans jargon."
    },
    {
      title: "Aligné sur le réel du chai",
      description: "Accepte les cas flous et garde la cohérence."
    },
    {
      title: "Pensé pour grandir avec vous",
      description: "DRM, e-commerce, traçabilité blockchain à venir."
    }
  ];

  // Données aperçu produit
  const productPreviews = [
    "Vue parcellaire",
    "Écran de vendange",
    "Suivi de cuve",
    "Stock / lots bouteilles"
  ];

  return (
    <div className="min-h-screen bg-anthracite">
      {/* Navigation minimaliste */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-anthracite/80 backdrop-blur-sm border-b border-ivoire/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-playfair text-wine-gold">Mon Chai</h1>
          <a 
            href="/auth/login/" 
            className="px-6 py-2 border border-wine-gold/50 hover:bg-wine-gold/10 text-ivoire 
                       hover:text-wine-gold transition-all duration-300 rounded-sm text-sm font-medium"
          >
            Me connecter à Mon Chai
          </a>
        </div>
      </nav>

      {/* 1. Hero Section */}
      <motion.section 
        className="pt-32 pb-20 px-6"
        initial="initial"
        animate="animate"
        variants={staggerContainer}
      >
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <motion.div variants={fadeInUp} className="space-y-8">
            <h1 className="text-5xl lg:text-6xl font-playfair text-ivoire leading-tight">
              Mon Chai — Du cep à la bouteille, tout votre chai dans le même outil.
            </h1>
            
            <p className="text-xl text-ivoire/80 font-light leading-relaxed">
              Suivez et pilotez vos traitements, vendanges, encuvages, mises et ventes 
              dans un seul espace clair, pensé pour les vignerons.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <button className="px-8 py-4 bg-bordeaux hover:bg-bordeaux/90 text-ivoire font-medium 
                                 rounded-sm transition-all duration-300 shadow-lg hover:shadow-xl
                                 border border-wine-gold/30 hover:border-wine-gold/50">
                Demander une démo
              </button>
              <button className="px-8 py-4 border border-ivoire/30 hover:border-ivoire/50 text-ivoire 
                                 font-medium rounded-sm transition-all duration-300">
                Voir le parcours en 5 étapes
              </button>
            </div>

            <p className="text-sm text-ivoire/60 space-x-4">
              <span>Sans carte bancaire</span>
              <span>•</span>
              <span>Données hébergées en France</span>
              <span>•</span>
              <span>Pensé avec des vignerons</span>
            </p>
          </motion.div>

          <motion.div variants={fadeInUp} className="relative">
            <div className="aspect-square bg-gradient-to-br from-bordeaux/20 to-wine-gold/10 
                            rounded-sm border border-ivoire/10 flex items-center justify-center">
              <svg className="w-64 h-64 stroke-ivoire/20" fill="none" viewBox="0 0 24 24" strokeWidth={0.5}>
                <path strokeLinecap="round" strokeLinejoin="round" 
                      d="M12 2v20M6 8h12v12a2 2 0 01-2 2H8a2 2 0 01-2-2V8z" />
              </svg>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* 2. Le parcours en 5 étapes */}
      <section className="py-20 px-6 bg-anthracite/50">
        <div className="max-w-5xl mx-auto">
          <motion.h2 
            className="text-4xl font-playfair text-center mb-4 text-ivoire"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Le parcours en 5 étapes
          </motion.h2>
          <motion.p 
            className="text-center text-ivoire/70 mb-16 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            De la vigne à la vente, suivez le fil de votre production
          </motion.p>

          <div className="relative">
            {/* Timeline verticale */}
            <div className="absolute left-8 top-0 bottom-0 w-px bg-wine-gold/30" />

            <div className="space-y-12">
              {steps.map((step, index) => (
                <motion.div
                  key={index}
                  className="relative pl-20"
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  {/* Icône */}
                  <div className="absolute left-0 w-16 h-16 bg-anthracite border border-wine-gold/50 
                                  rounded-sm flex items-center justify-center text-wine-gold">
                    {step.icon}
                  </div>

                  {/* Contenu */}
                  <div 
                    className="border border-ivoire/10 rounded-sm p-6 hover:border-ivoire/20 
                               transition-all duration-300 cursor-pointer bg-anthracite/50"
                    onClick={() => setActiveStep(activeStep === index ? null : index)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-2xl font-playfair text-ivoire">{step.title}</h3>
                      <span className="text-4xl font-playfair text-wine-gold/30">{step.number}</span>
                    </div>
                    
                    <p className="text-ivoire/70 mb-4">{step.description}</p>

                    {/* Points clés (accordéon) */}
                    <motion.div
                      initial={false}
                      animate={{ height: activeStep === index ? 'auto' : 0 }}
                      className="overflow-hidden"
                    >
                      <ul className="space-y-2 pt-4 border-t border-ivoire/10">
                        {step.points.map((point, i) => (
                          <li key={i} className="flex items-start text-sm text-ivoire/60">
                            <span className="text-wine-gold mr-2">–</span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 3. Pourquoi Mon Chai */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.h2 
            className="text-4xl font-playfair text-center mb-16 text-ivoire"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Pourquoi Mon Chai ?
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                className="border border-ivoire/10 rounded-sm p-8 hover:border-wine-gold/30 
                           transition-all duration-300 group"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <h3 className="text-2xl font-playfair text-ivoire mb-4 group-hover:text-wine-gold 
                               transition-colors">
                  {feature.title}
                </h3>
                <p className="text-ivoire/70">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Aperçu produit */}
      <section className="py-20 px-6 bg-anthracite/50">
        <div className="max-w-6xl mx-auto">
          <motion.h2 
            className="text-4xl font-playfair text-center mb-4 text-ivoire"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Aperçu produit
          </motion.h2>
          <motion.p 
            className="text-center text-ivoire/70 mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Découvrez l'interface pensée pour votre quotidien
          </motion.p>

          <div className="grid md:grid-cols-2 gap-8">
            {productPreviews.map((preview, index) => (
              <motion.div
                key={index}
                className="aspect-video bg-gradient-to-br from-bordeaux/10 to-wine-gold/5 
                           rounded-sm border border-ivoire/10 flex items-center justify-center
                           hover:border-wine-gold/30 transition-all duration-300 cursor-pointer
                           shadow-lg hover:shadow-xl"
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <p className="text-xl font-playfair text-ivoire/40">{preview}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. CTA final */}
      <section className="py-32 px-6">
        <motion.div 
          className="max-w-4xl mx-auto text-center border border-wine-gold/30 rounded-sm p-12
                     bg-gradient-to-br from-bordeaux/10 to-transparent"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl font-playfair text-ivoire mb-6">
            Envie de tester Mon Chai sur votre domaine ?
          </h2>
          <p className="text-xl text-ivoire/70 mb-10 max-w-2xl mx-auto">
            Discutons de votre façon de travailler et voyons si l'outil peut s'adapter à votre chai.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-8 py-4 bg-bordeaux hover:bg-bordeaux/90 text-ivoire font-medium 
                               rounded-sm transition-all duration-300 shadow-lg hover:shadow-xl
                               border border-wine-gold/30 hover:border-wine-gold/50">
              Demander un appel
            </button>
            <button className="px-8 py-4 text-ivoire hover:text-wine-gold font-medium 
                               transition-colors duration-300">
              Recevoir une présentation par email
            </button>
          </div>
        </motion.div>
      </section>

      {/* Footer minimal */}
      <footer className="border-t border-ivoire/10 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center 
                        text-sm text-ivoire/50 space-y-4 md:space-y-0">
          <p>© 2025 Mon Chai. Données hébergées en France.</p>
          <div className="flex space-x-8">
            <a href="#" className="hover:text-wine-gold transition-colors">Conditions</a>
            <a href="#" className="hover:text-wine-gold transition-colors">Confidentialité</a>
            <a href="#" className="hover:text-wine-gold transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
