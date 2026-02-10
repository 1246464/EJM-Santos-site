// Atualiza UI com os dados do produto
function showProduct(p) {
  console.log('Dados do produto:', p);
  
  // Atualiza imagem
  const imgElement = document.getElementById("imagem-produto");
  if (p.imagem) {
    // Remove "imagens/" do início se já existir para evitar duplicação
    const imagePath = p.imagem.startsWith('imagens/') ? p.imagem.substring(8) : p.imagem;
    imgElement.src = "/static/imagens/" + imagePath;
    imgElement.onerror = function() {
      console.error('Erro ao carregar imagem:', p.imagem);
      this.src = "/static/imagens/placeholder.jpg";
    };
  }
  
  document.getElementById("titulo-produto").textContent = p.titulo;
  document.getElementById("preco-produto").textContent = "R$ " + p.preco.toFixed(2);
  document.getElementById("descricao-produto").textContent = p.descricao;
}
}

// Comprar agora
async function buyNow(id) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const response = await fetch('/carrinho/add/' + id, { 
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    }
  });
  if (response.ok) {
    window.location.href = '/checkout';
  } else {
    alert('❌ Erro ao adicionar ao carrinho.');
  }
}

// Rolar até avaliações
function scrollToReviews() {
  document.getElementById('produto-reviews').scrollIntoView({ behavior: "smooth" });
}

// Carrinho
async function addToCart(id) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const response = await fetch('/carrinho/add/' + id, { 
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    }
  });
  if (response.ok) {
    alert('✅ Adicionado ao carrinho!');
  } else {
    alert('❌ Erro ao adicionar ao carrinho.');
  }
}

// Avaliações
function showReviews(list) {
  const c = document.getElementById('produto-reviews');
  c.innerHTML = '<h3>Avaliações</h3>';
  if (!list || list.length === 0) {
    c.innerHTML += '<p>Nenhuma avaliação ainda.</p>';
    return;
  }
  list.forEach(r => {
    const div = document.createElement('div');
    div.className = "comentario";
    div.innerHTML = `<strong>${r.nome}</strong> • ${r.nota} ⭐<br><span>${r.comentario}</span>`;
    c.appendChild(div);
  });
}

// Event listener para botão ver avaliações
document.addEventListener('DOMContentLoaded', () => {
  const btnVerAvaliacoes = document.querySelector('.btn-ver-avaliacoes');
  if (btnVerAvaliacoes) {
    btnVerAvaliacoes.addEventListener('click', scrollToReviews);
  }
  
  // Obter productId do data attribute
  const produtoDetalhe = document.querySelector('.produto-detalhe');
  const productId = produtoDetalhe ? produtoDetalhe.dataset.productId : null;
  
  // Event listeners para botões de ação
  const btnAddCart = document.getElementById("btn-add-cart");
  const btnFinalizar = document.getElementById("btn-finalizar");
  
  if (btnAddCart && productId) {
    btnAddCart.addEventListener('click', () => addToCart(productId));
  }
  
  if (btnFinalizar && productId) {
    btnFinalizar.addEventListener('click', () => buyNow(productId));
  }
  
  // Inicializa produto
  if (productId) {
    fetch(`/api/product/${productId}`)
      .then(r => r.json())
      .then(data => {
        console.log('Resposta da API:', data);
        showProduct(data);
        showReviews(data.reviews || []);
      })
      .catch(error => {
        console.error('Erro ao carregar produto:', error);
      });
  }
});
