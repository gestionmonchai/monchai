// --- Map style: OSM + Cadastre vector ---
const style = {
  version:8,
  sources:{
    osm:{ type:'raster', tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize:256, attribution:'© OpenStreetMap' },
    cadastre:{ type:'vector', url:'https://openmaptiles.geo.data.gouv.fr/data/cadastre.json' }
  },
  layers:[
    { id:'osm', type:'raster', source:'osm' },
    { id:'parcelles-line', type:'line', source:'cadastre', 'source-layer':'parcelles',
      paint:{'line-width':1,'line-color':'#e11d48'} }
  ]
};
const map = new maplibregl.Map({ container:'map', style, center:[2,46], zoom:5 });
map.addControl(new maplibregl.NavigationControl(),'top-right');

// Optional orthophoto (needs key) – toggle only swaps basemap source if provided
const orthoKey = window.IGN_KEY || null;
const checkboxOrtho = document.getElementById('toggle-ortho');
checkboxOrtho.addEventListener('change',()=>{
  if(!orthoKey){ alert('Ajoute IGN_KEY côté front pour activer.'); checkboxOrtho.checked=false; return; }
  const source = checkboxOrtho.checked
    ? { type:'raster', tiles:[`https://wxs.ign.fr/${orthoKey}/geoportail/wmts?layer=ORTHOIMAGERY.ORTHOPHOTOS&style=normal&tilematrixset=PM&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/jpeg&TileMatrix={z}&TileCol={x}&TileRow={y}`], tileSize:256, attribution:'© IGN' }
    : { type:'raster', tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize:256, attribution:'© OpenStreetMap' };
  map.removeLayer('osm'); map.removeSource('osm');
  map.addSource('osm', source); map.addLayer({id:'osm', type:'raster', source:'osm'}, 'parcelles-line');
});

// --- Selection layer ---
function ensureSelLayers(){
  if(!map.getSource('sel')) map.addSource('sel',{type:'geojson', data:{type:'FeatureCollection', features:[]}});
  if(!map.getLayer('sel-fill')) map.addLayer({id:'sel-fill', type:'fill', source:'sel', paint:{'fill-color':'#e11d48','fill-opacity':0.25}}, 'parcelles-line');
  if(!map.getLayer('sel-line')) map.addLayer({id:'sel-line', type:'line', source:'sel', paint:{'line-color':'#e11d48','line-width':2}});
}
ensureSelLayers();

// --- Click: pick parcel feature from vector tiles ---
map.on('click', (e)=>{
  const feats = map.queryRenderedFeatures(e.point, { layers:['parcelles-line'] });
  if(!feats.length) return;
  const f = feats[0];
  highlightGeo(f);
  showAddPanelFromFeature(f);
});

function highlightGeo(feature){
  map.getSource('sel').setData(feature);
  const bb = turf.bbox(feature);
  if (bb && isFinite(bb[0])) map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]], { padding:20 });
}

