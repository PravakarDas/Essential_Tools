(() => {
  const storageKey = 'theme-preference';
  const html = document.documentElement;
  const body = document.body;

  const getColorPreference = () => {
    return localStorage.getItem(storageKey) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  };

  const theme = { value: getColorPreference() };

  const reflectPreference = () => {
    html.setAttribute('data-theme', theme.value);
    html.setAttribute('data-bs-theme', theme.value);
  };

  const setPreference = () => {
    localStorage.setItem(storageKey, theme.value);
    reflectPreference();
  };

  reflectPreference();
  window.addEventListener('load', reflectPreference);

  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      theme.value = theme.value === 'light' ? 'dark' : 'light';
      setPreference();
    });
  }

  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  prefersDark.addEventListener('change', ({ matches: isDark }) => {
    theme.value = isDark ? 'dark' : 'light';
    setPreference();
  });

  const sidebar = document.getElementById('app-sidebar');
  const openNavBtn = document.getElementById('nav-toggle');
  const closeNavBtn = document.getElementById('nav-close');

  const openSidebar = () => {
    if (!sidebar) return;
    sidebar.classList.add('is-open');
    body.classList.add('sidebar-open');
  };

  const closeSidebar = () => {
    if (!sidebar) return;
    sidebar.classList.remove('is-open');
    body.classList.remove('sidebar-open');
  };

  if (openNavBtn) openNavBtn.addEventListener('click', openSidebar);
  if (closeNavBtn) closeNavBtn.addEventListener('click', closeSidebar);
  body.addEventListener('click', (event) => {
    if (!body.classList.contains('sidebar-open')) return;
    if (!sidebar) return;
    if (sidebar.contains(event.target) || (openNavBtn && openNavBtn.contains(event.target))) return;
    closeSidebar();
  });

  const searchInput = document.getElementById('tool-search');
  const grid = document.getElementById('tools-grid');
  const items = grid ? Array.from(grid.querySelectorAll('.tool-item')) : [];

  let activeCategory = 'all';
  let activeSort = null;
  const getQuery = () => (searchInput ? searchInput.value.trim().toLowerCase() : '');

  const applyFilters = () => {
    if (!items.length) return;
    const query = getQuery();
    items.forEach((item) => {
      const category = item.getAttribute('data-category') || '';
      const text = `${item.getAttribute('data-title') || ''} ${(item.getAttribute('data-desc') || '')}`;
      const matchesCategory = activeCategory === 'all' || category === activeCategory;
      const matchesText = !query || text.includes(query);
      item.style.display = matchesCategory && matchesText ? '' : 'none';
    });
  };

  const sortItems = () => {
    if (!grid || !items.length) return;
    const sorted = [...items];
    if (activeSort === 'az' || activeSort === 'za') {
      sorted.sort((a, b) => {
        const titleA = (a.getAttribute('data-title') || '').localeCompare((b.getAttribute('data-title') || ''), undefined, { sensitivity: 'base' });
        return activeSort === 'az' ? titleA : -titleA;
      });
    } else if (activeSort === 'new') {
      sorted.sort((a, b) => parseInt(b.dataset.index || '0', 10) - parseInt(a.dataset.index || '0', 10));
    } else {
      sorted.sort((a, b) => parseInt(a.dataset.index || '0', 10) - parseInt(b.dataset.index || '0', 10));
    }
    sorted.forEach((el) => grid.appendChild(el));
  };

  if (searchInput) searchInput.addEventListener('input', () => applyFilters());

  const categoryButtons = sidebar ? Array.from(sidebar.querySelectorAll('[data-filter]')) : [];
  categoryButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.filter || 'all';
      categoryButtons.forEach((chip) => chip.classList.toggle('is-active', chip === btn));
      applyFilters();
      if (window.innerWidth <= 1024) closeSidebar();
    });
  });

  const sortButtons = sidebar ? Array.from(sidebar.querySelectorAll('[data-sort]')) : [];
  sortButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const sort = btn.dataset.sort;
      if (sort === 'clear') {
        activeSort = null;
        sortButtons.forEach((chip) => chip.classList.remove('is-active'));
      } else {
        activeSort = sort;
        sortButtons.forEach((chip) => {
          if (chip.dataset.sort !== 'clear') chip.classList.toggle('is-active', chip === btn);
        });
      }
      sortItems();
      applyFilters();
      if (window.innerWidth <= 1024) closeSidebar();
    });
  });

  sortItems();
  applyFilters();

  const JOBS_KEY = 'essential-tools-jobs';
  const getJobs = () => {
    try { return JSON.parse(sessionStorage.getItem(JOBS_KEY) || '[]'); }
    catch { return []; }
  };
  const setJobs = (ids) => sessionStorage.setItem(JOBS_KEY, JSON.stringify(ids));

  window.essentialToolsAddJob = function(id){
    const ids = new Set(getJobs());
    ids.add(id);
    setJobs(Array.from(ids));
  };

  window.essentialToolsRemoveJob = function(id){
    const ids = new Set(getJobs());
    ids.delete(id);
    setJobs(Array.from(ids));
  };

  window.addEventListener('beforeunload', () => {
    const ids = getJobs();
    ids.forEach((id) => {
      try { navigator.sendBeacon(`/api/jobs/${id}/delete`, new Blob([], { type: 'text/plain' })); }
      catch { /* noop */ }
    });
    try { sessionStorage.removeItem(JOBS_KEY); } catch { /* noop */ }
  });
})();

