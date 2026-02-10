// Toggle filtros no mobile
function toggleFiltros() {
  const filtros = document.getElementById('filtros-avancados');
  const icon = document.getElementById('filtro-icon');
  
  if (filtros.classList.contains('show')) {
    filtros.classList.remove('show');
    icon.textContent = '🔽';
  } else {
    filtros.classList.add('show');
    icon.textContent = '🔼';
  }
}

function renderDesktop(p, card) {
  const esgotado = p.estoque <= 0;
  const estoqueClass = esgotado ? 'esgotado' : (p.estoque < 10 ? 'estoque-baixo' : '');
  const imagePath = p.imagem.startsWith('imagens/') ? p.imagem.substring(8) : p.imagem;
  
  card.innerHTML = `
    <img src="/static/imagens/${imagePath}" alt="${p.titulo}">
    <h3>${p.titulo}</h3>
    <p>${p.descricao}</p>
    <span class="preco">R$ ${p.preco.toFixed(2)}</span>
    
    ${esgotado ? '<div class="badge-esgotado">❌ Esgotado</div>' : 
      (p.estoque < 10 ? `<div class="badge-estoque">⚠️ Restam apenas ${p.estoque}</div>` : 
      `<div class="badge-disponivel">✅ ${p.estoque} disponíveis</div>`)}
    
    <div class="produto-actions">
      <a class="botao-comprar" href="/produto/${p.id}">Detalhes</a>
      ${esgotado ? '<button class="botao-comprar desabilitado" disabled>Esgotado</button>' :
        `<button class="botao-comprar" onclick="addToCart(${p.id})">Adicionar</button>`}
    </div>

    <div class="meta">Avaliação: ${p.media || 0} ⭐ (${p.n_reviews})</div>
  `;
}


function renderMobile(p, card) {
  const imagePath = p.imagem.startsWith('imagens/') ? p.imagem.substring(8) : p.imagem;
  card.innerHTML = `
    <a href="/produto/${p.id}" class="card-link">
      <img src="/static/imagens/${imagePath}" alt="${p.titulo}">
      <h3>${p.titulo}</h3>
      <span class="preco">R$ ${p.preco.toFixed(2)}</span>
    </a>
  `;
}

// Função para carregar produtos com filtros
function carregarProdutos() {
  console.log('🔄 Iniciando carregamento de produtos...');
  const busca = document.getElementById('busca').value;
  const precoMin = document.getElementById('preco-min').value;
  const precoMax = document.getElementById('preco-max').value;
  const ordenar = document.getElementById('ordenar').value;
  
  // Construir URL com parâmetros
  const params = new URLSearchParams();
  if (busca) params.append('q', busca);
  if (precoMin) params.append('preco_min', precoMin);
  if (precoMax) params.append('preco_max', precoMax);
  params.append('ordenar', ordenar);
  
  const url = `/api/products/search?${params.toString()}`;
  console.log('📡 Fazendo request para:', url);
  
  fetch(url)
    .then(r => {
      console.log('✅ Resposta recebida - Status:', r.status);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data => {
      console.log('📦 Produtos recebidos:', data.length, data);
      const grid = document.getElementById('produtos-grid');
      const semResultados = document.getElementById('sem-resultados');
      
      if (!grid) {
        console.error('❌ Elemento produtos-grid não encontrado!');
        return;
      }
      
      grid.innerHTML = '';
      
      if (data.length === 0) {
        console.log('⚠️  Nenhum produto encontrado');
        grid.style.display = 'none';
        semResultados.style.display = 'block';
        return;
      }
      
      grid.style.display = 'grid';
      semResultados.style.display = 'none';
      const isMobile = window.innerWidth <= 768;
      console.log('📱 Mobile?', isMobile);

      data.forEach(p => {
        const card = document.createElement('div');
        card.className = 'card';

        if (isMobile) {
          renderMobile(p, card);
        } else {
          renderDesktop(p, card);
        }

        grid.appendChild(card);
      });
      
      console.log('✅ Produtos renderizados com sucesso!');
    })
    .catch(error => {
      console.error('❌ Erro ao carregar produtos:', error);
      const grid = document.getElementById('produtos-grid');
      if (grid) {
        grid.innerHTML = '<p style="color:red;padding:20px;">Erro ao carregar produtos. Veja o console para detalhes.</p>';
      }
    });
}

// Event listeners para busca e filtros
document.addEventListener('DOMContentLoaded', () => {
  carregarProdutos();
  
  // Busca em tempo real
  document.getElementById('busca').addEventListener('input', carregarProdutos);
  
  // Filtros
  document.getElementById('preco-min').addEventListener('change', carregarProdutos);
  document.getElementById('preco-max').addEventListener('change', carregarProdutos);
  document.getElementById('ordenar').addEventListener('change', carregarProdutos);
  
  // Toggle filtros
  document.getElementById('btn-toggle-filtros').addEventListener('click', toggleFiltros);
  
  // Limpar filtros
  document.getElementById('btn-limpar-filtros').addEventListener('click', limparFiltros);
});

function limparFiltros() {
  document.getElementById('busca').value = '';
  document.getElementById('preco-min').value = '';
  document.getElementById('preco-max').value = '';
  document.getElementById('ordenar').value = 'nome';
  carregarProdutos();
}

async function addToCart(id) {
  const response = await fetch('/carrinho/add/' + id, { method: 'POST' });
  if (response.ok) {
    alert('✅ Produto adicionado ao carrinho!');
    location.reload(); // Atualiza estoque
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
