const detailCategoryNames = {
  mel: 'Mel', propolis: 'Própolis', 'geleia-real': 'Geleia real',
  polen: 'Pólen', combos: 'Kit e combo', outros: 'Produto apícola'
};

const detailUsageNames = {
  'uso-diario': 'Uso diário', bebidas: 'Bebidas', culinaria: 'Culinária',
  extrato: 'Extratos e sprays', presente: 'Presentes'
};

function detailImage(image) {
  if (!image) return '/static/imagens/1760708557479.jpg';
  const normalized = image.startsWith('imagens/') ? image.slice(8) : image;
  return `/static/imagens/${encodeURIComponent(normalized)}`;
}

function detailToast(message, error = false) {
  document.querySelector('.shop-toast')?.remove();
  const toast = document.createElement('div');
  toast.className = `shop-toast${error ? ' shop-toast--error' : ''}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 2600);
}

function showProduct(product) {
  const image = document.getElementById('imagem-produto');
  image.src = detailImage(product.imagem);
  image.alt = product.titulo;
  image.onerror = () => { image.src = '/static/imagens/1760708557479.jpg'; };

  document.getElementById('titulo-produto').textContent = product.titulo;
  document.getElementById('breadcrumb-produto').textContent = product.titulo;
  document.getElementById('categoria-produto').textContent = detailCategoryNames[product.categoria] || 'Produto apícola';
  document.getElementById('preco-produto').textContent = Number(product.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  document.getElementById('descricao-produto').textContent = product.descricao || 'Consulte a loja para saber mais sobre este produto.';

  const origin = document.getElementById('origem-produto');
  if (product.origem) {
    origin.textContent = `📍 Origem: ${product.origem}`;
    origin.hidden = false;
  }

  const stock = document.getElementById('estoque-produto');
  const soldOut = Number(product.estoque) <= 0;
  stock.textContent = soldOut ? 'Esgotado' : (product.estoque < 10 ? `Últimas ${product.estoque} unidades` : 'Em estoque');
  stock.classList.toggle('is-sold-out', soldOut);

  const tags = (product.beneficios || []).map(item => detailUsageNames[item] || item);
  if (product.sem_adicao_acucar) tags.push('Sem adição de açúcares*');
  document.getElementById('tags-produto').replaceChildren(...tags.map(text => {
    const tag = document.createElement('span');
    tag.textContent = text;
    return tag;
  }));

  const reviews = product.reviews || [];
  const average = reviews.length ? reviews.reduce((sum, review) => sum + Number(review.nota), 0) / reviews.length : 0;
  document.getElementById('resumo-avaliacoes').textContent = reviews.length
    ? `★ ${average.toFixed(1)} · ${reviews.length} ${reviews.length === 1 ? 'avaliação' : 'avaliações'}`
    : 'Novo produto · sem avaliações';

  ['btn-add-cart', 'btn-finalizar'].forEach(id => {
    const button = document.getElementById(id);
    button.disabled = soldOut;
    if (soldOut) button.textContent = 'Produto esgotado';
  });
  showReviews(reviews);
}

function showReviews(reviews) {
  const list = document.getElementById('reviews-list');
  list.replaceChildren();
  if (!reviews.length) {
    const empty = document.createElement('div');
    empty.className = 'reviews-empty';
    empty.innerHTML = '<span>☆</span><strong>Este produto ainda não tem avaliações</strong><p>Depois da compra, clientes podem compartilhar a experiência aqui.</p>';
    list.appendChild(empty);
    return;
  }

  reviews.forEach(review => {
    const card = document.createElement('article');
    card.className = 'review-card';
    const header = document.createElement('div');
    const name = document.createElement('strong');
    const rating = document.createElement('span');
    const comment = document.createElement('p');
    name.textContent = review.nome;
    rating.textContent = `${'★'.repeat(Number(review.nota))}${'☆'.repeat(5 - Number(review.nota))}`;
    comment.textContent = review.comentario;
    header.append(name, rating);
    card.append(header, comment);
    list.appendChild(card);
  });
}

async function detailAddToCart(id, redirectToCheckout, button) {
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
    if (redirectToCheckout) {
      window.location.href = '/checkout';
      return;
    }
    detailToast('Produto adicionado ao carrinho.');
    button.textContent = '✓ Adicionado';
    window.setTimeout(() => { button.disabled = false; button.textContent = original; }, 1700);
  } catch (_) {
    button.disabled = false;
    button.textContent = original;
    detailToast('Não foi possível adicionar o produto.', true);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const page = document.querySelector('.product-page');
  const productId = page?.dataset.productId;
  if (!productId) return;

  document.querySelector('.btn-ver-avaliacoes')?.addEventListener('click', () => {
    document.getElementById('produto-reviews').scrollIntoView({ behavior: 'smooth' });
  });
  document.getElementById('btn-add-cart').addEventListener('click', event => detailAddToCart(productId, false, event.currentTarget));
  document.getElementById('btn-finalizar').addEventListener('click', event => detailAddToCart(productId, true, event.currentTarget));

  try {
    const response = await fetch(`/api/product/${productId}`);
    if (!response.ok) throw new Error();
    showProduct(await response.json());
  } catch (_) {
    document.getElementById('titulo-produto').textContent = 'Não foi possível carregar o produto';
    document.getElementById('descricao-produto').textContent = 'Tente atualizar a página ou volte ao catálogo.';
  }
});
