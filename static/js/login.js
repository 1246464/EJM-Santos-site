// ============================================
// login.js — Lógica de Login e Cadastro
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  const loginC = document.getElementById('login-container');
  const cadC = document.getElementById('cadastro-container');
  const msg = document.getElementById('msg');

  // Alternar para CADASTRO
  const btnMostrarCadastro = document.getElementById('mostrar-cadastro');
  if (btnMostrarCadastro) {
    btnMostrarCadastro.onclick = (e) => {
      e.preventDefault();
      loginC.style.display = "none";
      cadC.style.display = "block";
      if (msg) msg.textContent = "";
    };
  }

  // Alternar para LOGIN
  const btnMostrarLogin = document.getElementById('mostrar-login');
  if (btnMostrarLogin) {
    btnMostrarLogin.onclick = (e) => {
      e.preventDefault();
      cadC.style.display = "none";
      loginC.style.display = "block";
      if (msg) msg.textContent = "";
    };
  }

  // CADASTRO VIA /api/register
  const btnCad = document.getElementById('btn-cad');
  if (btnCad) {
    btnCad.onclick = async () => {
      const nome = document.getElementById('nome-cad').value.trim();
      const email = document.getElementById('email-cad').value.trim();
      const senha = document.getElementById('senha-cad').value.trim();

      if (!nome || !email || !senha) {
        if (msg) {
          msg.textContent = 'Preencha todos os campos.';
          msg.style.color = 'red';
        }
        return;
      }

      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ nome, email, senha })
        });

        if (!res) {
          throw new Error('Resposta inválida do servidor');
        }

        const j = await res.json();
        
        if (res.ok) {
          if (msg) {
            msg.textContent = '✅ Cadastro realizado! Faça login agora.';
            msg.style.color = 'green';
          }
          setTimeout(() => {
            cadC.style.display = "none";
            loginC.style.display = "block";
          }, 2000);
        } else {
          if (msg) {
            msg.textContent = j.message || 'Erro ao cadastrar.';
            msg.style.color = 'red';
          }
        }
      } catch (error) {
        console.error('Erro ao cadastrar:', error);
        if (msg) {
          msg.textContent = 'Erro de conexão. Tente novamente.';
          msg.style.color = 'red';
        }
      }
    };
  }
});
