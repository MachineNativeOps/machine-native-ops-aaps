// MachineNativeOps Pages - Main Entry Point
console.log('🚀 MachineNativeOps Platform Initialized');

// Add interactive features
document.addEventListener('DOMContentLoaded', () => {
  console.log('✅ Page loaded successfully');
  
  // Add animation to feature cards
  const featureCards = document.querySelectorAll('.feature-card');
  
  featureCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
    card.style.opacity = '0';
    card.style.animation = 'fadeInUp 0.6s ease forwards';
  });
});

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
document.head.appendChild(style);
