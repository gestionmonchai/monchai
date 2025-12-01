(function(){
  const mapEl = document.getElementById('map');
  if (!mapEl) return;

  // Basemap style with 3 raster sources and layers; toggle visibility
  const style = {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      },
      cartoLight: {
        type: 'raster',
        tiles: ['https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap, © CARTO'
      },
      esriWorldImagery: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: 'Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community'
      }
    },
    layers: [
      { id: 'bm-osm', type: 'raster', source: 'osm' },
      { id: 'bm-cartoLight', type: 'raster', source: 'cartoLight', layout: { visibility: 'none' } },
      { id: 'bm-esri', type: 'raster', source: 'esriWorldImagery', layout: { visibility: 'none' } }
    ]
  };

  // PLU color mapping
  const PLU_COLORS = {
    U: '#f44336',     // Urban
    AU: '#ff9800',    // A urbaniser
    A: '#4caf50',     // Agricole
    N: '#8bc34a',     // Naturelle
    AUTRES: '#0080ff' // fallback
  };

  function getPLUColorExpr(){
    // color = match(coalesce(get('typezone'), slice(to-string(get('codezone')),0,2)), ... )
    return ['match',
      ['coalesce', ['upcase', ['to-string', ['get','typezone']]], ['slice', ['upcase', ['to-string', ['get','codezone']]], 0, 2]],
      'U', PLU_COLORS.U,
      'AU', PLU_COLORS.AU,
      'A', PLU_COLORS.A,
      'N', PLU_COLORS.N,
      PLU_COLORS.AUTRES
    ];
  }

  function zoneTypeFromProps(props){
    if (!props) return 'AUTRES';
    const tz = (props.typezone || props.TYPEZONE || props.typ || '').toString().toUpperCase();
    if (tz){ if (tz.startsWith('AU')) return 'AU'; const c = tz.charAt(0); if (['U','A','N'].includes(c)) return c; }
    const cz = (props.codezone || props.CODEZONE || '').toString().toUpperCase();
    if (cz){ if (cz.startsWith('AU')) return 'AU'; const c = cz.charAt(0); if (['U','A','N'].includes(c)) return c; }
    return 'AUTRES';
  }

  function updateLegendFromFC(fc){
    try {
      const panel = document.getElementById('legendPanel'); if (!panel) return;
      const set = new Map();
      (fc.features||[]).forEach(f=>{ const t = zoneTypeFromProps(f.properties); set.set(t, (set.get(t)||0)+1); });
      let html = '';
      Array.from(set.keys()).sort().forEach(k=>{
        const c = PLU_COLORS[k] || PLU_COLORS.AUTRES; const label = k==='AUTRES'?'Autres':k;
        html += `<div class="d-flex align-items-center mb-2"><span class="legend-color" style="background:${c};"></span> PLU – ${label}</div>`;
      });
      if (!html) html = `<div class="text-muted">Aucune zone visible</div>`;
      panel.innerHTML = html;
    } catch(e){}
  }

  const map = new maplibregl.Map({
    container: 'map',
    style,
    center: [-1.68, 48.11],
    zoom: 12
  });
  map.addControl(new maplibregl.NavigationControl(), 'top-right');

  // UI elements
  const $loading = document.getElementById('loadingMask');
  const $coordBar = document.getElementById('coordBar');

  // Draw controls
  let Draw = null;
  function getDrawCtor(){
    return window.MaplibreGlDraw || window.MapLibreGlDraw || window.MaplibreDraw || window.MapLibreDraw || window.MapboxDraw || null;
  }
  function initDraw(){
    const Ctor = getDrawCtor();
    if (!Ctor) return;
    Draw = new Ctor({ displayControlsDefault:false, controls:{ polygon:true, line_string:true, trash:true } });
    map.addControl(Draw, 'top-left');
    map.on('draw.create', updateMeasure);
    map.on('draw.update', updateMeasure);
    map.on('draw.delete', updateMeasure);
  }

  // Debounce helper
  function debounce(fn, wait){ let t; return function(){ const ctx=this, args=arguments; clearTimeout(t); t=setTimeout(()=>fn.apply(ctx,args), wait); } }

  function bboxFromMap(){
    const b = map.getBounds();
    return [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  }

  // Loading mask
  function showLoading(){ if ($loading) $loading.classList.remove('d-none'); }
  function hideLoading(){ if ($loading) $loading.classList.add('d-none'); }

  // Scale bar (custom)
  function updateScale(){
    const el = document.getElementById('scaleBar');
    const inner = document.getElementById('scaleInner');
    const label = document.getElementById('scaleLabel');
    if (!el || !inner || !label) return;
    const center = map.getCenter();
    const z = map.getZoom();
    const metersPerPixel = (40075016.686 * Math.cos(center.lat * Math.PI / 180)) / (Math.pow(2, z) * 256);
    const targetPx = 120;
    let meters = metersPerPixel * targetPx;
    // round meters to 1/2/5 * 10^n
    const pow10 = Math.pow(10, Math.floor(Math.log10(meters)));
    const norm = meters / pow10;
    let nice = 1;
    if (norm < 2) nice = 1; else if (norm < 5) nice = 2; else nice = 5;
    const niceMeters = nice * pow10;
    const px = niceMeters / metersPerPixel;
    inner.style.width = `${px}px`;
    if (niceMeters >= 1000) label.textContent = `${(niceMeters/1000).toFixed(niceMeters>=5000?0:1)} km`;
    else label.textContent = `${Math.round(niceMeters)} m`;
  }

  // Coordinates
  function updateCoords(e){
    if (!$coordBar) return;
    const p = e && e.lngLat ? e.lngLat : map.getCenter();
    $coordBar.textContent = `${p.lng.toFixed(5)}, ${p.lat.toFixed(5)}`;
  }

  // Permalink state
  function readHash(){
    const h = (location.hash||'').replace(/^#/, '');
    const params = new URLSearchParams(h);
    const out = {};
    params.forEach((v,k)=>{ out[k]=v; });
    return out;
  }
  function writeHash(state){
    const p = new URLSearchParams();
    Object.keys(state).forEach(k=>{ if(state[k]!==undefined && state[k]!=='' && state[k]!==null) p.set(k, state[k]); });
    const hash = p.toString();
    const url = location.pathname + (hash ? ('#'+hash) : '');
    history.replaceState(null, '', url);
    const a = document.getElementById('permalink');
    if (a) a.href = url;
  }

  // Basemap toggling
  function setBasemap(bm){
    // bm values stored in state/radios: 'osm' | 'light' | 'ortho'
    const target = bm === 'light' ? 'cartoLight' : (bm === 'ortho' ? 'esri' : 'osm');
    const ids = ['bm-osm','bm-cartoLight','bm-esri'];
    ids.forEach(id => map.setLayoutProperty(id, 'visibility', id==='bm-'+target ? 'visible' : 'none'));
  }

  // Parcel search
  async function searchParcel(insee, section, numero){
    try {
      showLoading();
      const u = `/api/cadastre/parcel?insee=${encodeURIComponent(insee)}&section=${encodeURIComponent(section)}&numero=${encodeURIComponent(numero)}`;
      let fc = await fetch(u).then(r=>r.ok?r.json():Promise.reject());
      if(!fc.features || !fc.features.length){
        fc = await fetch(u+`&fallback=1`).then(r=>r.ok?r.json():{features:[]}).catch(()=>({features:[]}));
      }
      if(!fc.features || !fc.features.length){ toast('Aucune géométrie'); return; }
      const f = fc.features[0];
      if (!map.getSource('parcel')) map.addSource('parcel',{type:'geojson', data: f});
      else map.getSource('parcel').setData(f);
      addParcelLayersIfNeeded();
      const bb = turf.bbox(f);
      map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]], {padding: 24});
      highlightFeature(f);
      state.parcel = `${insee}:${section}:${numero}`;
      writeHash(state);
    } catch(e){ console.error(e); toast('Erreur recherche parcelle'); }
    finally { hideLoading(); }
  }
  function addParcelLayersIfNeeded(){
    if (!map.getLayer('parcel-fill')){
      map.addLayer({id:'parcel-fill', type:'fill', source:'parcel', paint:{'fill-color':'#e91e63','fill-opacity':0.2}});
      map.addLayer({id:'parcel-line', type:'line', source:'parcel', paint:{'line-color':'#e91e63','line-width':2}});
    }
  }

  // PLU overlay
  let pluOn = false; let debPLU; let pluReqId = 0;
  async function refreshPLU(){
    if(!pluOn) return;
    const bbox = bboxFromMap();
    try {
      showLoading();
      const reqId = ++pluReqId;
      const fc = await fetch(`/api/plu/zones?bbox=${bbox.join(',')}`).then(r=>r.ok?r.json():Promise.reject());
      if (reqId !== pluReqId) return; // stale
      if (!map.getSource('plu')) map.addSource('plu',{type:'geojson', data: fc});
      else map.getSource('plu').setData(fc);
      addPLULayersIfNeeded();
      updateLegendFromFC(fc);
    } catch(e){ console.warn('PLU indisponible', e); }
    finally { hideLoading(); }
  }
  function addPLULayersIfNeeded(){
    if (!map.getLayer('plu-fill')){
      map.addLayer({id:'plu-fill', type:'fill', source:'plu', paint:{'fill-color': getPLUColorExpr(), 'fill-opacity':pluOpacity()}},
                   getFirstSymbolLayerId());
      map.addLayer({id:'plu-line', type:'line', source:'plu', paint:{'line-color':'#004c99','line-width':1}});
    }
  }
  function pluOpacity(){ const s = document.getElementById('pluOpacity'); return s ? parseFloat(s.value||'0.15') : 0.15; }

  // WMS overlay via iframe
  let wmsOn = false; let debWMS;
  function updateWMS(){
    if (!wmsOn) return;
    const bbox = bboxFromMap();
    const frame = document.getElementById('cadastreWmsFrame');
    const src = `/embed/cadastre-wms?bbox=${bbox.join(',')}`;
    try { if (frame && frame.contentWindow) frame.contentWindow.postMessage(JSON.stringify({type:'set-bbox', bbox}), '*'); else if(frame) frame.src = src; }
    catch(e){ if (frame) frame.src = src; }
  }

  // Address geocoding
  const $addrQ = document.getElementById('addrQ');
  const $addrResults = document.getElementById('addrResults');
  async function runGeocode(q){
    try {
      const res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}&limit=8`).then(r=>r.ok?r.json():Promise.reject());
      const feats = res && res.features || [];
      $addrResults.innerHTML = '';
      feats.forEach((f, idx) => {
        const label = (f.properties && f.properties.label) || `Résultat ${idx+1}`;
        const a = document.createElement('a');
        a.href = '#'; a.className = 'list-group-item list-group-item-action'; a.textContent = label;
        a.addEventListener('click', (ev)=>{ ev.preventDefault(); zoomToFeature(f); state.q = q; writeHash(state); });
        $addrResults.appendChild(a);
      });
    } catch(e){ console.error(e); }
  }
  function zoomToFeature(f){
    try {
      if (Array.isArray(f.bbox)){
        const bb = f.bbox; map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]], {padding: 20}); return;
      }
      const g = f.geometry; if (!g) return;
      if (g.type === 'Point'){
        const c = g.coordinates; map.flyTo({center:[c[0],c[1]], zoom: 16}); return;
      }
      const bb = turf.bbox(f); map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]], {padding: 20});
    } catch(e){}
  }

  // Click info
  const $info = document.getElementById('infoPanel');
  function setInfo(html){ if ($info) $info.innerHTML = html; }
  function showInfoFromFeatures(feats){
    if (!feats || !feats.length){ setInfo('<div class="text-muted">Aucune entité visible ici.</div>'); return; }
    let html = '';
    feats.forEach(f => {
      const id = f.id || f.properties && (f.properties.id || f.properties.ID || f.properties.gid) || '';
      const lib = f.properties && (f.properties.libelle || f.properties.lib_zone || f.properties.nom || '') || '';
      html += `<div class="mb-2"><div class="small text-muted">${f.layer && f.layer.id || 'Layer'}</div><div><strong>${lib||'Entité'}</strong> ${id?`<span class="text-muted">#${id}</span>`:''}</div></div>`;
    });
    setInfo(html);
  }
  map.on('click', (e)=>{
    const layers = [];
    if (map.getLayer('plu-fill')) layers.push('plu-fill');
    if (map.getLayer('parcel-fill')) layers.push('parcel-fill');
    const feats = layers.length ? map.queryRenderedFeatures(e.point, { layers }) : [];
    showInfoFromFeatures(feats);
    if (feats && feats[0]){
      highlightFeature(feats[0]);
    } else {
      clearHighlight();
    }
    // copy coords
    try { const txt = `${e.lngLat.lng.toFixed(5)},${e.lngLat.lat.toFixed(5)}`; navigator.clipboard?.writeText(txt); toast('Coordonnées copiées'); } catch(_){}
  });

  // Highlight management
  function addHighlightLayersIfNeeded(){
    if (!map.getLayer('hl-fill')){
      map.addSource('hl', {type:'geojson', data:{type:'FeatureCollection', features:[]}});
      map.addLayer({id:'hl-fill', type:'fill', source:'hl', paint:{'fill-color':'#ffeb3b','fill-opacity':0.25}}, getFirstSymbolLayerId());
      map.addLayer({id:'hl-line', type:'line', source:'hl', paint:{'line-color':'#ffc107','line-width':3}});
    }
  }
  function highlightFeature(f){
    addHighlightLayersIfNeeded();
    try {
      const feat = { type:'Feature', properties:{}, geometry: f.geometry || f._geometry || null };
      if (!feat.geometry) return;
      map.getSource('hl').setData({type:'FeatureCollection', features:[feat]});
    } catch(e){}
  }
  function clearHighlight(){ try { if (map.getSource('hl')) map.getSource('hl').setData({type:'FeatureCollection', features:[]}); } catch(e){} }

  // Measure bar
  function updateMeasure(){
    const bar = document.getElementById('measureBar'); if (!bar || !Draw) return;
    const fc = Draw.getAll(); if (!fc.features || !fc.features.length){ bar.textContent=''; return; }
    let totalLen = 0, totalArea = 0;
    fc.features.forEach(feat => {
      if (feat.geometry && feat.geometry.type === 'LineString'){
        totalLen += turf.length(feat, {units:'meters'}) * 1000; // km→m
      } else if (feat.geometry && feat.geometry.type === 'Polygon'){
        totalArea += turf.area(feat); // m²
      }
    });
    const parts = [];
    if (totalLen>0) parts.push(`Longueur: ${totalLen.toFixed(1)} m`);
    if (totalArea>0) parts.push(`Surface: ${(totalArea/10000).toFixed(2)} ha`);
    bar.textContent = parts.join(' — ');
  }

  // Helpers
  function toast(msg){ try{ const d=document.createElement('div'); d.className='alert alert-info position-fixed top-0 end-0 m-3'; d.textContent=msg; document.body.appendChild(d); setTimeout(()=>d.remove(), 2500);}catch(e){} }
  function getFirstSymbolLayerId(){
    const layers = map.getStyle().layers;
    for (let i=0;i<layers.length;i++){ if (layers[i].type === 'symbol') return layers[i].id; }
    return undefined;
  }

  // Toolbar actions
  document.getElementById('btnLocate')?.addEventListener('click', ()=>{
    if (!('geolocation' in navigator)) { toast('Géolocalisation indisponible'); return; }
    navigator.geolocation.getCurrentPosition((pos)=>{
      const lng = pos.coords.longitude, lat = pos.coords.latitude;
      map.flyTo({center:[lng,lat], zoom: 16});
      // location marker
      if (!map.getSource('loc')) map.addSource('loc', {type:'geojson', data:{type:'Feature', geometry:{type:'Point', coordinates:[lng,lat]}}});
      else map.getSource('loc').setData({type:'Feature', geometry:{type:'Point', coordinates:[lng,lat]}});
      if (!map.getLayer('loc-pt')) map.addLayer({id:'loc-pt', type:'circle', source:'loc', paint:{'circle-radius':6,'circle-color':'#2e7d32','circle-stroke-width':2,'circle-stroke-color':'#ffffff'}});
    }, ()=>toast('Impossible de récupérer la position'));
  });
  document.getElementById('btnReset')?.addEventListener('click', ()=>{
    map.flyTo({center: [-1.68, 48.11], zoom: 12});
    // Reset toggles
    const t1=document.getElementById('togglePLU'); if(t1){ t1.checked=false; }
    const t2=document.getElementById('toggleWMS'); if(t2){ t2.checked=false; const c=document.getElementById('wmsContainer'); if(c) c.style.display='none'; }
    pluOn=false; wmsOn=false; clearPLU(); clearParcel(); clearHighlight(); setInfo('<div class="text-muted">Cliquez sur la carte pour interroger les couches visibles.</div>');
    state.parcel=''; writeHash(state);
  });
  document.getElementById('btnClear')?.addEventListener('click', ()=>{
    try { Draw?.deleteAll(); } catch(e){}
    clearParcel(); clearHighlight();
  });
  document.getElementById('btnExportDraw')?.addEventListener('click', ()=>{
    try{
      const fc = Draw?.getAll();
      if (!fc || !fc.features || fc.features.length===0){ toast('Aucun dessin à exporter'); return; }
      const blob = new Blob([JSON.stringify(fc)], {type:'application/geo+json'});
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `dessin_${new Date().toISOString().slice(0,10)}.geojson`; a.click();
      setTimeout(()=>URL.revokeObjectURL(a.href), 5000);
    }catch(e){ toast('Export échoué'); }
  });
  document.getElementById('fileImportDraw')?.addEventListener('change', (ev)=>{
    const f = ev.target.files && ev.target.files[0]; if (!f) return;
    const rd = new FileReader();
    rd.onload = ()=>{
      try{
        let obj = JSON.parse(rd.result);
        if (obj.type === 'Feature') obj = {type:'FeatureCollection', features:[obj]};
        if (obj.type !== 'FeatureCollection') throw new Error('Format invalide');
        Draw?.add(obj);
        const bb = turf.bbox(obj); map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]], {padding: 20});
      } catch(e){ toast('Import invalide'); }
    };
    rd.readAsText(f);
  });

  function clearPLU(){ try{ if(map.getLayer('plu-line')) map.removeLayer('plu-line'); if(map.getLayer('plu-fill')) map.removeLayer('plu-fill'); if(map.getSource('plu')) map.removeSource('plu'); }catch(e){} }
  function clearParcel(){ try{ if(map.getLayer('parcel-line')) map.removeLayer('parcel-line'); if(map.getLayer('parcel-fill')) map.removeLayer('parcel-fill'); if(map.getSource('parcel')) map.removeSource('parcel'); }catch(e){} }

  // State & UI wiring
  const state = readHash();
  function syncFromState(){
    if (state.ll){ const parts=state.ll.split(',').map(parseFloat); if (parts.length===2 && parts.every(n=>!isNaN(n))) map.setCenter([parts[0], parts[1]]); }
    if (state.z){ const z=parseFloat(state.z); if (!isNaN(z)) map.setZoom(z); }
    if (state.bm){ setBasemap(state.bm); const id='bm-'+state.bm; const r=document.getElementById(id); if(r) r.checked=true; }
    if (state.plu){ const on=state.plu==='1'; const t=document.getElementById('togglePLU'); if(t){ t.checked=on; pluOn=on; if(on) refreshPLU(); } }
    if (state.pluOp){ const s=document.getElementById('pluOpacity'); if(s){ s.value=state.pluOp; map.setPaintProperty('plu-fill','fill-opacity', parseFloat(state.pluOp)); } }
    if (state.cadLabels){ const on=state.cadLabels==='1'; const t=document.getElementById('toggleWMS'); if(t){ t.checked=on; wmsOn=on; const cont=document.getElementById('wmsContainer'); if(cont) cont.style.display=on?'block':'none'; if(on) updateWMS(); } }
    if (state.parcel){ const parts=state.parcel.split(':'); if(parts.length===3) searchParcel(parts[0], parts[1], parts[2]); }
    if (state.q){ const q=document.getElementById('addrQ'); if(q){ q.value=state.q; runGeocode(state.q); } }
  }

  function updateStateFromMap(){
    const c = map.getCenter(); state.ll = `${c.lng.toFixed(5)},${c.lat.toFixed(5)}`; state.z = map.getZoom().toFixed(1);
    const tPLU = document.getElementById('togglePLU'); state.plu = tPLU && tPLU.checked ? '1' : '0';
    const sOp = document.getElementById('pluOpacity'); state.pluOp = sOp ? (sOp.value||'0.15') : '0.15';
    const tWMS = document.getElementById('toggleWMS'); state.cadLabels = tWMS && tWMS.checked ? '1' : '0';
    const bm = document.querySelector('input[name="bm"]:checked'); state.bm = bm ? bm.value : 'osm';
    writeHash(state);
  }

  map.on('moveend', debounce(()=>{ refreshPLU(); refreshCadastre(); updateWMS(); updateStateFromMap(); }, 300));

  document.getElementById('bm-osm')?.addEventListener('change', ()=>{ setBasemap('osm'); updateStateFromMap(); });
  document.getElementById('bm-light')?.addEventListener('change', ()=>{ setBasemap('light'); updateStateFromMap(); });
  document.getElementById('bm-ortho')?.addEventListener('change', ()=>{ setBasemap('ortho'); updateStateFromMap(); });

  document.getElementById('togglePLU')?.addEventListener('change', (e)=>{ pluOn=!!e.target.checked; if (pluOn) refreshPLU(); else { if(map.getLayer('plu-line')) map.removeLayer('plu-line'); if(map.getLayer('plu-fill')) map.removeLayer('plu-fill'); if(map.getSource('plu')) map.removeSource('plu'); } updateStateFromMap(); });
  document.getElementById('pluOpacity')?.addEventListener('input', (e)=>{ const v=parseFloat(e.target.value); if(map.getLayer('plu-fill')) map.setPaintProperty('plu-fill','fill-opacity', v); updateStateFromMap(); });

  document.getElementById('toggleWMS')?.addEventListener('change', (e)=>{ wmsOn=!!e.target.checked; const cont=document.getElementById('wmsContainer'); if(cont) cont.style.display=wmsOn?'block':'none'; if(wmsOn) updateWMS(); updateStateFromMap(); });

  // Cadastre vector overlay
  let cadOn = false;
  async function refreshCadastre(){
    if (!cadOn) return;
    const bbox = bboxFromMap();
    try {
      showLoading();
      const fc = await fetch(`/api/cadastre/wfs?bbox=${bbox.join(',')}`).then(r=>r.ok?r.json():Promise.reject());
      if (!map.getSource('cad')) map.addSource('cad', {type:'geojson', data: fc});
      else map.getSource('cad').setData(fc);
      if (!map.getLayer('cad-line')){
        map.addLayer({id:'cad-line', type:'line', source:'cad', paint:{'line-color':'#666','line-width':1,'line-opacity':0.8}}, getFirstSymbolLayerId());
      }
    } catch(e){ console.warn('Cadastre indisponible', e); }
    finally { hideLoading(); }
  }
  function clearCadastre(){ try{ if(map.getLayer('cad-line')) map.removeLayer('cad-line'); if(map.getSource('cad')) map.removeSource('cad'); }catch(e){} }

  document.getElementById('toggleCadastre')?.addEventListener('change', (e)=>{ cadOn=!!e.target.checked; if (cadOn) refreshCadastre(); else clearCadastre(); updateStateFromMap(); });

  document.getElementById('btnSearchParcel')?.addEventListener('click', ()=>{
    const i = document.getElementById('insee').value.trim();
    const s = document.getElementById('section').value.trim().toUpperCase();
    const n = document.getElementById('numero').value.trim();
    searchParcel(i, s, n);
  });

  let debAddr; $addrQ?.addEventListener('input', ()=>{ const q=$addrQ.value.trim(); clearTimeout(debAddr); debAddr=setTimeout(()=>{ if(q.length>=3) runGeocode(q); }, 250); });

  // Print (simple PNG export)
  document.getElementById('btnPrint')?.addEventListener('click', ()=>{
    try {
      const dataUrl = map.getCanvas().toDataURL('image/png');
      const a = document.createElement('a'); a.href = dataUrl; a.download = `mviewer_${new Date().toISOString().slice(0,10)}.png`; a.click();
    } catch(e) { toast('Export PNG non supporté'); }
  });

  map.on('mousemove', updateCoords);
  map.on('move', updateScale);
  map.on('load', ()=>{
    initDraw();
    syncFromState();
    updateScale();
    updateCoords({lngLat: map.getCenter()});
  });
})();
