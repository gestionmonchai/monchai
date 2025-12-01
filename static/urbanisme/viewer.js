const statusEl = document.getElementById('status');
function setStatus(msg){ if (statusEl) statusEl.textContent = msg || ''; }

// Init map
const map = L.map('map').setView([48.11, -1.68], 12);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Drawing / measures
if (map.pm && map.pm.addControls){
  map.pm.addControls({ position: 'topleft', drawPolygon: true, drawPolyline: true, editMode: true, dragMode: true, removalMode:true });
}

// Toggle tabs
const tabAddr = document.getElementById('tab-addr');
const tabParcel = document.getElementById('tab-parcel');
if (tabAddr) tabAddr.onclick = ()=>showPane('addr');
if (tabParcel) tabParcel.onclick = ()=>showPane('parcel');
function showPane(which){
  document.getElementById('tab-addr')?.classList.toggle('active', which==='addr');
  document.getElementById('tab-parcel')?.classList.toggle('active', which==='parcel');
  const pAddr = document.getElementById('pane-addr');
  const pParcel = document.getElementById('pane-parcel');
  if (pAddr) pAddr.style.display = (which==='addr')?'block':'none';
  if (pParcel) pParcel.style.display = (which==='parcel')?'block':'none';
}

// Layers
let layerPLU = null;
let layerParcel = null;
let layerCadastreWMS = null;

// WMS Cadastre (trame + n°)
const chkWMS = document.getElementById('chk-cad-wms');
function ensureCadastreWMS(){
  if (!chkWMS || !chkWMS.checked){
    if (layerCadastreWMS) { map.removeLayer(layerCadastreWMS); layerCadastreWMS = null; }
    return;
  }
  if (!layerCadastreWMS){
    const WMS_URL = (window.IGN_WMS_PARCELLAIRE || '').trim();
    const LAYERS = (window.IGN_WMS_LAYERS || 'CADASTRE.PARCELLE,CADASTRE.NUMERO').trim();
    if (!WMS_URL){ setStatus('WMS parcellaire non configuré (IGN_WMS_PARCELLAIRE).'); return; }
    layerCadastreWMS = L.tileLayer.wms(WMS_URL, {
      layers: LAYERS, format:'image/png', transparent:true, opacity:0.6, attribution:'IGN'
    }).addTo(map);
  }
}
if (chkWMS){ chkWMS.onchange = ensureCadastreWMS; ensureCadastreWMS(); }

// PLU (WFS → GeoJSON via proxy)
const chkPLU = document.getElementById('chk-plu');
let deb=null;
function refreshPLU(){
  if (!chkPLU || !chkPLU.checked){
    if (layerPLU) { map.removeLayer(layerPLU); layerPLU = null; }
    return;
  }
  const b = map.getBounds();
  const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(',');
  setStatus('Chargement PLU…');
  fetch(`/api/plu/zones?bbox=${bbox}`)
    .then(r=>r.json())
    .then(fc=>{
      setStatus('');
      if (layerPLU) { map.removeLayer(layerPLU); layerPLU = null; }
      layerPLU = L.geoJSON(fc, {
        style: { color:'#0a58ca', weight:1, opacity:0.9, fillOpacity:0.15 }
      }).bindPopup(f => {
        const p = f.properties || {};
        return `<b>PLU</b><br>${p.libelle || p.typezone || 'Zone'}`;
      }).addTo(map);
    })
    .catch(()=> setStatus('PLU indisponible (clé/flux ?)'));
}
if (chkPLU) chkPLU.onchange = ()=>refreshPLU();
map.on('moveend', ()=>{ clearTimeout(deb); deb=setTimeout(refreshPLU,300); });

// Recherche Adresse (BAN via proxy)
const btnAddrGo = document.getElementById('addr-go');
if (btnAddrGo) btnAddrGo.onclick = async ()=>{
  const qEl = document.getElementById('addr-q');
  const q = (qEl && qEl.value || '').trim();
  if (!q) return;
  setStatus('Recherche adresse…');
  try{
    const gj = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`).then(r=>r.json());
    const f = (gj.features && gj.features[0]);
    if (!f) { setStatus('Adresse introuvable'); return; }
    const g = f.geometry || {};
    if (g.type === 'Point'){
      const [lon,lat] = g.coordinates; map.setView([lat,lon], 18);
    } else {
      const bb = turf.bbox(f); map.fitBounds([[bb[1],bb[0]],[bb[3],bb[2]]], { padding:[20,20] });
    }
    setStatus('');
  }catch{ setStatus('Erreur géocodage'); }
};

// Recherche Parcelle (Cadastre + fallback)
const btnParcel = document.getElementById('p-go');
if (btnParcel) btnParcel.onclick = async ()=>{
  const insee = (document.getElementById('p-insee')?.value || '').trim();
  const section = ((document.getElementById('p-sec')?.value || '').trim()).toUpperCase();
  let numero = (document.getElementById('p-num')?.value || '').trim();
  numero = numero.padStart(4,'0');

  setStatus('Recherche parcelle…');
  try{
    let fc = await fetch(`/api/cadastre/parcel?insee=${insee}&section=${section}&numero=${numero}`).then(r=>r.json());
    if (!fc.features || !fc.features.length){
      fc = await fetch(`/api/cadastre/parcel?insee=${insee}&section=${section}&numero=${numero}&fallback=1`).then(r=>r.json());
    }
    if (!fc.features || !fc.features.length){ setStatus('Aucune géométrie'); return; }

    if (layerParcel) { map.removeLayer(layerParcel); layerParcel = null; }
    layerParcel = L.geoJSON(fc, {
      style: { color:'#E53935', weight:2, fillOpacity:0.2 }
    }).addTo(map);

    try{
      const bb = turf.bbox(fc);
      map.fitBounds([[bb[1],bb[0]],[bb[3],bb[2]]], { padding:[20,20] });
    }catch{}
    setStatus('');
  }catch{ setStatus('Erreur recherche parcelle'); }
};
