// Perfil - Gerenciamento de Abas
document.addEventListener('DOMContentLoaded', function() {
  // Configurar event listeners para as abas
  const tabButtons = document.querySelectorAll('.tab-btn');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const tabName = this.getAttribute('data-tab');
      showTab(tabName, this);
    });
  });
});

function showTab(tabName, buttonElement) {
  // Remove active de todos os botões e conteúdos
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  // Adiciona active no botão e conteúdo selecionado
  if (buttonElement) {
    buttonElement.classList.add('active');
  }
  document.getElementById('tab-' + tabName).classList.add('active');
}

function abrirModalEndereco() {
  document.getElementById('modal-endereco').style.display = 'flex';
}

function abrirModalCartao() {
  document.getElementById('modal-cartao').style.display = 'flex';
}

function fecharModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
}

// Fechar modal ao clicar fora
document.querySelectorAll('.modal-overlay').forEach(modal => {
  modal.addEventListener('click', function(e) {
    if (e.target === this) {
      this.style.display = 'none';
    }
  });
});

// Form de Endereço
document.getElementById('form-endereco')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const data = Object.fromEntries(formData);
  
  try {
    const response = await fetch('/api/addresses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert('✅ Endereço salvo com sucesso!');
      fecharModal('modal-endereco');
      this.reset();
      location.reload();
    } else {
      alert('❌ Erro: ' + (result.error || 'Não foi possível salvar o endereço'));
    }
  } catch (error) {
    console.error('Erro ao salvar endereço:', error);
    alert('❌ Erro ao salvar endereço. Tente novamente.');
  }
});

// Form de Cartão
document.getElementById('form-cartao')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const data = Object.fromEntries(formData);
  
  try {
    const response = await fetch('/api/payment-methods', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert('✅ Cartão salvo com sucesso!');
      fecharModal('modal-cartao');
      this.reset();
      location.reload();
    } else {
      alert('❌ Erro: ' + (result.error || 'Não foi possível salvar o cartão'));
    }
  } catch (error) {
    console.error('Erro ao salvar cartão:', error);
    alert('❌ Erro ao salvar cartão. Tente novamente.');
  }
});

// Form de Alterar Senha
document.getElementById('form-senha')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const data = Object.fromEntries(formData);
  
  if (data.nova_senha !== data.confirmar_senha) {
    alert('❌ As senhas não coincidem!');
    return;
  }
  
  console.log('Alterando senha');
  alert('✅ Senha alterada com sucesso!\n\n(Funcionalidade de backend em desenvolvimento)');
  fecharModal('modal-senha');
  this.reset();
});

// Botão alterar senha
document.querySelector('.btn-alterar')?.addEventListener('click', function() {
  document.getElementById('modal-senha').style.display = 'flex';
});

// Máscara de CEP
document.querySelector('input[name="cep"]')?.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 5) {
    value = value.slice(0, 5) + '-' + value.slice(5, 8);
  }
  e.target.value = value;
});

// Máscara de Telefone
document.querySelector('input[name="telefone"]')?.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 10) {
    value = '(' + value.slice(0, 2) + ') ' + value.slice(2, 7) + '-' + value.slice(7, 11);
  } else if (value.length > 6) {
    value = '(' + value.slice(0, 2) + ') ' + value.slice(2, 6) + '-' + value.slice(6);
  } else if (value.length > 2) {
    value = '(' + value.slice(0, 2) + ') ' + value.slice(2);
  }
  e.target.value = value;
});

// Máscara de Número de Cartão
document.getElementById('numero-cartao')?.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
  e.target.value = value.slice(0, 19);
});

// Máscara de Validade do Cartão
document.getElementById('validade-cartao')?.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length >= 2) {
    value = value.slice(0, 2) + '/' + value.slice(2, 4);
  }
  e.target.value = value;
});

// Máscara de CVV
document.getElementById('cvv-cartao')?.addEventListener('input', function(e) {
  e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
});

// Máscara de CPF
document.getElementById('cpf-cartao')?.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length <= 11) {
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  }
  e.target.value = value;
});

// Funções para gerenciar endereços e cartões
function irParaCheckout() {
  window.location.href = '/carrinho';
}

function removerEndereco(id) {
  if (!confirm('Deseja remover este endereço?')) return;
  
  fetch(`/api/addresses/${id}`, {
    method: 'DELETE',
    headers: {'Content-Type':'application/json'}
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert('❌ Erro ao remover endereço: ' + data.error);
    } else {
      alert('✅ Endereço removido com sucesso!');
      location.reload();
    }
  })
  .catch(err => {
    alert('❌ Erro: ' + err.message);
  });
}

function removerCartao(id) {
  if (!confirm('Deseja remover este cartão? Esta ação não pode ser desfeita.')) return;
  
  fetch(`/api/payment-methods/${id}`, {
    method: 'DELETE',
    headers: {'Content-Type':'application/json'}
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert('❌ Erro ao remover cartão: ' + data.error);
    } else {
      alert('✅ Cartão removido com sucesso!');
      location.reload();
    }
  })
  .catch(err => {
    alert('❌ Erro: ' + err.message);
  });
}

function editarEndereco(id) {
  alert('💡 Para editar, remova este endereço e adicione um novo durante o próximo checkout.');
}
