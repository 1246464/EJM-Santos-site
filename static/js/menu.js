// Menu Mobile - Arquivo externo para compatibilidade com CSP
(function() {
  console.log('🔧 DEBUG: Script do menu carregando...');
  
  function initMenu() {
    console.log('🔧 DEBUG: Inicializando menu mobile');
    
    const toggle = document.getElementById('menu-toggle');
    const menu = document.getElementById('menu');
    const closeBtn = document.getElementById('menu-close');
    
    console.log('🔧 DEBUG: Toggle encontrado?', !!toggle);
    console.log('🔧 DEBUG: Menu encontrado?', !!menu);
    console.log('🔧 DEBUG: Botão fechar encontrado?', !!closeBtn);
    
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
    
    // Botão de fechar
    if (closeBtn) {
      closeBtn.addEventListener('click', function(e) {
        console.log('🔧 DEBUG: Clique no botão X');
        e.preventDefault();
        e.stopPropagation();
        fecharMenu();
      });
      
      closeBtn.addEventListener('touchstart', function(e) {
        console.log('🔧 DEBUG: Touch no botão X');
        e.preventDefault();
        e.stopPropagation();
        fecharMenu();
      }, { passive: false });
    }
    
    // Fechar menu ao clicar em um link
    menuLinks.forEach(function(link, index) {
      link.addEventListener('click', function(e) {
        console.log('🔧 DEBUG: Clique no link', index, link.href);
        // NÃO prevenir default - deixar navegação acontecer
        setTimeout(fecharMenu, 100);
      });
      
      link.addEventListener('touchend', function(e) {
        console.log('🔧 DEBUG: Touch no link', index, link.href);
        // NÃO prevenir default - deixar navegação acontecer  
        setTimeout(fecharMenu, 100);
      });
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
