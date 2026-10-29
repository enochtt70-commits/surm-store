/* =========================================================
   Surm Store - Main JavaScript
   ========================================================= */

// ── Flash message auto-dismiss ──────────────────────────────
document.querySelectorAll('.alert[data-dismiss]').forEach(el => {
  setTimeout(() => el.remove(), parseInt(el.dataset.dismiss) || 5000);
});

// ── User dropdown toggle ─────────────────────────────────────
const userBtn  = document.getElementById('userBtn');
const userMenu = document.getElementById('userMenu');
if (userBtn && userMenu) {
  userBtn.addEventListener('click', e => {
    e.stopPropagation();
    userMenu.classList.toggle('hidden');
  });
  document.addEventListener('click', () => userMenu.classList.add('hidden'));
}

// ── Sidebar toggle (mobile) ──────────────────────────────────
const menuToggle = document.getElementById('menuToggle');
const sidebar    = document.getElementById('sidebar');
if (menuToggle && sidebar) {
  menuToggle.addEventListener('click', e => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
  });
  document.addEventListener('click', e => {
    if (sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        e.target !== menuToggle) {
      sidebar.classList.remove('open');
    }
  });
}

// ── Mark active sidebar link ─────────────────────────────────
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  const href = link.getAttribute('href');
  if (href && href !== '/' && window.location.pathname.startsWith(href)) {
    link.classList.add('active');
  } else if (href === '/' && window.location.pathname === '/') {
    link.classList.add('active');
  }
});

