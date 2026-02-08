// Menu Mobile - Arquivo externo para compatibilidade com CSP
(function() {
  console.log('🔧 DEBUG: Script do menu carregando...');
  
  function initMenu() {
    const toggle = document.getElementById('menu-toggle');
    const menu = document.getElementById('menu');
    
    if (!toggle || !menu) return;
    
    const menuLinks = menu.querySelectorAll('a');
    
    function fecharMenu() {
      menu.classList.remove('ativo');
      document.body.classList.remove('menu-aberto');
    }
    
    // Toggle menu
    toggle.addEventListener('click', function(e) {
      e.stopPropagation();
      menu.classList.toggle('ativo');
      document.body.classList.toggle('menu-aberto');
    });
    
    // Fechar ao clicar em link
    menuLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        fecharMenu();
      });
    });
    
    // Fechar ao clicar fora
    document.addEventListener('click', function(e) {
      if (!menu.contains(e.target) && !toggle.contains(e.target)) {
        fecharMenu();
      }
    });
  }
  
  // Executar quando DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMenu);
  } else {
    initMenu();
  }
})();
