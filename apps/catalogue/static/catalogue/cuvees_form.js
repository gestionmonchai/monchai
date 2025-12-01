(function () {
  function formatLabel(u) {
    const nom = u.nom ?? '';
    const symbole = u.symbole ? ` ${u.symbole}` : '';
    const type = u.type ? ` — ${u.type}` : '';
    const facteurRaw = (u.facteur ?? u.factor ?? '');
    const facteur = (typeof facteurRaw === 'number' || typeof facteurRaw === 'string') ? String(facteurRaw) : '';
    const fx = facteur ? ` ×${facteur}` : '';
    return `${nom}${symbole}${type}${fx}`.trim();
  }

  async function loadUnits(select) {
    const help = document.getElementById('units-help');
    const endpoint = select.getAttribute('data-units-endpoint');
    if (!endpoint) return;
    try {
      if (help) help.textContent = 'Chargement…';
      const res = await fetch(endpoint, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const items = Array.isArray(data) ? data : (data.results || []);
      // Sort alpha by nom if not guaranteed server-side
      items.sort((a, b) => (a.nom || '').localeCompare(b.nom || ''));

      // Reset options
      select.innerHTML = '';
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = '— Sélectionner —';
      select.appendChild(placeholder);

      for (const u of items) {
        if (u.id == null) continue;
        const opt = document.createElement('option');
        opt.value = String(u.id);
        opt.textContent = formatLabel(u);
        select.appendChild(opt);
      }

      // Restore selection if present
      const pre = select.getAttribute('data-selected');
      if (pre) {
        select.value = String(pre);
      }
      if (help) help.textContent = '';
    } catch (e) {
      if (help) {
        help.innerHTML = 'Échec du chargement. <button type="button" id="retry-units">Réessayer</button>';
        const btn = document.getElementById('retry-units');
        if (btn) btn.addEventListener('click', () => loadUnits(select));
      }
      // Ensure at least a placeholder exists
      if (!select.querySelector('option')) {
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = '— Sélectionner —';
        select.appendChild(placeholder);
      }
      console.error('loadUnits error:', e);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('id_default_unit');
    if (select) loadUnits(select);
  });
})();

// Advanced Unit Sense Picker
(function () {
  const DIM_RULES = [
    { dim: 'volume', kw: [/litre?s?/i, /\bcl\b/i, /\bml\b/i, /\bl\b/i, /hl/i, /volume/i, /bouteille/i, /magnum|jeroboam|rehoboam|nabuchodonosor/i] },
    { dim: 'masse', kw: [/grammes?/i, /\bg\b/i, /\bkg\b/i, /poids|masse/i] },
    { dim: 'surface', kw: [/m²|m2|hectare|ha/i] },
    { dim: 'conditionnement', kw: [/carton|caisse|palette|pack|colis/i] },
    { dim: 'unite', kw: [/^u(nité)?$/i, /^pi(e|è)ce?$/i, /\bunit/i] },
  ];
  const BOTTLE_ALIASES = [
    { name: 'Bouteille', volL: 0.75, aliases: [/^bt/i, /bouteille/i] },
    { name: 'Magnum', volL: 1.5, aliases: [/mag(num)?/i] },
    { name: 'Demi', volL: 0.375, aliases: [/demi/i, /37\.?5?cl/i] },
    { name: 'Jéroboam', volL: 3.0, aliases: [/j[ée]roboam/i] },
  ];
  const u = (s) => (s || '').toString();
  const norm = (s) => u(s).toLowerCase().normalize('NFKD').replace(/\p{Diacritic}/gu, '');

  function guessDim(unit) {
    const hay = [unit.type, unit.nom, unit.symbole].map(u).join(' ');
    for (const rule of DIM_RULES) if (rule.kw.some(rx => rx.test(hay))) return rule.dim;
    if (typeof unit.facteur === 'number' && unit.facteur > 0 && unit.facteur <= 5) return 'volume';
    return 'autre';
  }
  function formatSenseLabel(unit) {
    const nom = unit.nom ?? '';
    const symbole = unit.symbole ? ` ${unit.symbole}`  : '';
    const dim = unit.__dim || guessDim(unit);
    const fx = (unit.facteur ?? unit.factor ?? '');
    const mult = fx ? ` ×${fx}`  : '';
    return `${nom}${symbole} — ${dim}${mult}` .trim();
  }
  function parseAllowed(attr) {
    if (!attr) return null;
    return new Set(attr.split(',').map(s => s.trim().toLowerCase()).filter(Boolean));
  }

  function parseIntent(text, ctx) {
    const raw = norm(text).replace(/\s+/g, ' ').trim();
    let volL = null;
    const mVol = raw.match(/(\d+(?:[.,]\d+)?)\s*(l|cl|ml)\b/);
    if (mVol) {
      const val = parseFloat(mVol[1].replace(',', '.'));
      const unit = mVol[2];
      volL = unit === 'l' ? val : unit === 'cl' ? val / 100 : val / 1000;
    }
    for (const a of BOTTLE_ALIASES) {
      if (a.aliases.some(rx => rx.test(raw))) { volL = volL ?? a.volL; break; }
    }
    let pack = null;
    const mPack = raw.match(/(\d+)\s*[x×]\s*(bt|bouteille|magnum|carton|caisse|pack|colis)?/);
    if (mPack) pack = parseInt(mPack[1], 10);
    if (volL == null && ctx?.target_volume_l) volL = ctx.target_volume_l;
    return { volL, pack, tokens: raw };
  }

  function scoreUnit(unit, q, allowed, ctx, intent, freqScore=0, mode='unit') {
    let s = 0;
    const dim = (unit.__dim || guessDim(unit)).toLowerCase();
    const hay = norm([unit.nom, unit.symbole, unit.type, unit.name, unit.code].join(' '));
    const nq = norm(q||'');
    if (nq) {
      if (hay.startsWith(nq)) s += 8; else if (hay.includes(nq)) s += 4;
    }
    if (mode === 'unit') {
      if (allowed?.has(dim)) s += 10;
      if (nq && norm(unit.symbole) === nq) s += 6;
      const fx = typeof unit.facteur === 'number' ? unit.facteur : null;
      if (intent?.volL != null && fx != null) {
        const d = Math.abs(fx - intent.volL);
        if (d < 0.01) s += 12; else if (d < 0.05) s += 8; else if (d < 0.15) s += 4;
      } else if (ctx?.target_volume_l && fx != null) {
        const d = Math.abs(fx - ctx.target_volume_l);
        if (d < 0.01) s += 8; else if (d < 0.05) s += 4;
      }
      if ((intent?.pack || ctx?.pack_count) && dim === 'conditionnement') s += 6;
      if (ctx?.hints?.length) for (const h of ctx.hints) if (h && hay.includes(norm(h))) s += 2;
    }
    s += freqScore;
    return s;
  }

  const LS = {
    FAV: 'monchai.units.favs',
    REC: 'monchai.units.recent',
    FREQ: 'monchai.units.freq',
  };
  const readLS = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || JSON.stringify(d)); } catch { return d; } };
  const writeLS = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };
  const addRecent = (id) => { const a=readLS(LS.REC,[]); const n=[id,...a.filter(x=>x!==id)].slice(0,3); writeLS(LS.REC,n); };
  const toggleFav = (id) => { const s=new Set(readLS(LS.FAV,[])); s.has(id)?s.delete(id):s.add(id); writeLS(LS.FAV,[...s]); return s; };
  const bumpFreq = (id) => { const m=readLS(LS.FREQ,{}); m[id]=(m[id]||0)+1; writeLS(LS.FREQ,m); };

  function makeChip(label, payload){ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=label; b.dataset.payload=JSON.stringify(payload); return b; }
  function renderChips(container, items, allowed, ctx, flabel, idField) {
    container.innerHTML = '';
    const ctxChips = [];
    if (ctx?.target_volume_l) {
      const volTxt = ctx.target_volume_l === 0.75 ? 'Bouteille 75cl' :
                     ctx.target_volume_l === 1.5 ? 'Magnum 1.5L' :
                     `${ctx.target_volume_l}L` ;
      ctxChips.push(makeChip(volTxt, {q: volTxt}));
    }
    if (ctx?.pack_count) ctxChips.push(makeChip(`${ctx.pack_count}× bt` , {q: `${ctx.pack_count}x bt` }));
    const favs = new Set(readLS(LS.FAV, []));
    const rec = readLS(LS.REC, []);
    const favUnits = items.filter(u => favs.has(String(u[idField]))).slice(0,2).map(u => makeChip(`⭐ ${flabel(u)}` , {id:String(u[idField])}));
    const recUnits = items.filter(u => rec.includes(String(u[idField]))).slice(0,2).map(u => makeChip(`Réc. ${flabel(u)}` , {id:String(u[idField])}));
    const out = [...ctxChips, ...favUnits, ...recUnits].slice(0,4);
    out.forEach(ch => container.appendChild(ch));
  }

  async function loadUnits(endpoint, itemsKey) {
    const res = await fetch(endpoint, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    let data = await res.json();
    let items = Array.isArray(data) ? data : (itemsKey ? (data?.[itemsKey] || []) : (data.results || data.items || []));
    items = items.map(u => ({ ...u, __dim: guessDim(u) }));
    items.sort((a,b)=> (a.nom||a.name||'').localeCompare(b.nom||b.name||''));
    return items;
  }
  function renderLI(unit, isFav, isRecent, flabel) {
    const li = document.createElement('li');
    li.setAttribute('role','option');
    li.dataset.id = String(unit.id);
    li.innerHTML = `
      <span class="cbx-label">${flabel(unit)}</span>
      <span class="cbx-badges">
        ${isRecent ? '<span class="cbx-badge">réc.</span>' : ''}
        <button type="button" class="cbx-fav" aria-label="Basculer favori" title="Favori">☆</button>
      </span>`;
    return li;
  }

  function sniffContext(root, ctx) {
    let out = {...ctx};
    try {
      const sniff = JSON.parse(root.getAttribute('data-sniff')||'null');
      if (sniff?.capacity_selector) {
        const el = document.querySelector(sniff.capacity_selector);
        const val = el?.value?.replace(',', '.');
        const num = val ? parseFloat(val) : NaN;
        if (!isNaN(num) && num>0 && num<10) out.target_volume_l = num;
      }
      if (sniff?.pack_selector) {
        const elp = document.querySelector(sniff.pack_selector);
        const num = elp ? parseInt(elp.value,10) : NaN;
        if (!isNaN(num) && num>0 && num<100) out.pack_count = num;
      }
    } catch {}
    return out;
  }

  function attachSensePicker(root) {
    const input  = root.querySelector('input[role="combobox"]');
    const list   = root.querySelector('[role="listbox"]');
    const help   = root.querySelector('.cbx-help') || root.querySelector('#units-help');
    const sinkSelect = root.querySelector('select[hidden][name]');
    const sinkInput  = root.querySelector('input[type="hidden"][name]');
    const sink = sinkSelect || sinkInput; // element that will carry the value for POST
    const chips  = root.querySelector('.cbx-chips');
    const endpoint = root.getAttribute('data-endpoint');
    const allowed  = parseAllowed(root.getAttribute('data-allowed'));
    const mode     = (root.getAttribute('data-mode') || 'unit').toLowerCase();
    const itemsKey = root.getAttribute('data-items-key') || '';
    const idField  = root.getAttribute('data-id-field') || 'id';
    const tpl      = root.getAttribute('data-label-template') || '';
    let ctx = null; try { ctx = JSON.parse(root.getAttribute('data-context')||'null'); } catch {}
    ctx = sniffContext(root, ctx);

    let items = [];
    let filtered = [];
    let open=false, idx=-1;

    const favs = () => new Set(readLS(LS.FAV, []));
    const recs = () => readLS(LS.REC, []);
    const freqs = () => readLS(LS.FREQ, {});

    function openList(){ list.hidden=false; input.setAttribute('aria-expanded','true'); open=true; }
    function closeList(){ list.hidden=true; input.setAttribute('aria-expanded','false'); open=false; idx=-1; }
    function setActive(i){
      const lis = Array.from(list.querySelectorAll('li[role="option"]'));
      lis.forEach((el,k)=> el.setAttribute('aria-selected', k===i?'true':'false')); idx=i;
      if (i>=0 && lis[i]) lis[i].scrollIntoView({block:'nearest'});
    }
    function ensureOptionForSelect(val, label) {
      if (!sinkSelect) return;
      let opt = Array.from(sinkSelect.options).find(o => String(o.value) === String(val));
      if (!opt) {
        opt = new Option(label || String(val), String(val), true, true);
        sinkSelect.add(opt);
      } else {
        sinkSelect.value = String(val);
      }
    }

    function commit(id,label){
      if (sinkSelect) {
        ensureOptionForSelect(id, label);
      } else if (sink) {
        sink.value = id || '';
      }
      input.value = label||'';
      if (id) { addRecent(id); bumpFreq(id); }
      closeList();
    }

    // label builder
    const flabel = (u) => {
      if (mode === 'unit' && !tpl) return formatSenseLabel(u);
      // simple template replacement {field}
      if (tpl) return tpl.replace(/\{(\w+)\}/g, (_, k) => (u?.[k] ?? ''));
      return u.name || u.nom || u.code || String(u[idField]||'');
    };

    function rebuild(q){
      const intent = mode === 'unit' ? parseIntent(q, ctx) : null;
      const F = freqs();
      const scoreWrap = items.map(u => {
        const freqScore = Math.min((F[String(u[idField])]||0), 20);
        return { u, s: scoreUnit(u, q, allowed, ctx, intent, freqScore, mode) };
      }).sort((a,b)=> b.s - a.s);

      filtered = scoreWrap.map(x=>x.u);
      list.innerHTML='';
      const favSet = favs(), rec = recs();
      filtered.slice(0,12).forEach(u=>{
        const li = renderLI(u, favSet.has(String(u[idField])), rec.includes(String(u[idField])), flabel);
        list.appendChild(li);
      });
      list.querySelectorAll('.cbx-fav').forEach(btn=>{
        btn.addEventListener('click', (ev)=>{
          ev.stopPropagation();
          const li = btn.closest('li[role="option"]');
          const id = li?.dataset.id;
          const fs = toggleFav(String(id));
          btn.textContent = fs.has(String(id)) ? '⭐' : '☆';
          renderChips(chips, items, allowed, ctx);
        });
      });

      openList(); setActive(filtered.length?0:-1);
    }

    (async ()=>{
      try{
        help && (help.textContent='Chargement…');
        items = await loadUnits(endpoint, itemsKey);
        help && (help.textContent='');
        renderChips(chips, items, allowed, ctx, flabel, idField);
        const pre = sink ? (sink.getAttribute('data-selected') || sink.value) : '';
        if (pre) {
          const found = items.find(u => String(u[idField])===String(pre));
          if (found) commit(String(found[idField]), mode === 'unit' ? formatSenseLabel(found) : flabel(found));
        }
      } catch(e){
        console.error(e);
        help && (help.innerHTML='Échec du chargement. <button type="button" id="retry-units">Réessayer</button>');
        document.getElementById('retry-units')?.addEventListener('click', ()=>location.reload());
      }
    })();

    chips.addEventListener('click',(e)=>{
      const b = e.target.closest('.chip'); if (!b) return;
      const payload = JSON.parse(b.dataset.payload||'{}');
      if (payload.id) {
        const found = items.find(u => String(u[idField])===String(payload.id));
        if (found) commit(String(found[idField]), flabel(found));
      } else if (payload.q) {
        input.value = payload.q;
        rebuild(payload.q);
        input.focus();
      }
    });

    input.addEventListener('focus', ()=> rebuild(input.value));
    input.addEventListener('input', ()=> rebuild(input.value));
    input.addEventListener('keydown', (e)=>{
      const opts = Array.from(list.querySelectorAll('li[role="option"]'));
      if (e.key==='ArrowDown'){ e.preventDefault(); if(!open) openList(); setActive(Math.min(idx+1, opts.length-1)); }
      else if (e.key==='ArrowUp'){ e.preventDefault(); setActive(Math.max(idx-1,0)); }
      else if (e.key==='Enter'){
        if (open && idx>=0 && opts[idx]) {
          e.preventDefault();
          const li=opts[idx]; commit(li.dataset.id, li.querySelector('.cbx-label')?.textContent||'');
        }
      } else if (e.key==='Escape'){ closeList(); }
    });
    list.addEventListener('mousedown', (e)=>{
      const li = e.target.closest('li[role="option"]'); if (!li) return;
      commit(li.dataset.id, li.querySelector('.cbx-label')?.textContent||'');
    });
    document.addEventListener('click', (e)=>{ if(!root.contains(e.target)) closeList(); });

    const resniff = () => { ctx = sniffContext(root, ctx); renderChips(chips, items, allowed, ctx); rebuild(input.value); };
    const sniffCfg = root.getAttribute('data-sniff');
    if (sniffCfg) {
      try {
        const cfg = JSON.parse(sniffCfg);
        [cfg.capacity_selector, cfg.pack_selector].flat().filter(Boolean).forEach(sel=>{
          const el = document.querySelector(sel);
          el && el.addEventListener('input', resniff);
          el && el.addEventListener('change', resniff);
        });
      } catch {}
    }
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.cbx--sense').forEach(attachSensePicker);
  });
})();
