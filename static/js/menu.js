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
    
    // Abrir/fechar menu ao clicar/tocar no toggle
    toggle.addEventListener('click', function(e) {
      console.log('🔧 DEBUG: CLICK no botão toggle!');
      e.preventDefault();
      e.stopPropagation();
      
      const estaAtivo = menu.classList.contains('ativo');
      console.log('🔧 DEBUG: Menu está ativo?', estaAtivo);
      
      menu.classList.toggle('ativo');
      document.body.classList.toggle('menu-aberto');
      
      console.log('🔧 DEBUG: Menu agora:', menu.classList.contains('ativo') ? 'ABERTO ✅' : 'FECHADO ❌');
    });
    
    // Adicionar touchstart para melhor resposta no mobile
    toggle.addEventListener('touchstart', function(e) {
      console.log('🔧 DEBUG: TOUCH no botão toggle!');
      e.preventDefault();
      e.stopPropagation();
      
      menu.classList.toggle('ativo');
      document.body.classList.toggle('menu-aberto');
      
      console.log('🔧 DEBUG: Menu (touch):', menu.classList.contains('ativo') ? 'ABERTO ✅' : 'FECHADO ❌');
    }, { passive: false });
    
    // Fechar menu ao clicar em um link
    menuLinks.forEach(function(link, index) {
      link.addEventListener('click', function() {
        console.log('🔧 DEBUG: Clique no link', index, link.href);
        menu.classList.remove('ativo');
        document.body.classList.remove('menu-aberto');
      });
    });
    
    // Fechar menu ao clicar fora (no overlay)
    document.addEventListener('click', function(e) {
      if (menu.classList.contains('ativo') && 
          !menu.contains(e.target) && 
          !toggle.contains(e.target)) {
        console.log('🔧 DEBUG: Clique fora do menu - fechando');
        menu.classList.remove('ativo');
        document.body.classList.remove('menu-aberto');
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
