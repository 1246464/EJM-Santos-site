// Carregar e exibir produtos em destaque
window.addEventListener('DOMContentLoaded', () => {
  fetch('/api/products/search?ordenar=nome')
    .then(r => r.json())
    .then(data => {
      console.log('📦 Produtos carregados:', data.length);
      const wrap = document.getElementById('produtos-destaque');
      if (!wrap) return;

      data.slice(0, 6).forEach(p => {
        const esgotado = p.estoque <= 0;
        const card = document.createElement('div');
        card.className = 'card';
        
        // Clique no card inteiro vai para detalhes (exceto botões)
        card.onclick = (e) => {
          if (!e.target.classList.contains('botao-comprar')) {
            window.location.href = `/produto/${p.id}`;
          }
        };
        
        const imagePath = p.imagem.startsWith('imagens/') ? p.imagem.substring(8) : p.imagem;
        card.innerHTML = `
          <img src="/static/imagens/${imagePath}" alt="${p.titulo}">
          <h3>${p.titulo}</h3>
          <p class="desc">${p.descricao}</p>
          <span class="preco">R$ ${p.preco.toFixed(2)}</span>
          <div class="produto-actions">
            ${esgotado ? '<button class="botao-comprar" style="opacity:0.5" disabled>Esgotado</button>' :
              `<button class="botao-comprar btn-add-cart" data-product-id="${p.id}">Adicionar</button>`}
            <a class="botao-comprar btn-detalhes" href="/produto/${p.id}">Detalhes</a>
          </div>
        `;
        
        // Event listener para botão adicionar
        if (!esgotado) {
          const btnAdd = card.querySelector('.btn-add-cart');
          if (btnAdd) {
            btnAdd.addEventListener('click', (e) => {
              e.stopPropagation();
              addToCart(p.id);
            });
          }
        }
        
        // Event listener para botão detalhes
        const btnDetalhes = card.querySelector('.btn-detalhes');
        if (btnDetalhes) {
          btnDetalhes.addEventListener('click', (e) => {
            e.stopPropagation();
          });
        }
        
        wrap.appendChild(card);
      });
      console.log('✅ Produtos renderizados na home!');
    })
    .catch(err => console.error('❌ Erro ao carregar produtos:', err));
});

async function addToCart(id) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const response = await fetch('/carrinho/add/' + id, { 
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    }
  });
  if (response.ok) {
    alert('✅ Produto adicionado ao carrinho!');
    location.href = '/carrinho';
  } else {
    const text = await response.text();
    if (text.includes('Esgotado')) {
      alert('❌ Produto esgotado!');
    } else if (text.includes('insuficiente')) {
      alert('⚠️ Estoque insuficiente!');
    } else {
      alert('❌ Erro ao adicionar produto!');
    }
  }
}