// ── Confirm dialogs ──────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ── Currency formatter ───────────────────────────────────────
function formatCurrency(amount, symbol = 'GHS') {
  const n = parseFloat(amount);
  if (isNaN(n)) return symbol + ' 0.00';
  return symbol + ' ' + n.toLocaleString('en-GH', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// ── POS System ───────────────────────────────────────────────
class POSSystem {
  constructor() {
    this.cart    = [];
    this.vatRate = parseFloat(document.getElementById('vat-rate')?.value || 0);
    this.applyTax = false;
    this.init();
  }

  init() {
    this.renderCart();
    this.bindEvents();
    this.setupSearch();
  }

  bindEvents() {
    document.getElementById('apply-tax')?.addEventListener('change', e => {
      this.applyTax = e.target.checked;
      this.renderCart();
    });
    document.getElementById('extra-discount')?.addEventListener('input', () => this.renderCart());
    document.getElementById('amount-paid')?.addEventListener('input', () => this.updateChange());
    document.getElementById('checkout-btn')?.addEventListener('click', () => this.checkout());
    document.getElementById('clear-cart')?.addEventListener('click', () => {
      if (confirm('Clear all items from cart?')) { this.cart = []; this.renderCart(); }
    });
  }

  setupSearch() {
    const inp = document.getElementById('product-search');
    if (!inp) return;
    let timer;
    inp.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => this.searchProducts(inp.value.trim()), 250);
    });
    // close results when clicking outside
    document.addEventListener('click', e => {
      if (!inp.contains(e.target)) {
        const r = document.getElementById('search-results');
        if (r) r.innerHTML = '';
      }
    });
  }

  async searchProducts(q) {
    const results = document.getElementById('search-results');
    if (!results) return;
    if (q.length < 1) { results.innerHTML = ''; return; }
    try {
      const res  = await fetch('/products/search-json?q=' + encodeURIComponent(q));
      const list = await res.json();
      if (!list.length) {
        results.innerHTML = '<div class="search-result-item" style="color:#6b7280;cursor:default">No products found</div>';
        return;
      }
      results.innerHTML = list.map(p => {
        const safeName = p.name.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        const safeUnit = p.unit.replace(/'/g,"\\'");
        return '<div class="search-result-item" onclick="pos.addToCart(' +
          p.id + ',\'' + safeName + '\',' + p.price + ',\'' + safeUnit + '\',' + p.stock + ')">' +
          '<div><strong>' + p.name + '</strong> <small style="color:#6b7280">' + p.sku + '</small></div>' +
          '<div style="display:flex;justify-content:space-between;margin-top:.2rem">' +
          '<small style="color:#6b7280">Stock: ' + p.stock + ' ' + p.unit + '</small>' +
          '<span style="font-weight:600;color:#2563eb">' + formatCurrency(p.price) + '</span>' +
          '</div></div>';
      }).join('');
    } catch(err) {
      console.error('Product search error:', err);
      results.innerHTML = '<div class="search-result-item" style="color:#dc2626">Search error</div>';
    }
  }

  addToCart(id, name, price, unit, stock) {
    // id comes in as number from onclick attribute
    const existing = this.cart.find(i => i.id === id);
    if (existing) {
      if (existing.qty < stock) { existing.qty++; }
      else { alert('Only ' + stock + ' ' + unit + '(s) in stock'); return; }
    } else {
      if (stock <= 0) { alert('Product is out of stock'); return; }
      this.cart.push({ id, name, price, unit, stock, qty: 1, discount: 0 });
    }
    const results = document.getElementById('search-results');
    const inp     = document.getElementById('product-search');
    if (results) results.innerHTML = '';
    if (inp)     inp.value = '';
    this.renderCart();
  }

  removeFromCart(id) {
    this.cart = this.cart.filter(i => i.id !== id);
    this.renderCart();
  }

  updateQty(id, qty) {
    const item = this.cart.find(i => i.id === id);
    if (!item) return;
    qty = Math.max(1, Math.min(parseInt(qty) || 1, item.stock));
    item.qty = qty;
    this.renderCart();
  }

  renderCart() {
    const container = document.getElementById('cart-items');
    if (!container) return;

    if (this.cart.length === 0) {
      container.innerHTML = '<div class="text-center text-muted" style="padding:2rem;color:#9ca3af"><i class="fas fa-shopping-cart" style="font-size:2rem;display:block;margin-bottom:.5rem"></i>Cart is empty</div>';
    } else {
      container.innerHTML = this.cart.map(item => {
        const lineTotal = item.price * item.qty;
        return '<div class="cart-item">' +
          '<div style="flex:1;min-width:0">' +
          '<div class="fw-600 fs-sm" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + item.name + '</div>' +
          '<div class="text-muted fs-sm">' + formatCurrency(item.price) + ' / ' + item.unit + '</div>' +
          '</div>' +
          '<div style="display:flex;gap:.25rem;align-items:center;flex-shrink:0">' +
          '<button class="btn btn-secondary btn-sm" onclick="pos.updateQty(' + item.id + ',' + (item.qty-1) + ')">&#8722;</button>' +
          '<input type="number" value="' + item.qty + '" min="1" max="' + item.stock + '" style="width:44px;text-align:center;padding:.2rem .3rem" class="form-control" onchange="pos.updateQty(' + item.id + ',this.value)">' +
          '<button class="btn btn-secondary btn-sm" onclick="pos.updateQty(' + item.id + ',' + (item.qty+1) + ')">&#43;</button>' +
          '<button class="btn btn-danger btn-sm" onclick="pos.removeFromCart(' + item.id + ')">&times;</button>' +
          '</div>' +
          '<div style="min-width:72px;text-align:right;font-weight:600;font-size:.8rem;flex-shrink:0">' + formatCurrency(lineTotal) + '</div>' +
          '</div>';
      }).join('');
    }

    const subtotal      = this.cart.reduce((s, i) => s + i.price * i.qty, 0);
    const extraDiscount = parseFloat(document.getElementById('extra-discount')?.value || 0);
    const tax           = this.applyTax ? subtotal * this.vatRate : 0;
    const total         = Math.max(0, subtotal + tax - extraDiscount);

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('subtotal-display',  formatCurrency(subtotal));
    set('tax-display',       formatCurrency(tax));
    set('discount-display',  formatCurrency(extraDiscount));
    set('total-display',     formatCurrency(total));
    const hidden = document.getElementById('cart-total-hidden');
    if (hidden) hidden.value = total.toFixed(2);
    this.updateChange();
  }

  updateChange() {
    const paid   = parseFloat(document.getElementById('amount-paid')?.value || 0);
    const total  = parseFloat(document.getElementById('cart-total-hidden')?.value || 0);
    const change = paid - total;
    const el     = document.getElementById('change-display');
    if (!el) return;
    el.textContent = formatCurrency(Math.max(0, change));
    el.style.color = change < 0 ? '#dc2626' : '#16a34a';
  }

  checkout() {
    if (this.cart.length === 0) { alert('Cart is empty — add products first'); return; }
    const itemsEl = document.getElementById('items-json');
    const formEl  = document.getElementById('sale-form');
    if (!itemsEl || !formEl) return;
    itemsEl.value = JSON.stringify(this.cart.map(i => ({
      product_id: i.id,
      quantity:   i.qty,
      unit_price: i.price,
      discount:   i.discount
    })));
    formEl.submit();
  }
}

// Initialise POS on the new sale page
if (document.getElementById('sale-form')) {
  window.pos = new POSSystem();
}

// ── Table column sort ─────────────────────────────────────────
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.style.cursor = 'pointer';
  th.title = 'Click to sort';
  th.addEventListener('click', () => {
    const table = th.closest('table');
    const col   = Array.from(th.parentElement.children).indexOf(th);
    const asc   = th.dataset.dir !== 'asc';
    document.querySelectorAll('th[data-sort]').forEach(t => delete t.dataset.dir);
    th.dataset.dir = asc ? 'asc' : 'desc';
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.sort((a, b) => {
      const va = a.cells[col]?.textContent.trim() || '';
      const vb = b.cells[col]?.textContent.trim() || '';
      return asc
        ? va.localeCompare(vb, undefined, {numeric: true})
        : vb.localeCompare(va, undefined, {numeric: true});
    });
    const tbody = table.querySelector('tbody');
    rows.forEach(r => tbody.appendChild(r));
  });
});
