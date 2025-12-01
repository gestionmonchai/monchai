(function(global){
  function init(cfg){
    const { el, tenant, token, mode='view', onSave } = cfg || {};
    if(!el||!tenant||!token) throw new Error('Missing el/tenant/token');
    const container = (typeof el==='string')? document.querySelector(el): el;
    if(!container) throw new Error('Container not found');
    const iframe = document.createElement('iframe');
    const url = new URL('/embed/parcelles', window.location.origin);
    url.searchParams.set('tenant', tenant);
    url.searchParams.set('token', token);
    iframe.src = url.toString();
    iframe.style.width='100%'; iframe.style.height='600px'; iframe.style.border='0';
    container.appendChild(iframe);
    // Placeholder hooks for future two-way communication via postMessage
    const api = {
      destroy(){ try{ container.removeChild(iframe); }catch(e){} },
      setMode(m){ /* future */ },
      save(cb){ if(typeof onSave==='function'){ onSave({ ok:true }); } if(typeof cb==='function'){ cb(); } },
    };
    return api;
  }
  global.MonChaiParcelles = { init };
})(window);
