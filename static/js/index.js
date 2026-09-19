function homeEscape(value) {
  const element = document.createElement('div');
  element.textContent = value == null ? '' : String(value);
  return element.innerHTML;
}

function homePrice(value) {
  return Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function homeImage(image) {
  if (!image) return '/static/imagens/1760708557479.jpg';
  const normalized = image.startsWith('imagens/') ? image.slice(8) : image;
  return `/static/imagens/${encodeURIComponent(normalized)}`;
}

function homeCard(product) {
  const soldOut = Number(product.estoque) <= 0;
  const rating = product.n_reviews
    ? `<span>★ ${Number(product.media || 0).toFixed(1)} (${product.n_reviews})</span>`
    : '<span class="new-product">Novo</span>';
  return `
    <article class="home-product-card">
      <a href="/produto/${product.id}" class="home-product-card__image">
        <img src="${homeImage(product.imagem)}" alt="${homeEscape(product.titulo)}" loading="lazy">
        ${product.destaque ? '<b>Destaque</b>' : ''}
      </a>
      <div class="home-product-card__body">
        <div class="home-product-card__meta">${rating}<small>${homeEscape(product.origem || '')}</small></div>
        <a href="/produto/${product.id}" class="home-product-card__title">${homeEscape(product.titulo)}</a>
        <strong class="home-product-card__price">${homePrice(product.preco)}</strong>
        <button type="button" class="home-add-button" data-product-id="${product.id}" ${soldOut ? 'disabled' : ''}>
          ${soldOut ? 'Indisponível' : 'Adicionar ao carrinho'}
        </button>
      </div>
    </article>
  `;
}

function homeToast(message, error = false) {
  document.querySelector('.shop-toast')?.remove();
  const toast = document.createElement('div');
  toast.className = `shop-toast${error ? ' shop-toast--error' : ''}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 2600);
}

async function homeAddToCart(id, button) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const original = button.textContent;
  button.disabled = true;
  button.textContent = 'Adicionando...';
  try {
    const response = await fetch(`/carrinho/add/${id}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken }
    });
    if (!response.ok) throw new Error();
    button.textContent = '✓ Adicionado';
    homeToast('Produto adicionado ao carrinho.');
    window.setTimeout(() => { button.disabled = false; button.textContent = original; }, 1600);
  } catch (_) {
    button.disabled = false;
    button.textContent = original;
    homeToast('Não foi possível adicionar o produto.', true);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const grid = document.getElementById('produtos-destaque');
  if (!grid) return;
  grid.innerHTML = '<p class="home-loading">Carregando produtos selecionados...</p>';

  try {
    let response = await fetch('/api/products/search?destaque=1&ordenar=nome');
    if (!response.ok) throw new Error();
    let products = await response.json();
    if (!products.length) {
      response = await fetch('/api/products/search?ordenar=nome');
      if (!response.ok) throw new Error();
      products = await response.json();
    }

    if (!products.length) {
      grid.innerHTML = '<div class="home-empty"><strong>Novidades chegando</strong><p>Em breve você encontrará nossa seleção aqui.</p><a href="/produtos">Visitar o catálogo</a></div>';
      return;
    }

    grid.innerHTML = products.slice(0, 6).map(homeCard).join('');
    grid.querySelectorAll('.home-add-button:not(:disabled)').forEach(button => {
      button.addEventListener('click', () => homeAddToCart(button.dataset.productId, button));
    });
  } catch (_) {
    grid.innerHTML = '<div class="home-empty"><strong>Não foi possível carregar os produtos.</strong><p>Tente novamente em alguns instantes.</p></div>';
  }
});
