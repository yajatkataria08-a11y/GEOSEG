import { Variants, Transition } from 'framer-motion';

// Smooth exponential easing
const smoothSpring: Transition = {
  type: 'spring',
  stiffness: 260,
  damping: 28,
  mass: 0.8,
};

const gentleSpring: Transition = {
  type: 'spring',
  stiffness: 180,
  damping: 24,
  mass: 1,
};

// Page-level cross-fade transitions
export const pageVariants: Variants = {
  initial: {
    opacity: 0,
    y: 16,
    filter: 'blur(4px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.08,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    filter: 'blur(4px)',
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 1, 1],
    },
  },
};

// Stagger container
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1,
    },
  },
};

// Fade up for children
export const fadeUp: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.45,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

// Scale in from center
export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.92 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: smoothSpring,
  },
};

// Smooth slide in from side
export const slideInRight: Variants = {
  initial: { opacity: 0, x: 30 },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1],
    },
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 1, 1],
    },
  },
};

// Floating organic motion (for chips, badges, thumbnails)
export const floatMotion = {
  animate: {
    y: [-3, 3, -3],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: 'easeInOut' as const,
    },
  },
};

// Hover lift interaction
export const hoverLift = {
  whileHover: { y: -3, scale: 1.02 },
  whileTap: { scale: 0.98 },
  transition: smoothSpring,
};

// Card hover with glow
export const cardHover = {
  whileHover: {
    y: -4,
    scale: 1.015,
    transition: gentleSpring,
  },
  whileTap: {
    scale: 0.985,
    transition: { duration: 0.1 },
  },
};

// Smooth number counter transition (for progress bars, dials)
export const counterTransition: Transition = {
  type: 'spring',
  stiffness: 100,
  damping: 20,
  mass: 1.2,
};

export { smoothSpring, gentleSpring };
