(function(){
  // Theme preference (emoji toggle)
  const storageKey = 'theme-preference';
  const html = document.documentElement;
  const getColorPreference = () => localStorage.getItem(storageKey) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const theme = { value: getColorPreference() };
  const reflectPreference = () => {
    html.setAttribute('data-theme', theme.value);
    html.setAttribute('data-bs-theme', theme.value);
    const btn = document.getElementById('theme-toggle');
    if (btn){
      btn.setAttribute('aria-label', theme.value);
      btn.textContent = theme.value === 'dark' ? '🌑' : '☀';
    }
  };
  const setPreference = () => { localStorage.setItem(storageKey, theme.value); reflectPreference(); };
  reflectPreference();
  window.addEventListener('load', reflectPreference);
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', () => { theme.value = (theme.value === 'light') ? 'dark' : 'light'; setPreference(); });
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ({matches:isDark}) => { theme.value = isDark ? 'dark' : 'light'; setPreference(); });

  // Sidebar filtering + live search (index page)
  const searchHeader = document.getElementById('tool-search');
  const searchSidebar = document.getElementById('sidebar-search');
  const grid = document.getElementById('tools-grid');
  const items = grid ? Array.from(grid.querySelectorAll('.tool-item')) : [];
  let activeCat = 'all';
  let lastActiveSearch = searchHeader || searchSidebar || null;
  function applyFilters(){
    const src = lastActiveSearch;
    const q = (src && src.value || '').trim().toLowerCase();
    items.forEach((el) => {
      const cat = el.getAttribute('data-category');
      const txt = (el.getAttribute('data-title') + ' ' + el.getAttribute('data-desc'));
      const matchCat = (activeCat === 'all') || (cat === activeCat);
      const matchText = !q || txt.includes(q);
      el.style.display = (matchCat && matchText) ? '' : 'none';
    });
  }
  if (searchHeader && items.length){
    searchHeader.addEventListener('input', (e)=>{ lastActiveSearch = e.target; applyFilters(); });
  }
  if (searchSidebar && items.length){
    searchSidebar.addEventListener('input', (e)=>{ lastActiveSearch = e.target; applyFilters(); });
  }
  const sidebar = document.getElementById('sidebar');
  if (sidebar && items.length){
    sidebar.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-filter]');
      if(!btn) return;
      e.preventDefault();
      activeCat = btn.getAttribute('data-filter');
      sidebar.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
      btn.classList.add('active');
      applyFilters();
    });
  }

  // Sidebar search toggle
  const sidebarSearchToggle = document.getElementById('sidebar-search-toggle');
  const sidebarSearchWrap = document.getElementById('sidebar-search-wrap');
  if (sidebarSearchToggle && sidebarSearchWrap){
    sidebarSearchToggle.addEventListener('click', () => {
      const visible = sidebarSearchWrap.style.display !== 'none';
      sidebarSearchWrap.style.display = visible ? 'none' : '';
      sidebarSearchToggle.setAttribute('aria-expanded', String(!visible));
      if (!visible) {
        const input = document.getElementById('sidebar-search');
        if (input) { input.focus(); lastActiveSearch = input; }
      }
    });
  }

  // Job lifecycle: track job IDs and cleanup on unload
  const JOBS_KEY = 'neonpdf-jobs';
  function getJobs(){ try { return JSON.parse(sessionStorage.getItem(JOBS_KEY) || '[]'); } catch { return []; } }
  function setJobs(ids){ sessionStorage.setItem(JOBS_KEY, JSON.stringify(ids)); }
  window.neonpdfAddJob = function(id){ const ids = new Set(getJobs()); ids.add(id); setJobs(Array.from(ids)); }
  window.neonpdfRemoveJob = function(id){ const ids = new Set(getJobs()); ids.delete(id); setJobs(Array.from(ids)); }
  window.addEventListener('beforeunload', () => {
    const ids = getJobs();
    ids.forEach((id) => {
      try{ navigator.sendBeacon(`/api/jobs/${id}/delete`, new Blob([], {type: 'text/plain'})); } catch {}
    });
    // clear local record
    try{ sessionStorage.removeItem(JOBS_KEY); } catch {}
  });
})();
