document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('overlay');
  const sideMenu = document.getElementById('side-menu');
  let cartPanel = document.getElementById('cart-panel');
  const cartCountEl = document.getElementById('cart-count');
  const loginModal = document.getElementById('login-modal');
  const loginModalBody = document.getElementById('login-modal-body');
  const toastRoot = document.getElementById('toast-root');

  // --- Animación suave para el badge (sin tocar HTML) ---
  if (cartCountEl) {
    cartCountEl.style.transition = 'transform .15s ease, opacity .15s ease';
  }

  // ===== Toasts con Tailwind (sin CSS custom) =====
  function showToast({ title = '', message = '', type = 'info', timeout = 2600 } = {}) {
    if (!toastRoot) return;

    const variants = {
      success: 'bg-emerald-700/95 border-emerald-500 text-white',
      error:   'bg-red-700/95 border-red-500 text-white',
      info:    'bg-neutral-900/95 border-neutral-700 text-white'
    };
    const icons = { success: '✔', error: '✖', info: 'ℹ' };
    const cls = variants[type] || variants.info;
    const icon = icons[type] || icons.info;

    const wrap = document.createElement('div');
    wrap.setAttribute('role', 'status');
    wrap.className = [
      'pointer-events-auto w-full max-w-sm',
      'rounded-2xl border shadow-lg backdrop-blur',
      'grid grid-cols-[1.25rem_1fr_auto] gap-2 items-start',
      'px-4 py-3',
      'opacity-0 translate-y-2',
      'transition ease-out duration-150',
      cls
    ].join(' ');

    wrap.innerHTML = `
      <div class="text-base leading-none mt-0.5">${icon}</div>
      <div>
        ${title ? `<p class="font-bold text-sm sm:text-base">${title}</p>` : ''}
        ${message ? `<p class="text-xs sm:text-sm/5 opacity-90 mt-0.5">${message}</p>` : ''}
      </div>
      <button type="button" class="text-white/80 hover:text-white text-lg leading-none px-1 select-none" aria-label="Cerrar notificación">×</button>
    `;

    const close = () => {
      wrap.classList.add('opacity-0', 'translate-y-2');
      wrap.classList.remove('opacity-100', 'translate-y-0');
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      if (mq.matches) {
        wrap.remove();
      } else {
        wrap.addEventListener('transitionend', () => wrap.remove(), { once: true });
      }
    };

    // ⬇️ Importante: no dejar que el click burbujee al delegador global
    wrap.querySelector('button').addEventListener('click', (ev) => {
      ev.stopPropagation();
      close();
    });

    toastRoot.appendChild(wrap);

    requestAnimationFrame(() => {
      wrap.classList.remove('opacity-0', 'translate-y-2');
      wrap.classList.add('opacity-100', 'translate-y-0');
    });

    if (timeout > 0) setTimeout(close, timeout);
    return { close };
  }

  // ===== Helpers =====
  const $html = document.documentElement;
  const $body = document.body;

  function lockScroll() {
    $html.classList.add('no-scroll');
    $body.classList.add('no-scroll');
  }
  function unlockScroll() {
    $html.classList.remove('no-scroll');
    $body.classList.remove('no-scroll');
  }
  function setAria(el, open) {
    if (!el) return;
    el.setAttribute('aria-hidden', open ? 'false' : 'true');
  }
  function getNavbarHeight() {
    const navbar = document.getElementById('navbar');
    return navbar ? navbar.offsetHeight : 0;
  }

  async function safeFetch(url, opts = {}, options = { errorToast: true }) {
    try {
      const res = await fetch(url, opts);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return res;
    } catch (err) {
      console.error('Fetch error:', err);
      if (options.errorToast) {
        showToast({ type: 'error', title: 'Error de red', message: 'No se pudo completar la acción. Intenta de nuevo.' });
      }
      throw err;
    }
  }

  // ===== Paneles =====
  function openSide() {
    sideMenu?.classList.add('open');
    overlay?.classList.add('show');
    setAria(sideMenu, true);
    lockScroll();
  }
  function closeSide() {
    sideMenu?.classList.remove('open');
    overlay?.classList.remove('show');
    setAria(sideMenu, false);
    unlockScroll();
  }
  function openCart() {
    cartPanel?.classList.add('open');
    overlay?.classList.add('show');
    setAria(cartPanel, true);
    lockScroll();
  }
  function closeCart() {
    cartPanel?.classList.remove('open');
    overlay?.classList.remove('show');
    setAria(cartPanel, false);
    unlockScroll();
  }
  function openLogin() {
    loginModal?.classList.remove('hidden');
    overlay?.classList.add('show');
    setAria(loginModal, true);
    lockScroll();
    const focusable = loginModal?.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
    focusable?.focus();
  }
  function closeLogin() {
    loginModal?.classList.add('hidden');
    overlay?.classList.remove('show');
    setAria(loginModal, false);
    unlockScroll();
  }

  // Mantiene el panel ABIERTO y preserva el scroll al refrescar
  async function refreshCartPanel() {
    const html = await (await safeFetch('/carrito/panel')).text();

    const wasOpen = cartPanel?.classList.contains('open');
    const prevScroll = cartPanel?.querySelector('#cart-list')?.scrollTop ?? 0;

    const temp = document.createElement('div');
    temp.innerHTML = html;
    const newPanel = temp.querySelector('#cart-panel');

    if (newPanel && cartPanel) {
      cartPanel.replaceWith(newPanel);
      cartPanel = newPanel;

      if (wasOpen) {
        cartPanel.classList.add('open');
        cartPanel.setAttribute('aria-hidden', 'false');
        const list = cartPanel.querySelector('#cart-list');
        if (list) list.scrollTop = prevScroll;
      }
    }
  }

  // devuelve el número actualizado y anima el badge
  async function refreshCartBadge() {
    try {
      const res = await safeFetch('/carrito/qty');
      let qty;

      const ct = (res.headers.get('content-type') || '').toLowerCase();
      if (ct.includes('application/json')) {
        const data = await res.json();
        qty = (typeof data === 'number') ? data : (data.qty ?? 0);
      } else {
        const txt = await res.text();
        qty = parseInt(txt, 10);
        if (Number.isNaN(qty)) {
          try { qty = JSON.parse(txt).qty ?? 0; } catch { qty = 0; }
        }
      }

      if (cartCountEl) {
        cartCountEl.textContent = qty;
        cartCountEl.classList.toggle('hidden', qty <= 0);
        if (qty > 0) {
          cartCountEl.classList.add('scale-110');            // animación
          setTimeout(() => cartCountEl.classList.remove('scale-110'), 150);
        }
      }
      return qty;
    } catch (_) {
      return 0;
    }
  }

  // ===== Scroll suave a secciones (hash links) =====
  function smoothScrollToHash(hash) {
    if (!hash || hash === '#') return;
    const target = document.querySelector(hash);
    if (!target) return;
    const top = target.getBoundingClientRect().top + window.scrollY - (getNavbarHeight() + 8);
    window.scrollTo({ top, behavior: 'smooth' });
  }

  // Click en enlaces internos: cerrar menú + scroll suave
  document.body.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (href && href.startsWith('#')) {
      e.preventDefault();
      closeSide();
      smoothScrollToHash(href);
    }
  });

  // ===== Delegación de clicks =====
  document.body.addEventListener('click', async (e) => {
    const t = e.target.closest('button, a, [data-action]');
    if (!t) return;

    // Menú
    if (t.id === 'menu-btn') { e.preventDefault(); openSide(); return; }
    if (t.id === 'close-side') { e.preventDefault(); closeSide(); return; }

    // Carrito
    if (t.id === 'open-cart') {
      e.preventDefault();
      await refreshCartPanel();
      openCart();
      return;
    }
    if (t.id === 'close-cart-panel') { e.preventDefault(); closeCart(); return; }

    // Vaciar carrito (POST al endpoint real y cerrar si queda en 0)
    if (t.id === 'clear-cart') {
      e.preventDefault();
      const form = document.getElementById('clear-cart-form');
      if (form) {
        await safeFetch(form.action || '/carrito/clear', { method: 'POST' });
        await refreshCartPanel();
        const qty = await refreshCartBadge();
        showToast({ type: 'info', title: 'Carrito', message: 'Se vació el carrito.' });
        if (qty === 0) closeCart();
      }
      return;
    }

    // Cambiar cantidad (+/-): POST al formulario real
    if (t.dataset?.action === 'qty') {
      e.preventDefault();
      const form = t.closest('form'); // .cart-qty-form
      if (!form) return;
      await safeFetch(form.action, { method: 'POST', body: new FormData(form) });
      await refreshCartPanel();
      const qty = await refreshCartBadge();
      showToast({ type: 'success', title: 'Cantidad actualizada' });
      if (qty === 0) closeCart();
      return;
    }

    // Eliminar item
    if (t.dataset?.action === 'remove') {
      e.preventDefault();
      const form = t.closest('form'); // .cart-remove-form
      if (!form) return;
      await safeFetch(form.action, { method: 'POST' });
      await refreshCartPanel();
      const qty = await refreshCartBadge();
      showToast({ type: 'info', title: 'Producto eliminado' });
      if (qty === 0) closeCart();
      return;
    }

    // Submenú
    if (t.dataset?.action === 'toggle-submenu' && t.dataset.target) {
      e.preventDefault();
      const el = document.getElementById(t.dataset.target);
      if (el) el.classList.toggle('hidden');
      return;
    }

    // Carrusel
    if (t.dataset?.action === 'scroll') {
      const wrap = t.closest('.carousel-wrap');
      const track = wrap?.querySelector('.carousel-track');
      const dir = parseInt(t.dataset.dir, 10) || 1;
      if (track) {
        track.scrollBy({ left: dir * Math.round(track.clientWidth * 0.6), behavior: 'smooth' });
      }
      return;
    }

    // Login modal
    if (t.id === 'open-login') {
      e.preventDefault();
      const html = await (await safeFetch('/auth/login?partial=1')).text();
      loginModalBody.innerHTML = html;
      openLogin();
      return;
    }
    if (t.id === 'close-login') { e.preventDefault(); closeLogin(); return; }
  });

  // ===== Bloqueo de submit accidental en forms del panel =====
  document.addEventListener('submit', async (e) => {
    const qtyForm = e.target.closest('.cart-qty-form');
    const rmForm  = e.target.closest('.cart-remove-form');
    const clrForm = e.target.closest('#clear-cart-form');

    if (!qtyForm && !rmForm && !clrForm) return; // los demás submits siguen normal
    e.preventDefault();

    if (qtyForm) {
      await safeFetch(qtyForm.action, { method: 'POST', body: new FormData(qtyForm) });
      await refreshCartPanel();
      await refreshCartBadge();
      return;
    }
    if (rmForm) {
      await safeFetch(rmForm.action, { method: 'POST' });
      await refreshCartPanel();
      await refreshCartBadge();
      showToast({ type: 'info', title: 'Producto eliminado' });
      return;
    }
    if (clrForm) {
      await safeFetch(clrForm.action, { method: 'POST' });
      await refreshCartPanel();
      await refreshCartBadge();
      showToast({ type: 'info', title: 'Carrito', message: 'Se vació el carrito.' });
      return;
    }
  });

  // ===== Añadir al carrito (server) =====
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('.add-to-cart-form');
    if (!form) return;
    e.preventDefault();

    const productName =
      form.dataset.productName ||
      form.closest('.product-card')?.querySelector('h3')?.textContent?.trim() ||
      '';

    const submitBtn = form.querySelector('button[type="submit"], .btn');
    const prevDisabled = submitBtn?.disabled;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.7'; }

    try {
      await safeFetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' }
      });
      await Promise.all([refreshCartPanel(), refreshCartBadge()]);
      openCart();
      showToast({ type: 'success', title: 'Añadido al carrito', message: productName });
    } finally {
      if (submitBtn) { submitBtn.disabled = prevDisabled ?? false; submitBtn.style.opacity = ''; }
    }
  });

  // ===== Overlay & ESC =====
  overlay.addEventListener('click', () => { closeSide(); closeLogin(); closeCart(); });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { closeSide(); closeLogin(); closeCart(); }
  });

  // ===== Hash inicial (si llega con #seccion) =====
  if (window.location.hash) {
    setTimeout(() => smoothScrollToHash(window.location.hash), 0);
  }
});