const catalogState = { categoria: '', controller: null };

const byId = (id) => document.getElementById(id);

function escapeHtml(value) {
  const element = document.createElement('div');
  element.textContent = value == null ? '' : String(value);
  return element.innerHTML;
}

function formatPrice(value) {
  return Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

function imageUrl(image) {
  if (!image) return '/static/imagens/1760708557479.jpg';
  const normalized = image.startsWith('imagens/') ? image.slice(8) : image;
  return `/static/imagens/${encodeURIComponent(normalized)}`;
}

function categoryName(category) {
  return {
    mel: 'Mel',
    propolis: 'Própolis',
    'geleia-real': 'Geleia real',
    polen: 'Pólen',
    combos: 'Kit',
    outros: 'Produto apícola'
  }[category] || 'Produto apícola';
}

function usageName(value) {
  return {
    'uso-diario': 'Uso diário', bebidas: 'Bebidas', culinaria: 'Culinária',
    extrato: 'Extratos e sprays', presente: 'Presentes'
  }[value] || value;
}

function renderSkeletons() {
  byId('produtos-grid').innerHTML = Array.from({ length: 6 }, () => `
    <div class="product-skeleton" aria-hidden="true">
      <div></div><span></span><span></span><strong></strong>
    </div>
  `).join('');
}

function renderProduct(product) {
  const soldOut = Number(product.estoque) <= 0;
  const lowStock = !soldOut && Number(product.estoque) < 10;
  const benefits = Array.isArray(product.beneficios) ? product.beneficios.slice(0, 2) : [];
  const rating = Number(product.media || 0);
  const ratingText = product.n_reviews
    ? `<span class="product-rating">★ ${rating.toFixed(1)} <small>(${product.n_reviews})</small></span>`
    : '<span class="product-rating product-rating--new">Novo</span>';
  const benefitTags = benefits.map(item => `<span>${escapeHtml(usageName(item))}</span>`).join('');

  return `
    <article class="market-product-card">
      <a class="product-image-wrap" href="/produto/${product.id}" aria-label="Ver ${escapeHtml(product.titulo)}">
        <img src="${imageUrl(product.imagem)}" alt="${escapeHtml(product.titulo)}" loading="lazy">
        ${product.destaque ? '<span class="product-highlight">Destaque</span>' : ''}
        ${soldOut ? '<span class="product-sold-out">Esgotado</span>' : ''}
      </a>
      <div class="product-card-body">
        <div class="product-card-meta">
          <span>${escapeHtml(categoryName(product.categoria))}</span>
          ${ratingText}
        </div>
        <a href="/produto/${product.id}" class="product-title">${escapeHtml(product.titulo)}</a>
        ${product.origem ? `<p class="product-origin">📍 ${escapeHtml(product.origem)}</p>` : ''}
        <p class="product-description">${escapeHtml(product.descricao || 'Conheça os detalhes deste produto selecionado.')}</p>
        ${benefitTags ? `<div class="product-tags">${benefitTags}</div>` : ''}
        ${product.sem_adicao_acucar ? '<span class="sugar-note">Sem adição de açúcares*</span>' : ''}
        <div class="product-buy-row">
          <div><small>A partir de</small><strong>${formatPrice(product.preco)}</strong></div>
          <button class="quick-add" type="button" data-product-id="${product.id}" ${soldOut ? 'disabled' : ''} aria-label="Adicionar ${escapeHtml(product.titulo)} ao carrinho">
            ${soldOut ? 'Indisponível' : '<span>＋</span> Adicionar'}
          </button>
        </div>
        ${lowStock ? `<p class="low-stock">Últimas ${product.estoque} unidades</p>` : '<p class="shipping-hint">Consulte a entrega no carrinho</p>'}
      </div>
    </article>
  `;
}

function buildParams() {
  const params = new URLSearchParams();
  const values = {
    q: byId('busca').value.trim(),
    preco_min: byId('preco-min').value,
    preco_max: byId('preco-max').value,
    finalidade: byId('finalidade').value,
    categoria: catalogState.categoria,
    ordenar: byId('ordenar').value
  };

  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  if (byId('sem-acucar').checked) params.set('sem_adicao_acucar', '1');
  if (byId('disponiveis').checked) params.set('disponiveis', '1');
  return params;
}

function renderActiveFilters() {
  const filters = [];
  if (catalogState.categoria) filters.push(categoryName(catalogState.categoria));
  if (byId('finalidade').value) filters.push(byId('finalidade').selectedOptions[0].text);
  if (byId('sem-acucar').checked) filters.push('Sem adição de açúcares');
  if (byId('disponiveis').checked) filters.push('Disponíveis');
  byId('filtros-ativos').innerHTML = filters.map(label => `<span>${escapeHtml(label)}</span>`).join('');
}

async function loadProducts() {
  if (catalogState.controller) catalogState.controller.abort();
  catalogState.controller = new AbortController();
  renderSkeletons();
  renderActiveFilters();

  try {
    const response = await fetch(`/api/products/search?${buildParams()}`, {
      signal: catalogState.controller.signal
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const products = await response.json();
    const grid = byId('produtos-grid');
    const empty = byId('sem-resultados');
    grid.innerHTML = products.map(renderProduct).join('');
    grid.hidden = products.length === 0;
    empty.hidden = products.length !== 0;
    byId('resultado-contagem').textContent = `${products.length} ${products.length === 1 ? 'produto encontrado' : 'produtos encontrados'}`;

    grid.querySelectorAll('.quick-add:not(:disabled)').forEach(button => {
      button.addEventListener('click', () => addToCart(button.dataset.productId, button));
    });
  } catch (error) {
    if (error.name === 'AbortError') return;
    byId('produtos-grid').innerHTML = `
      <div class="catalog-error"><strong>Não foi possível carregar os produtos.</strong><button type="button" id="tentar-novamente">Tentar novamente</button></div>
    `;
    byId('resultado-contagem').textContent = 'Falha ao carregar';
    byId('tentar-novamente')?.addEventListener('click', loadProducts);
  }
}

function clearFilters() {
  byId('busca').value = '';
  byId('preco-min').value = '';
  byId('preco-max').value = '';
  byId('finalidade').value = '';
  byId('sem-acucar').checked = false;
  byId('disponiveis').checked = false;
  byId('ordenar').value = 'nome';
  catalogState.categoria = '';
  document.querySelectorAll('.category-chip').forEach(button => {
    button.classList.toggle('is-active', button.dataset.category === '');
  });
  loadProducts();
}

function showToast(message, type = 'success') {
  document.querySelector('.shop-toast')?.remove();
  const toast = document.createElement('div');
  toast.className = `shop-toast shop-toast--${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 2800);
}

async function addToCart(id, button) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = 'Adicionando...';
  try {
    const response = await fetch(`/carrinho/add/${id}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken }
    });
    if (!response.ok) throw new Error(await response.text());
    button.textContent = '✓ Adicionado';
    showToast('Produto adicionado ao carrinho.');
    window.setTimeout(() => {
      button.disabled = false;
      button.innerHTML = original;
    }, 1800);
  } catch (error) {
    button.disabled = false;
    button.innerHTML = original;
    showToast(error.message.includes('Esgotado') ? 'Este produto está esgotado.' : 'Não foi possível adicionar o produto.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const initialParams = new URLSearchParams(window.location.search);
  const initialQuery = initialParams.get('q');
  if (initialQuery) byId('busca').value = initialQuery;
  const initialCategory = initialParams.get('categoria') || '';
  if (document.querySelector(`.category-chip[data-category="${CSS.escape(initialCategory)}"]`)) {
    catalogState.categoria = initialCategory;
    document.querySelectorAll('.category-chip').forEach(button => {
      button.classList.toggle('is-active', button.dataset.category === initialCategory);
    });
  }
  const initialPurpose = initialParams.get('finalidade');
  if (initialPurpose && [...byId('finalidade').options].some(option => option.value === initialPurpose)) {
    byId('finalidade').value = initialPurpose;
  }
  if (initialParams.get('sem_adicao_acucar') === '1') byId('sem-acucar').checked = true;
  let searchTimer;
  byId('busca').addEventListener('input', () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(loadProducts, 280);
  });

  ['preco-min', 'preco-max', 'finalidade', 'sem-acucar', 'disponiveis', 'ordenar'].forEach(id => {
    byId(id).addEventListener('change', loadProducts);
  });

  document.querySelectorAll('.category-chip').forEach(button => {
    button.addEventListener('click', () => {
      catalogState.categoria = button.dataset.category;
      document.querySelectorAll('.category-chip').forEach(item => item.classList.remove('is-active'));
      button.classList.add('is-active');
      loadProducts();
    });
  });

  byId('btn-toggle-filtros').addEventListener('click', () => {
    const panel = byId('filtros-avancados');
    const open = panel.classList.toggle('is-open');
    byId('btn-toggle-filtros').setAttribute('aria-expanded', String(open));
    byId('filtro-icon').textContent = open ? '−' : '+';
  });

  byId('limpar-busca').addEventListener('click', () => {
    byId('busca').value = '';
    loadProducts();
  });
  byId('btn-limpar-filtros').addEventListener('click', clearFilters);
  byId('btn-empty-clear').addEventListener('click', clearFilters);
  loadProducts();
});