// --- Search address (via backend proxy) ---
document.getElementById('addr-go').onclick = async ()=>{
  const q = document.getElementById('addr-q').value.trim();
  if(!q) return;
  const gj = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`).then(r=>r.json());
  const f = gj.features?.[0]; if(!f) return alert('Adresse introuvable');
  const [lon,lat] = f.geometry.coordinates;
  map.flyTo({center:[lon,lat], zoom:18});
};

// --- Search parcel by ref ---
async function fetchParcelRef(insee, section, numero, fb=false){
  const url = `/api/parcel/by-ref?insee=${insee}&section=${section}&numero=${numero}${fb?'&fallback=1':''}`;
  return fetch(url).then(r=>r.json());
}
document.getElementById('parcel-go').onclick = async ()=>{
  let insee = document.getElementById('insee').value.trim();
  let section = document.getElementById('section').value.trim().toUpperCase();
  let numero = document.getElementById('numero').value.trim().padStart(4,'0');
  let fc = await fetchParcelRef(insee, section, numero, false);
  if(!fc.features?.length) fc = await fetchParcelRef(insee, section, numero, true);
  if(!fc.features?.length) return alert('Aucune géométrie');
  const f = fc.features[0];
  highlightGeo(f);
  showAddPanelFromGeo(f, {insee, section, numero});
};

// --- Search by parcelleId ---
document.getElementById('pid-go').onclick = async ()=>{
  const pid = document.getElementById('pid').value.trim();
  if(!pid) return;
  const fc = await fetch(`/api/parcel/by-id?parcelleId=${pid}`).then(r=>r.json());
  if(!fc.features?.length){
    // try fallback by reconstructing ref
    const insee = pid.slice(0,5), section = pid.slice(8,10), numero = pid.slice(-4);
    let fc2 = await fetchParcelRef(insee, section, numero, true);
    if(!fc2.features?.length) return alert('Aucune géométrie');
    const f2 = fc2.features[0]; highlightGeo(f2); showAddPanelFromGeo(f2, {insee, section, numero, parcelle_id:pid}); return;
  }
  const f = fc.features[0]; highlightGeo(f); showAddPanelFromGeo(f, {});
};

// --- “Mes parcelles” panel ---
async function refreshList(){
  const r = await fetch('/api/me/parcels', { headers:{ Authorization:`Bearer ${window.JWT_TOKEN}` }});
  const arr = await r.json();
  const box = document.getElementById('list'); box.innerHTML='';
  arr.forEach(p=>{
    const div = document.createElement('div'); div.className='item';
    div.innerHTML = `
      <h4>${p.label || p.parcelle_id} <span class="badge">${p.harvested_pct}%</span></h4>
      <input type="range" min="0" max="100" step="1" value="${p.harvested_pct}" />
      <input type="text" value="${p.label||''}" placeholder="Tag"/>
      <div style="display:flex; gap:6px; margin-top:6px">
        <button data-act="zoom">Zoom</button>
        <button data-act="save">💾</button>
        <button data-act="del">🗑</button>
      </div>`;
    box.appendChild(div);

    const rng = div.querySelector('input[type=range]');
    const txt = div.querySelector('input[type=text]');
    div.querySelector('[data-act=zoom]').onclick = ()=>{
      if (p.geojson && p.geojson.geometry){
        map.getSource('sel').setData(p.geojson);
        try{
          const bb=turf.bbox(p.geojson); map.fitBounds([[bb[0],bb[1]],[bb[2],bb[3]]],{padding:20});
        }catch{}
      }
    };
    div.querySelector('[data-act=save]').onclick = async ()=>{
      await fetch(`/api/me/parcels/${p.id}`, {
        method:'PUT', headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${window.JWT_TOKEN}` },
        body: JSON.stringify({ harvested_pct: parseFloat(rng.value), label: txt.value })
      });
      refreshList();
    };
    div.querySelector('[data-act=del]').onclick = async ()=>{
      await fetch(`/api/me/parcels/${p.id}`, { method:'DELETE', headers:{ Authorization:`Bearer ${window.JWT_TOKEN}` }});
      refreshList();
    };
  });
}
function showAddPanelFromFeature(f){
  const props = f.properties||{};
  const section = (props.section || props.sec || '').toString();
  const numero  = (props.numero || props.num || '').toString().padStart(4,'0');
  const insee   = props.insee || props.commune || '';
  showAddPanelFromGeo(f, {insee, section, numero});
}
async function showAddPanelFromGeo(f, ref){
  const label = prompt('Tag pour cette parcelle ? (optionnel)', '');
  const pct   = prompt('Pourcentage récolté ? (0-100)', '0');
  const payload = {
    parcelle_id: ref.parcelle_id || (ref.insee ? `${ref.insee}000${(ref.section||'').slice(0,2)}${(ref.numero||'').toString().padStart(4,'0')}` : undefined),
    insee: ref.insee, section: ref.section, numero: ref.numero,
    label: label || '', harvested_pct: parseFloat(pct || 0),
    geojson: f.type==='Feature'? f : { type:'Feature', properties:{}, geometry:f.geometry || f }
  };
  await fetch('/api/me/parcels', {
    method:'POST', headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${window.JWT_TOKEN}` },
    body: JSON.stringify(payload)
  });
  refreshList();
}
refreshList();
