(function(){
  function getCsrfToken(){
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function scrollIntoViewIfNeeded(el){
    if (!el) return Promise.resolve();
    const rect = el.getBoundingClientRect();
    const inView = rect.top >= 80 && rect.bottom <= (window.innerHeight - 80);
    if (inView) return Promise.resolve();
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return new Promise(res => setTimeout(res, 250));
  }

  function placePopover(pop, rect, placement){
    const gap = 14;
    let top = 0, left = 0;
    pop.setAttribute('data-placement', placement);
    
    const pw = pop.offsetWidth;
    const ph = pop.offsetHeight;
    const ww = window.innerWidth;
    const wh = window.innerHeight;

    // Center horizontally/vertically by default
    if (placement === 'bottom' || placement === 'top'){
      left = rect.left + (rect.width / 2) - (pw / 2);
      // Clamp to viewport
      left = Math.max(12, Math.min(ww - pw - 12, left));
      
      if (placement === 'bottom') top = rect.bottom + gap;
      else top = rect.top - ph - gap;
      
    } else {
      // left / right
      top = rect.top + (rect.height / 2) - (ph / 2);
      // Clamp to viewport
      top = Math.max(12, Math.min(wh - ph - 12, top));
      
      if (placement === 'right') left = rect.right + gap;
      else left = rect.left - pw - gap;
    }

    pop.style.top = `${top}px`;
    pop.style.left = `${left}px`;
    
    // Adjust arrow position if popover was clamped
    // (Simple approach: stick to center for now, CSS handles it)
  }

  function computePlacement(rect){
    const spaceBottom = window.innerHeight - rect.bottom;
    const spaceTop = rect.top;
    const spaceRight = window.innerWidth - rect.right;
    const spaceLeft = rect.left;
    
    // Favor bottom/top for mobile/wide items
    if (spaceBottom > 250) return 'bottom';
    if (spaceTop > 250) return 'top';
    
    if (spaceRight > 300) return 'right';
    if (spaceLeft > 300) return 'left';
    
    return 'bottom'; // fallback
  }

  function fmtHtml(text){
    return text;
  }

  function create(ops){
    const steps = (ops.steps || []).filter(s => !!s && !!s.target);
    let index = 0;
    let spotlight, pop, onScroll, onResize, currentTargetEl = null;

    function ensureElements(){
      if (!spotlight){
        // Backdrop blocks clicks outside the spotlight
        const backdrop = document.getElementById('tour-backdrop') || document.createElement('div');
        backdrop.id = 'tour-backdrop';
        if (!backdrop.parentNode) document.body.appendChild(backdrop);
        spotlight = document.createElement('div');
        spotlight.id = 'tour-spotlight';
        document.body.appendChild(spotlight);
        try { document.body.classList.add('tour-active'); } catch(e) {}
      }
      if (!pop){
        pop = document.createElement('div');
        pop.id = 'tour-popover';
        pop.innerHTML = `
          <div class="tour-title"></div>
          <div class="tour-content"></div>
          <div class="tour-actions">
            <button class="tour-btn tour-btn-outline" data-act="prev">Précédent</button>
            <button class="tour-btn tour-btn-outline" data-act="stop">Arrêter</button>
            <button class="tour-btn tour-btn-primary" data-act="next">Suivant</button>
          </div>
        `;
        document.body.appendChild(pop);
        pop.addEventListener('click', async (e)=>{
          const btn = e.target.closest('button[data-act]');
          if (!btn) return;
          const act = btn.getAttribute('data-act');
          if (act === 'prev') prev();
          if (act === 'next') next();
          if (act === 'stop') {
            try { if (window.MonChaiTourFlow && typeof window.MonChaiTourFlow.stopFlow === 'function') window.MonChaiTourFlow.stopFlow(); } catch(e) {}
            stop(false);
            return;
          }
        });
      }
    }

    function cleanup(){
      if (spotlight && spotlight.parentNode) spotlight.parentNode.removeChild(spotlight);
      if (pop && pop.parentNode) pop.parentNode.removeChild(pop);
      const backdrop = document.getElementById('tour-backdrop');
      if (backdrop && backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
      spotlight = null; pop = null;
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      try { document.body.classList.remove('tour-active'); } catch(e) {}
    }

    async function show(){
      ensureElements();
      const s = steps[index];
      const el = document.querySelector(s.target);
      if (!el){
        // Step target not found: skip forward; if none left, stop
        const hadNext = index < steps.length - 1;
        if (hadNext){ index++; return show(); }
        return stop(true);
      }
      await scrollIntoViewIfNeeded(el);
      const rect = el.getBoundingClientRect();
      
      // Spotlight with padding
      const pad = 6;
      const hl = {
        top: rect.top - pad,
        left: rect.left - pad,
        width: rect.width + (pad*2),
        height: rect.height + (pad*2)
      };
      spotlight.style.top = `${hl.top}px`;
      spotlight.style.left = `${hl.left}px`;
      spotlight.style.width = `${hl.width}px`;
      spotlight.style.height = `${hl.height}px`;

      currentTargetEl = el;
      pop.querySelector('.tour-title').textContent = s.title || '';
      pop.querySelector('.tour-content').innerHTML = fmtHtml(s.content || '');
      
      // Actions logic
      pop.setAttribute('data-first-step', index === 0);
      pop.setAttribute('data-last-step', index === steps.length - 1);
      
      const nextBtn = pop.querySelector('[data-act="next"]');
      nextBtn.textContent = (index === steps.length - 1) ? 'Terminer' : 'Suivant';

      const placement = computePlacement(rect);
      placePopover(pop, rect, placement);

      // bind update on scroll/resize
      onScroll = () => {
        const r = el.getBoundingClientRect();
        const pad2 = 6;
        const hl2 = {
          top: r.top - pad2,
          left: r.left - pad2,
          width: r.width + (pad2*2),
          height: r.height + (pad2*2)
        };
        spotlight.style.top = `${hl2.top}px`;
        spotlight.style.left = `${hl2.left}px`;
        spotlight.style.width = `${hl2.width}px`;
        spotlight.style.height = `${hl2.height}px`;
        placePopover(pop, r, computePlacement(r));
      };
      onResize = onScroll;
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onResize);
    }

    function start(){ index = 0; show(); return api; }
    function next(){
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      if (index < steps.length - 1){ index++; show(); }
      else { stop(true); }
    }
    function prev(){
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      if (index > 0){ index--; show(); }
    }
    function skip(){
      if (typeof ops.onSkip === 'function') ops.onSkip();
      else {
        // Default: POST to dismiss onboarding
        fetch('/onboarding/dismiss/', { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } }).finally(()=>{
          stop(false);
        });
      }
    }
    function stop(finished){
      cleanup();
      if (finished && typeof ops.onFinish === 'function') ops.onFinish();
    }

    const api = { start, next, prev, skip, stop };
    return api;
  }

  window.MonChaiTour = { create };

  // --- Cross-page flow orchestrator ---
  function pathMatches(url){
    if (!url) return true;
    try {
      const a = document.createElement('a');
      a.href = url;
      const want = a.pathname;
      const cur = window.location.pathname;
      return cur === want || cur.startsWith(want.replace(/\/$/, '') + '/');
    } catch(e){ return false; }
  }

  function resumeFlow(flow){
    try {
      const active = localStorage.getItem('mc_tour_flow_active');
      if (!active) return;
      const idx = parseInt(localStorage.getItem('mc_tour_flow_index') || '0', 10);
      runAtIndex(flow, isNaN(idx) ? 0 : idx);
    } catch(e) {}
  }

  function startFlow(flow){
    try {
      localStorage.setItem('mc_tour_flow_active', '1');
      localStorage.setItem('mc_tour_flow_index', '0');
    } catch(e) {}
    runAtIndex(flow, 0);
  }

  function stopFlow(){
    try {
      localStorage.removeItem('mc_tour_flow_active');
      localStorage.removeItem('mc_tour_flow_index');
    } catch(e) {}
    try { window.__mc_flow_advance_index = null; } catch(e) {}
  }

  function runAtIndex(flow, idx){
    const steps = flow || [];
    if (idx < 0 || idx >= steps.length){ stopFlow(); return; }
    const step = steps[idx];
    // If not on the right page, navigate except when user is on a form-like page (nouveau/modifier)
    if (step.url && !pathMatches(step.url)){
      const cur = window.location.pathname || '';
      const onFormLikePage = /(\/|^)(nouveau|modifier|edit|create)(\/|$)/.test(cur);
      if (onFormLikePage){
        try { localStorage.setItem('mc_tour_flow_index', String(idx)); } catch(e) {}
        return; // pause here; user will continue later
      }
      try { localStorage.setItem('mc_tour_flow_index', String(idx)); } catch(e) {}
      window.location.href = step.url;
      return;
    }
    // Expose a helper so the popover "Ouvrir" can advance the flow before navigating
    try {
      window.__mc_flow_advance_index = function(){
        try {
          const next = idx + 1;
          localStorage.setItem('mc_tour_flow_index', String(next));
          localStorage.setItem('mc_tour_flow_active', '1');
        } catch(e) {}
      };
    } catch(e) {}
    // On the right page: ensure element exists or wait briefly
    const tryShow = (attempts) => {
      const el = document.querySelector(step.target);
      if (el){
        const t = create({
          steps: [{ target: step.target, title: step.title, content: step.content }],
          onFinish: () => {
            const next = idx + 1;
            try { localStorage.setItem('mc_tour_flow_index', String(next)); } catch(e) {}
            if (next < steps.length) runAtIndex(flow, next);
            else stopFlow();
          },
        });
        t.start();
      } else if (attempts < 20){
        setTimeout(() => tryShow(attempts + 1), 150);
      } else {
        // If element never appears, skip to next step
        const next = idx + 1;
        if (next < steps.length) runAtIndex(flow, next); else stopFlow();
      }
    };
    tryShow(0);
  }

  window.MonChaiTourFlow = { startFlow, resumeFlow, stopFlow };
})();
