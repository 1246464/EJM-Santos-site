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
          msg.textContent = '⚠️ Preencha todos os campos.';
          msg.style.color = '#ff9800';
        }
        return;
      }

      // Validações básicas no frontend
      if (nome.length < 3) {
        if (msg) {
          msg.textContent = '⚠️ Nome deve ter no mínimo 3 caracteres.';
          msg.style.color = '#ff9800';
        }
        return;
      }

      if (senha.length < 8) {
        if (msg) {
          msg.textContent = '⚠️ Senha deve ter no mínimo 8 caracteres.';
          msg.style.color = '#ff9800';
        }
        return;
      }

      // Desabilitar botão durante requisição
      btnCad.disabled = true;
      btnCad.textContent = 'Criando conta...';

      try {
        // Obter CSRF token do meta tag ou input hidden
        let csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (!csrfToken) {
          csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        }
        
        if (!csrfToken) {
          throw new Error('Token CSRF não encontrado. Recarregue a página.');
        }
        
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
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
            msg.style.color = '#4caf50';
          }
          
          // Limpar campos
          document.getElementById('nome-cad').value = '';
          document.getElementById('email-cad').value = '';
          document.getElementById('senha-cad').value = '';
          
          setTimeout(() => {
            cadC.style.display = "none";
            loginC.style.display = "block";
            if (msg) msg.textContent = '';
          }, 2000);
        } else {
          if (msg) {
            msg.textContent = '❌ ' + (j.message || 'Erro ao cadastrar.');
            msg.style.color = '#f44336';
          }
        }
      } catch (error) {
        console.error('Erro ao cadastrar:', error);
        if (msg) {
          msg.textContent = '❌ ' + (error.message || 'Erro de conexão. Tente novamente.');
          msg.style.color = '#f44336';
        }
      } finally {
        // Reabilitar botão
        btnCad.disabled = false;
        btnCad.textContent = 'Criar conta';
      }
    };
  }
});
