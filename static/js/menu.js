// Menu Mobile - Arquivo externo para compatibilidade com CSP
(function() {
  console.log('🔧 DEBUG: Script do menu carregando...');
  
  function initMenu() {
    console.log('🔧 DEBUG: Inicializando menu mobile');
    
    const toggle = document.getElementById('menu-toggle');
    const menu = document.getElementById('menu');
    
    console.log('🔧 DEBUG: Toggle encontrado?', !!toggle);
    console.log('🔧 DEBUG: Menu encontrado?', !!menu);
    
    if (!toggle || !menu) {
      console.error('❌ DEBUG: Elementos do menu não encontrados!');
      return;
    }
    
    const menuLinks = menu.querySelectorAll('a');
    console.log('🔧 DEBUG: Links do menu:', menuLinks.length);
    
    function abrirMenu() {
      console.log('🔧 DEBUG: Abrindo menu');
      menu.classList.add('ativo');
      document.body.classList.add('menu-aberto');
      toggle.setAttribute('aria-expanded', 'true');
    }
    
    function fecharMenu() {
      console.log('🔧 DEBUG: Fechando menu');
      menu.classList.remove('ativo');
      document.body.classList.remove('menu-aberto');
      toggle.setAttribute('aria-expanded', 'false');
    }
    
    // Abrir/fechar menu ao clicar/tocar no toggle
    toggle.addEventListener('click', function(e) {
      console.log('🔧 DEBUG: CLICK no botão toggle!');
      e.preventDefault();
      e.stopPropagation();
      
      if (menu.classList.contains('ativo')) {
        fecharMenu();
      } else {
        abrirMenu();
      }
    });
    
    // Touchstart para melhor resposta no mobile
    toggle.addEventListener('touchstart', function(e) {
      console.log('🔧 DEBUG: TOUCH no botão toggle!');
      e.preventDefault();
      e.stopPropagation();
      
      if (menu.classList.contains('ativo')) {
        fecharMenu();
      } else {
        abrirMenu();
      }
    }, { passive: false });
    
    // Fechar menu ao clicar em um link
    menuLinks.forEach(function(link, index) {
      link.addEventListener('click', function(e) {
        console.log('🔧 DEBUG: Clique no link', index, link.href);
        setTimeout(fecharMenu, 100);
      });
      
      link.addEventListener('touchend', function(e) {
        console.log('🔧 DEBUG: Touch no link', index, link.href);
        setTimeout(fecharMenu, 100);
      });
    });
    
    // Fechar menu ao clicar no overlay (área escura)
    document.addEventListener('click', function(e) {
      if (menu.classList.contains('ativo') && 
          !menu.contains(e.target) && 
          !toggle.contains(e.target)) {
        console.log('🔧 DEBUG: Clique no overlay - fechando');
        fecharMenu();
      }
    });
    
    console.log('✅ DEBUG: Menu mobile inicializado com sucesso!');
  }
  
  // Executar quando DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMenu);
  } else {
    initMenu();
  }
})();
