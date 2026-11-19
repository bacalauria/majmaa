window.__S=t=>new Promise(r=>setTimeout(r,t));
if(!window.__got){window.__got={}; window.__ready=false;
addEventListener('message',e=>{if(e.origin!=='https://bacalauria.github.io'||!e.data||!e.data.__majmaa) return; if(e.data.ready) window.__ready=true; if(e.data.file) window.__got[e.data.name]=e.data.file;});
const f=document.createElement('iframe'); f.id='__relay'; f.style.cssText='position:fixed;width:1px;height:1px;left:-10px;top:-10px;border:0'; f.src='https://bacalauria.github.io/majmaa/assets/relay-tmp.html?x='+Date.now(); document.body.appendChild(f);}
window.__req=async(p)=>{if(__got[p]) return __got[p]; for(let i=0;i<20&&!__ready;i++) await __S(500); document.getElementById('__relay').contentWindow.postMessage({__majmaaReq:1,path:p},'https://bacalauria.github.io'); for(let i=0;i<160&&!__got[p];i++) await __S(500); return __got[p];};
window.__setFile=(file,sel)=>{const inp=[...document.querySelectorAll(sel||'input[type=file]')][0]; const dt=new DataTransfer(); dt.items.add(file); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));};
window.__paste=(cap)=>{const tb=[...document.querySelectorAll('[contenteditable=true][role=textbox]')].find(e=>e.getBoundingClientRect().width>0); tb.focus(); const dt=new DataTransfer(); dt.setData('text/plain',cap); tb.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true})); return tb;};
window.__btn=(re)=>[...document.querySelectorAll('[role=button],button')].filter(e=>e.getBoundingClientRect().width>0&&re.test((e.innerText||e.getAttribute('aria-label')||'').trim())).pop();
window.__leaf=(txt)=>[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.getBoundingClientRect().width>0&&e.innerText?.trim()===txt).pop();
window.__clickTxt=async(re)=>{const el=[...document.querySelectorAll('div[role=button],span,div[role=menuitem],[role=button]')].filter(e=>e.getBoundingClientRect().width>0&&re.test((e.innerText||'').trim())).pop(); if(!el) return false; el.click(); await __S(900); return true;};
window.__schedDlg=()=>{const h=__leaf('Scheduling options'); let p=h; while(p&&p.querySelectorAll('input').length<2) p=p.parentElement; return p;};
window.__pickDay=async(lbl)=>{const els=[...document.querySelectorAll('[role=gridcell]')].filter(e=>e.getBoundingClientRect().width>0&&e.innerText.includes(lbl)); if(!els.length) return 'none'; (els[0].querySelector('[role=button]')||els[0]).click(); await __S(900); return 'ok';};
window.__sched=async(lbl,time)=>{const log=[]; document.querySelector('[aria-label="More post options"]').click(); await __S(1200); log.push('menu:'+await __clickTxt(/^Schedule post$/)); await __S(1500);
 const dlg=__schedDlg(); if(!dlg) return log.concat('nodlg'); const inputs=[...dlg.querySelectorAll('input')];
 inputs[0].click(); inputs[0].focus(); await __S(1000);
 for(let k=0;k<2&&!([...document.querySelectorAll('[role=gridcell]')].some(e=>e.getBoundingClientRect().width>0&&e.innerText.includes(lbl)));k++){const nx=[...document.querySelectorAll('[aria-label]')].find(e=>/next/i.test(e.getAttribute('aria-label'))&&e.getBoundingClientRect().width>0); nx&&nx.click(); await __S(800);}
 log.push('day:'+await __pickDay(lbl));
 inputs[1].click(); inputs[1].focus(); await __S(1200);
 const opt=__leaf(time); log.push('opt:'+!!opt); if(opt){opt.scrollIntoView({block:'center'}); (opt.closest('[role=option],[role=button]')||opt).click(); await __S(900);}
 log.push('vals:'+inputs.map(i=>i.value).join(' / ')); return log;};
window.__A=async(key)=>{await __S(1500); window.__M=window.__M||JSON.parse(await (await __req('meta.json')).text()); window.__m=__M.find(x=>x.key===key);
 const v=await __req(__m.video); const t=await __req(__m.thumb);
 for(let i=0;i<20&&!document.querySelector('input[type=file]');i++) await __S(500);
 __setFile(v); for(let i=0;i<25&&!/Choose a thumbnail/.test(document.body.innerText);i++) await __S(1000);
 return key+' video:'+v?.size+' thumb:'+t?.size+' ui:'+/Choose a thumbnail/.test(document.body.innerText);};
window.__B=async(pl)=>{const log=[]; const m=__m;
 const ct=__leaf('Choose a thumbnail'); (ct.closest('[role=button]')||ct).click(); await __S(1800);
 const inp=[...document.querySelectorAll('input[type=file]')].find(i=>i.accept==='.png,.jpg,.jpeg'); if(inp){const dt=new DataTransfer(); dt.items.add(__got[m.thumb]); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); await __S(3500); log.push('thumb');} else log.push('NOTHUMB');
 const tb=__paste(m.fb); await __S(1200); log.push('cap:'+(tb.innerText.trim().length===m.fb.length));
 const ap=__leaf('Add to playlist'); (ap.closest('[role=button]')||ap).click(); await __S(2200);
 const row=__leaf(pl); if(row){(row.closest('[role=button],[role=listitem],[role=checkbox],label')||row).click(); await __S(1500); const d=__btn(/^(Done|Save|Add)$/); d&&d.click(); await __S(1000);} else log.push('noplrow');
 const plc=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.innerText?.trim()===pl&&e.getBoundingClientRect().width>0).length; log.push('pl:'+plc);
 return log;};
window.__C=async()=>{const m=__m; const AR={'11':'November','12':'December'}; const [y,mo,d]=m.date.split('-'); const lbl=AR[mo]+' '+(+d)+', '+y; const hh=+m.time.split(':')[0]+2; const time=(hh>12?hh-12:hh)+':00 '+(hh>=12?'PM':'AM');
 const log=await __sched(lbl,time); if(!log.includes('day:ok')||!log.includes('opt:true')) return 'STOP '+log.join(' | ');
 const b1=__btn(/^Schedule for later$/); b1&&b1.click(); await __S(1500);
 const sw=[...document.querySelectorAll('input[role=switch],[role=switch]')].map(s=>s.checked??s.getAttribute('aria-checked')); if(sw.some(x=>x===true||x==='true')) return 'STOP switch on '+sw;
 setTimeout(async()=>{__btn(/^Schedule post$/).click(); for(let i=0;i<20;i++){await __S(1000); const o=__btn(/^Publish Original Post$/); if(o){o.click(); break;}}},50);
 return 'scheduling '+m.key+' '+lbl+' '+time+' | '+log.join(' | ');};
