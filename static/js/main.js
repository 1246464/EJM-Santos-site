// static/js/main.js

// ============================================
// CSRF Token Helper para AJAX
// ============================================

/**
 * Obtém o token CSRF da meta tag
 */
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : null;
}

/**
 * Adiciona token CSRF automaticamente em requisições fetch
 * Uso: fetch(url, csrfFetch({ method: 'POST', body: data }))
 */
function csrfFetch(options = {}) {
  const token = getCSRFToken();
  if (!token) {
    console.warn('⚠️ CSRF token não encontrado na página');
    return options;
  }
  
  // Adicionar token no header para requisições que modificam dados
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    options.headers = options.headers || {};
    options.headers['X-CSRFToken'] = token;
  }
  
  return options;
}

/**
 * Setup para jQuery (se usar)
 */
if (typeof $ !== 'undefined' && $.ajaxSetup) {
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      // Adicionar CSRF token em requisições AJAX do jQuery
      if (!/^(GET|HEAD|OPTIONS)$/i.test(settings.type)) {
        const token = getCSRFToken();
        if (token) {
          xhr.setRequestHeader('X-CSRFToken', token);
        }
      }
    }
  });
}

// ============================================
// Inicialização
// ============================================

document.addEventListener('DOMContentLoaded', ()=>{
  const token = localStorage.getItem('token');
  const linkLogin = document.getElementById('link-login');
  const linkPerfil = document.getElementById('link-perfil');
  if(token){
    const user = JSON.parse(localStorage.getItem('user')||'null');
    if(linkLogin) linkLogin.textContent = user ? user.nome : 'Conta';
    if(linkPerfil) linkPerfil.style.display = 'inline';
  } else {
    if(linkPerfil) linkPerfil.style.display = 'inline';
    if(linkLogin) linkLogin.textContent = 'Entrar / Cadastrar';
  }
  
  // Log do status CSRF (apenas em desenvolvimento)
  if (window.location.hostname === 'localhost' && getCSRFToken()) {
    console.log('✅ CSRF Protection ativo');
  }
});
