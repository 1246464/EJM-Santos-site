// static/js/main.js
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
});
