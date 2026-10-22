(() => {
'use strict';
const REPO = 'https://raw.githubusercontent.com/mnlmnlmatheus-sketch/maison-prive-radar.-/main/';
const URLS = { prices: REPO+'data/prices.json', catalog: REPO+'data/catalog.json' };
const $ = id => document.getElementById(id);
const money = n => Number(n).toLocaleString('pt-BR',{style:'currency',currency:'BRL',minimumFractionDigits:2});
const day = iso => { if(!iso)return 'Sem data'; const d=new Date(iso);return Number.isNaN(+d)?'Sem data':d.toLocaleDateString('pt-BR',{day:'2-digit',month:'short',year:'numeric'}); };
const ageDays = iso => iso? Math.max(0,(Date.now()-new Date(iso).getTime())/864e5) : 99999;
const norm = s => String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const esc = s => String(s??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = url => {try {const u=new URL(url);return u.protocol==='https:'?u.href:''}catch(e){return ''}};
const naturalCategory = p => {
 const text=norm([p.category,p.type,p.name,p.productType,p.brand].join(' '));
 if(/bolsa|bag|tote|neverfull|speedy|pochette|flap|crossbody|hobo|satchel|camera bag|birkin|kelly|montsouris|maleta|pegase|mochila/.test(text)) return 'Bolsas';
 if(/tenis|sneaker|samba|sandalia|sapato|bota|scarpin|mocassim|chinelo|salto|pump|flats|slipper|shoe/.test(text)) return 'Calçados';
 if(/jaqueta|calca|camisa|blusa|vestido|casaco|short|saia|jeans|bomber|blazer|t shirt|camiseta|tricot|colete|moletom|roupa|dress/.test(text)) return 'Roupas';
 if(/relogio|watch/.test(text)) return 'Relógios';
 if(/brinco|anel|colar|pulseira|jewel|joia|bijou/.test(text)) return 'Joias';
 return 'Acessórios';
};
const COLOR_FAMILIES = [
 ['Off-white',/\boff white\b|\boffwhite\b|\boff\b/],
 ['Preto',/\bpreto\b|\bpreta\b|\bblack\b/],
 ['Branco',/\bbranco\b|\bbranca\b|\bwhite\b/],
 ['Bege',/\bbege\b|\bcreme\b|\bareia\b|\bnude\b/],
 ['Marrom',/\bmarrom\b|\bcaramelo\b|\bchocolate\b|\bcafe\b/],
 ['Azul',/\bazul\b|\bblue\b|\bmarinho\b/],
 ['Cinza',/\bcinza\b|\bgrafite\b|\bgrey\b/],
 ['Verde',/\bverde\b|\bgreen\b/],
 ['Rosa',/\brosa\b|\bpink\b/],
 ['Vermelho',/\bvermelho\b|\bvermelha\b|\bbordo\b/],
 ['Amarelo',/\bamarelo\b|\bamarela\b/],
 ['Dourado',/\bdourado\b|\bdourada\b/],
 ['Prateado',/\bprateado\b|\bprateada\b/],
 ['Roxo',/\broxo\b|\broxa\b|\blilas\b/],
 ['Laranja',/\blaranja\b/]
];
const colorOf = p => {
 const label=String(p.color||p.name?.split(/\s[-–—]\s/).at(-1)||'');
 const normalized=norm(label);
 return COLOR_FAMILIES.find(([,rx])=>rx.test(normalized))?.[0]||'';
};
const audienceOf = p => {
 if(['Feminino','Masculino','Unissex'].includes(p.audience))return p.audience;
 const name=norm(p.name||'');
 if(name.includes('unissex'))return 'Unissex';
 if(name.includes('feminin'))return 'Feminino';
 if(name.includes('masculin'))return 'Masculino';
 return '';
};
const perfumeProduct = p => String(p.category||'').startsWith('Perfumes');
const categoryMatches = (selected,p) => !selected || (selected==='Perfumes' ? perfumeProduct(p) : selected===p.category);
const unitPrice = p => p.volumeMl>0 ? p.price/p.volumeMl : null;
const perfDiscount = p => Math.max(Number(p.drop)||0,p.originalPrice>p.price?Math.round((p.originalPrice-p.price)/p.originalPrice*100):0);
const store = {
 all:[], visible:[], favorites:new Set(), compare:new Set(), search:'', category:'',brand:'',shop:'',audience:'',color:'',volume:'',concentration:'',min:'',max:'',photos:false,fresh:false,discount:false,favoritesOnly:false,sort:'relevance', pageSize:36, shown:36,list:false, updated:false, started:false, loading:true, synced:null, error:false
};
const loadSet = key => {try {const a=JSON.parse(localStorage.getItem(key)||'[]');return new Set(Array.isArray(a)?a:[])}catch(e){return new Set()}};
store.favorites=loadSet('maison-favorites-v9');
const saveFavorites=()=>{try{localStorage.setItem('maison-favorites-v9',JSON.stringify([...store.favorites]))}catch(e){}};
function normalizeProduct(raw,src){
 if(!raw||typeof raw!=='object')return null;
 const price=Number(raw.price);
 if(!raw.id||!Number.isFinite(price)||price<=0||String(raw.currency||'BRL').toUpperCase()!=='BRL')return null;
 const url=safeUrl(raw.url||raw.link); if(!url)return null;
 const image=safeUrl(raw.image||raw.imageUrl||raw.photo);
 const name=String(raw.name||raw.title||'Peça sem nome').trim().slice(0,240);
 const brand=String(raw.brand||'Outras marcas').trim().slice(0,100);
 const shop=String(raw.shop||raw.store||'Loja de origem').trim().slice(0,90);
 const checkedAt=raw.checkedAt||raw.lastVerifiedAt||raw.lastSeenAt||null;
 const history=Array.isArray(raw.history)?raw.history.filter(x=>Number(x.price)>0).slice(-90):[];
 const original=Number(raw.originalPrice);
 const originalPrice=Number.isFinite(original)&&original>price?original:null;
 const previous=history.length>1?Number(history.at(-2).price):null;
 const drop=Number.isFinite(previous)&&previous>price?Math.round((previous-price)/previous*100):0;
 const vol=Number(raw.volumeMl);
 const volumeMl=Number.isFinite(vol)&&vol>=1&&vol<=1000?vol:(Number((name.match(/\b(\d{1,3})\s*ml\b/i)||[])[1])||null);
 const concentration=String(raw.concentration||'').slice(0,30);
 const priceBasis=raw.priceBasis==='from'?'from':'listed';
 const category=raw.category||naturalCategory(raw);
 const audience=audienceOf(raw), color=colorOf(raw);
 return {id:String(raw.id),name,brand,shop,price,url,image,checkedAt,history,originalPrice,drop,category,audience,color,volumeMl,concentration,priceBasis,source:raw.source||src,addedAt:raw.addedAt||null,condition:raw.condition||null,
  searchValue:norm([name,brand,shop,category,audience,color,volumeMl?volumeMl+' ml':'',concentration,raw.productType,raw.tags,raw.condition].filter(Boolean).join(' '))};
}
function score(p,q) {
 if(!q)return 0;
 const words=norm(q).split(' ').filter(Boolean);
 const name=norm(p.name),brand=norm(p.brand),full=p.searchValue;
 let score=0;
 for(const w of words) {
  if(!full.includes(w))return -999;
  if(brand===w)score+=13;
  else if(brand.startsWith(w))score+=9;
  else if(name.startsWith(w))score+=8;
  else if(name.includes(w))score+=5;
  else score+=2;
 }
 if(name.includes(norm(q)))score+=12;
 return score;
}
async function load() {
 if(store.started)return;
 store.started=true;
 $('syncLabel').textContent='Carregando preços verificados…';
 try {
  const [pricesResponse,catalogResponse]=await Promise.allSettled([
   fetch(URLS.prices+'?at='+Math.floor(Date.now()/900000),{cache:'no-store'}),
   fetch(URLS.catalog+'?at='+Math.floor(Date.now()/900000),{cache:'no-store'})
  ]);
  const fromPrices=pricesResponse.status==='fulfilled'&&pricesResponse.value.ok?await pricesResponse.value.json():null;
  const fromCatalog=catalogResponse.status==='fulfilled'&&catalogResponse.value.ok?await catalogResponse.value.json():null;
  const combined=new Map();
  if(fromCatalog&&Array.isArray(fromCatalog.products)) for(const p of fromCatalog.products) {
   const n=normalizeProduct(p,'Catálogo público'); if(n)combined.set(n.id,n);
  }
  if(fromPrices&&fromPrices.products) for(const p of Object.values(fromPrices.products)) {
   const n=normalizeProduct(p,'Radar verificado');if(!n)continue;
   const old=combined.get(n.id);
   if(!old||ageDays(n.checkedAt)<ageDays(old.checkedAt))combined.set(n.id,{...old,...n,image:n.image||old?.image||'',category:n.category||old?.category||''});
   else combined.set(n.id,{...n,...old,image:old.image||n.image,category:old.category||n.category});
  }
  store.all=[...combined.values()];
  if(store.all.length===0)throw Error('Nenhum produto válido encontrado');
  store.synced=fromCatalog?.updatedAt||fromPrices?.lastRunAt||null;
  store.error=false;store.loading=false;
  $('syncDot').className='status-dot ok';
  $('syncLabel').textContent='Acervo consultado · '+(store.synced?day(store.synced):'dados disponíveis');
  $('totalCount').textContent=store.all.length.toLocaleString('pt-BR');
  $('brandCount').textContent=new Set(store.all.map(p=>p.brand)).size.toLocaleString('pt-BR');
  $('sourceCount').textContent=new Set(store.all.map(p=>p.shop)).size.toLocaleString('pt-BR');
  setupCollections(); fillFilters(); restoreQuery();render();
 }catch(e) {
  store.loading=false;store.error=true;
  $('syncDot').className='status-dot error';
  $('syncLabel').textContent='Não foi possível carregar os dados';
  $('resultCount').textContent='0';
  $('resultText').textContent='peças disponíveis agora';
  $('emptyState').hidden=false;
  $('emptyState').querySelector('h3').textContent='Catálogo temporariamente indisponível.';
  $('emptyState').querySelector('p').textContent='Confira sua conexão ou recarregue a página. Nenhum preço fictício será exibido.';
  $('loadingCards').hidden=true;
 }
}
function setupCollections(){
 const hero=store.all.find(p=>p.image && /Chanel|Louis Vuitton/i.test(p.brand))||store.all.find(p=>p.image);
 if(hero){
  const img=$('heroImage'); img.src=hero.image;img.alt=hero.brand+' — '+hero.name+' (fotografia da '+hero.shop+')';
  img.onload=()=>img.classList.add('loaded');
  $('heroBrand').textContent=hero.brand.toUpperCase();$('heroProduct').textContent=hero.name.slice(0,40).toUpperCase()+' · '+hero.shop.toUpperCase();
 }
 const bag=store.all.find(p=>p.category==='Bolsas'&&p.image);
 const shoe=store.all.find(p=>p.category==='Calçados'&&p.image);
 const fragrance=store.all.find(p=>perfumeProduct(p)&&p.image);
 for(const [id,p] of [['collectionBagImage',bag],['collectionShoeImage',shoe],['collectionPerfumeImage',fragrance]]){
  if(!p)continue; const el=$(id);el.src=p.image;el.alt='Fotografia de '+p.name+' — '+p.shop;el.onload=()=>el.classList.add('loaded');
 }
}
function fillFilters(){
 const fill=(id,values)=>{
  const select=$(id),chosen=select.value;
  while(select.options.length>1)select.remove(1);
  values.filter(Boolean).sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(s=>{
   const opt=document.createElement('option');opt.value=s;opt.textContent=s;select.add(opt);
  });select.value=chosen;
 };
 fill('categorySelect',[...new Set(store.all.map(x=>x.category))]);
 fill('brandSelect',[...new Set(store.all.map(x=>x.brand))]);
 fill('shopSelect',[...new Set(store.all.map(x=>x.shop))]);
 fill('audienceSelect',[...new Set(store.all.map(x=>x.audience))]);
 fill('colorSelect',[...new Set(store.all.map(x=>x.color))]);
 fill('volumeSelect',[...new Set(store.all.filter(perfumeProduct).map(x=>x.volumeMl).filter(Boolean))].sort((a,b)=>a-b).map(String));
 fill('concentrationSelect',[...new Set(store.all.map(x=>x.concentration).filter(Boolean))]);
}
function filterAll(){
 let list=store.all.filter(p=>{
  if(!categoryMatches(store.category,p))return false;
  if(store.brand&&p.brand!==store.brand)return false;
  if(store.shop&&p.shop!==store.shop)return false;
  if(store.audience&&p.audience!==store.audience)return false;
  if(store.color&&p.color!==store.color)return false;
  if(store.volume&&Number(p.volumeMl)!==Number(store.volume))return false;
  if(store.concentration&&p.concentration!==store.concentration)return false;
  if(store.min!==''&&p.price<Number(store.min))return false;
  if(store.max!==''&&p.price>Number(store.max))return false;
  if(store.photos&&!p.image)return false;
  if(store.fresh&&ageDays(p.checkedAt)>7)return false;
  if(store.discount&&!perfDiscount(p))return false;
  if(store.favoritesOnly&&!store.favorites.has(p.id))return false;
  return score(p,store.search)>-900;
 });
 list.sort((a,b)=>{
  switch(store.sort){
   case 'price-asc':return a.price-b.price;
   case 'price-desc':return b.price-a.price;
   case 'unit-asc':return (unitPrice(a)??Infinity)-(unitPrice(b)??Infinity)||a.price-b.price;
   case 'brand':return a.brand.localeCompare(b.brand,'pt-BR')||a.price-b.price;
   case 'newest':return ageDays(a.checkedAt)-ageDays(b.checkedAt);
   case 'discount':return (perfDiscount(b)-perfDiscount(a))||a.price-b.price;
   default:return score(b,store.search)-score(a,store.search)||ageDays(a.checkedAt)-ageDays(b.checkedAt)||a.price-b.price;
  }
 });
 store.visible=list;return list;
}
const imageHTML=(p,cssclass='')=>p.image?'<img class="'+cssclass+'" src="'+esc(p.image)+'" alt="Fotografia original do anúncio: '+esc(p.brand)+' '+esc(p.name)+' — '+esc(p.shop)+'" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.replaceWith(document.createTextNode(\'Fotografia indisponível\'))">':'<div class="product-placeholder"><span>✳</span><small>FOTOGRAFIA<br>AINDA NÃO DISPONÍVEL</small></div>';
function productCard(p) {
 const old=ageDays(p.checkedAt)>7;
 const advertised=p.originalPrice>p.price?Math.round((p.originalPrice-p.price)/p.originalPrice*100):0;
 const savings=p.drop?'<span class="photo-badge sale-badge">↓ '+p.drop+'% QUEDA DE PREÇO</span>':advertised?'<span class="photo-badge sale-badge">↓ '+advertised+'% DA LOJA</span>':'';
 const volumeDetails=p.volumeMl?'<div class="product-unit-price">'+(p.concentration?esc(p.concentration)+' · ':'')+p.volumeMl+' ml · '+money(p.price/p.volumeMl)+'/ml</div>':'';
 return '<article class="product-card" data-id="'+esc(p.id)+'">'+
  '<div class="product-picture-wrap"><button class="product-picture" data-action="details" data-id="'+esc(p.id)+'" aria-label="Ver detalhes de '+esc(p.name)+'">'+imageHTML(p)+'</button>'+
  (savings|| (p.image?'<span class="photo-badge">FOTO ORIGINAL</span>':''))+
  '<button class="heart-btn '+(store.favorites.has(p.id)?'saved':'')+'" data-action="favorite" data-id="'+esc(p.id)+'" title="Favoritar" aria-label="'+(store.favorites.has(p.id)?'Remover dos':'Adicionar aos')+' favoritos"><svg viewBox="0 0 24 24"><path d="M20.8 8.4c0 4.2-8.8 10.5-8.8 10.5S3.2 12.6 3.2 8.4a4.8 4.8 0 0 1 8.8-2.6 4.8 4.8 0 0 1 8.8 2.6Z"/></svg></button></div>'+
  '<div class="product-info"><div class="product-topline"><span>'+esc(p.brand)+'</span><span class="source">'+esc(p.shop)+'</span></div>'+
  '<button class="product-name link-button" data-action="details" data-id="'+esc(p.id)+'">'+esc(p.name)+'</button>'+
  '<div class="product-price">'+(p.priceBasis==='from'?'<small class="price-from">A PARTIR DE</small>':'')+money(p.price)+(p.originalPrice>p.price?'<span class="product-reference-price">'+money(p.originalPrice)+'</span>':'')+'</div>'+volumeDetails+
  '<div class="product-recorded '+(old?'is-stale':'')+'">'+(p.checkedAt?(old?'Última leitura (antiga): ':'Verificado em ')+day(p.checkedAt):'Data da última leitura indisponível')+'</div>'+
  '<div class="product-actions"><a class="product-link" href="'+esc(p.url)+'" target="_blank" rel="noopener noreferrer" aria-label="Ver '+esc(p.name)+' na loja '+esc(p.shop)+'">Ver na loja ↗</a>'+
  '<label class="compare-add"><input type="checkbox" data-action="compare" data-id="'+esc(p.id)+'" '+(store.compare.has(p.id)?'checked':'')+'> Comparar</label></div></div></article>';
}
function render(){
 const list=filterAll(),count=list.length;
 $('loadingCards').hidden=true;
 $('resultCount').textContent=count.toLocaleString('pt-BR');
 $('resultText').textContent=count===1?'peça encontrada':'peças encontradas';
 $('searchContext').textContent=store.search?'Pesquisa: "'+store.search.slice(0,65)+'"':'Preços exibidos com data da coleta';
 $('productGrid').classList.toggle('list-view',store.list);
 $('productGrid').innerHTML=list.slice(0,store.shown).map(productCard).join('');
 $('emptyState').hidden=count!==0;
 $('loadMoreBox').hidden=count<=store.shown;
 $('loadedCaption').textContent='Exibindo '+Math.min(count,store.shown)+' de '+count+' peças';
 $('clearSearch').hidden=!store.search;
 $('favCount').textContent=store.favorites.size;
 $('favCount').hidden=store.favorites.size===0;
 const filterCount=[store.category,store.brand,store.shop,store.audience,store.color,store.volume,store.concentration,store.min,store.max,store.photos,store.fresh,store.discount,store.favoritesOnly].filter(x=>x!==''&&x!==false).length;
 $('filterBadge').hidden=filterCount===0;$('filterBadge').textContent=filterCount;
 renderChips();updateCompareBar();document.title=(store.search?store.search+' — ':'')+'Maison Privé · The Private Edit';
}
function renderChips(){
 const chips=[];
 const add=(name,action)=>chips.push('<button data-remove="'+action+'">'+esc(name)+' <span>×</span></button>');
 if(store.search)add('Pesquisa: '+store.search,'search');
 if(store.category)add(store.category,'category');
 if(store.brand)add(store.brand,'brand');
 if(store.shop)add(store.shop,'shop');
 if(store.audience)add(store.audience,'audience');
 if(store.color)add('Cor: '+store.color,'color');
 if(store.volume)add('Volume: '+store.volume+' ml','volume');
 if(store.concentration)add(store.concentration,'concentration');
 if(store.min)add('A partir de '+money(store.min),'min');
 if(store.max)add('Até '+money(store.max),'max');
 if(store.photos)add('Fotos reais','photos');
 if(store.fresh)add('Últimos 7 dias','fresh');
 if(store.discount)add('Quedas confirmadas','discount');
 if(store.favoritesOnly)add('Favoritos','favorites');
 $('activeFilters').hidden=chips.length===0;$('activeFilters').innerHTML=chips.join('');
 const btns=document.querySelectorAll('#quickFilters button');
 for(const b of btns)b.classList.toggle('is-active',b.dataset.quick==='favorites'?store.favoritesOnly:b.dataset.quick==='discounts'?store.discount:b.dataset.quick==='all'?!store.category&&!store.brand&&!store.favoritesOnly&&!store.discount:(b.dataset.quick===store.category||b.dataset.quick===store.brand));
}
function reset(){
 Object.assign(store,{search:'',category:'',brand:'',shop:'',audience:'',color:'',volume:'',concentration:'',min:'',max:'',photos:false,fresh:false,discount:false,favoritesOnly:false,shown:36});
 $('searchInput').value=''; syncFields();render(); updateUrl();
}
function syncFields(){
 $('categorySelect').value=store.category;
 $('brandSelect').value=store.brand;$('shopSelect').value=store.shop;
 $('audienceSelect').value=store.audience;$('colorSelect').value=store.color;
 $('volumeSelect').value=store.volume;$('concentrationSelect').value=store.concentration;
 $('minPrice').value=store.min;$('maxPrice').value=store.max;
 $('withImage').checked=store.photos;$('onlyFresh').checked=store.fresh;$('onlyDiscount').checked=store.discount;
}
function updateUrl(){
 const q=new URLSearchParams();
 if(store.search)q.set('q',store.search);
 if(store.category)q.set('cat',store.category);
 if(store.brand)q.set('brand',store.brand);
 if(store.shop)q.set('shop',store.shop);
 if(store.audience)q.set('audience',store.audience);
 if(store.color)q.set('color',store.color);
 if(store.volume)q.set('volume',store.volume);
 if(store.concentration)q.set('conc',store.concentration);
 if(store.min!=='')q.set('min',store.min);
 if(store.max!=='')q.set('max',store.max);
 if(store.sort!=='relevance')q.set('sort',store.sort);
 history.replaceState({},'',location.pathname+(q.size?'?'+q.toString():'')+location.hash);
}
function restoreQuery(){
 const q=new URLSearchParams(location.search);
 store.search=(q.get('q')||'').slice(0,120);
 store.category=q.get('cat')||'';
 store.brand=q.get('brand')||'';
 store.shop=q.get('shop')||'';
 store.audience=q.get('audience')||'';
 store.color=q.get('color')||'';
 store.volume=q.get('volume')||'';
 store.concentration=q.get('conc')||'';
 store.min=q.get('min')||'';
 store.max=q.get('max')||'';
 const sorts=['relevance','newest','price-asc','price-desc','brand','discount'];
 store.sort=sorts.includes(q.get('sort'))?q.get('sort'):'relevance';
 $('searchInput').value=store.search;$('sortSelect').value=store.sort;
 syncFields();
}
function toast(msg) {
 const el=$('toast');el.textContent=msg;el.classList.add('visible');
 clearTimeout(toast.t);toast.t=setTimeout(()=>el.classList.remove('visible'),2800);
}
function toggleFavorite(id){
 if(store.favorites.has(id))store.favorites.delete(id);else store.favorites.add(id);
 saveFavorites();toast(store.favorites.has(id)?'Peça adicionada aos favoritos ♡':'Peça removida dos favoritos');
 render();
 if(!$('favDrawer').hidden)showFavorites();
}
function toggleCompare(id,enabled) {
 if(enabled && store.compare.size>=4){toast('Compare até 4 peças por vez.');render();return}
 if(enabled)store.compare.add(id);else store.compare.delete(id);
 updateCompareBar();
}
function updateCompareBar(){
 $('compareBar').hidden=store.compare.size===0;
 $('compareCount').textContent=store.compare.size+' '+(store.compare.size===1?'peça':'peças');
}
function openLayer(id,backdrop){
 $(id).hidden=false;$(backdrop).hidden=false;document.body.classList.add('no-scroll');
}
function closeLayers(){
 for(const x of ['favDrawer','drawerBackdrop','productModal','compareModal','modalBackdrop'])$(x).hidden=true;
 document.body.classList.remove('no-scroll');
}
function showFavorites(){
 const list=store.all.filter(p=>store.favorites.has(p.id));
 $('drawerCount').textContent='('+list.length+')';
 $('favList').innerHTML=list.length?list.map(p=>
  '<div class="fav-item">'+(p.image?'<img src="'+esc(p.image)+'" alt="'+esc(p.name)+'" loading="lazy">':'<div class="fav-photo-placeholder"></div>')+
  '<div class="fav-item-info"><strong>'+esc(p.name)+'</strong><span>'+esc(p.brand)+' · '+esc(p.shop)+'</span><b>'+money(p.price)+'</b>'+
  '<a href="'+esc(p.url)+'" target="_blank" rel="noopener noreferrer">Ver na loja ↗</a><button data-action="favorite" data-id="'+esc(p.id)+'">Remover</button></div></div>').join(''):'<div class="empty-state"><span>✳</span><h3>Nenhum favorito por enquanto.</h3><p>Toque no coração de uma peça para guardar.</p></div>';
}
function showProduct(id){
 const p=store.all.find(x=>x.id===id);if(!p)return;
 $('modalBody').innerHTML='<div class="modal-layout"><div class="modal-photo">'+imageHTML(p)+'</div><div class="modal-description">'+
 '<p class="overline">'+esc(p.brand)+' · '+esc(p.category)+'</p><h2>'+esc(p.name)+'</h2>'+
 '<div class="modal-price">'+(p.priceBasis==='from'?'A partir de ':'')+money(p.price)+'</div>'+
 (p.volumeMl?'<div class="modal-unit">'+esc(p.concentration)+' · '+p.volumeMl+'ml · '+money(p.price/p.volumeMl)+'/ml</div>':'')+
 (p.originalPrice>p.price?'<p>Preço de referência informado pela loja: <s>'+money(p.originalPrice)+'</s></p>':'')+
 '<p>Preço observado pela fonte indicada. Confira valor final, estado, tamanho, frete e disponibilidade na loja.</p>'+
 '<div class="modal-meta"><div><span>Loja</span><b>'+esc(p.shop)+'</b></div><div><span>Última verificação</span><b>'+day(p.checkedAt)+'</b></div><div><span>Fotografia</span><b>'+(p.image?'Original da loja':'Não disponível')+'</b></div><div><span>Queda verificada</span><b>'+(p.drop?p.drop+'%':'Nenhuma registrada')+'</b></div></div>'+
 '<div class="modal-buttons"><a class="btn btn-dark" target="_blank" rel="noopener noreferrer" href="'+esc(p.url)+'">Abrir na loja ↗</a><button class="btn btn-outline" data-action="favorite" data-id="'+esc(p.id)+'">'+(store.favorites.has(p.id)?'♥ Favoritado':'♡ Favoritar')+'</button></div>'+
 '<p class="modal-note">Maison Privé é uma curadoria pessoal independente. Não há venda, estoque próprio ou afiliação com as marcas.</p></div></div>';
 openLayer('productModal','modalBackdrop');
}
function showCompare(){
 const items=store.all.filter(p=>store.compare.has(p.id));
 $('compareBody').innerHTML='<p class="overline">ANÁLISE PESSOAL</p><h2>Compare suas escolhas.</h2>'+
 '<div class="compare-table" style="--comparecols:'+items.length+'">'+items.map(p=>
 '<div class="compare-item">'+(p.image?'<img src="'+esc(p.image)+'" alt="'+esc(p.name)+'" loading="lazy">':'<div class="product-placeholder" style="height:180px">SEM FOTO</div>')+
 '<strong>'+esc(p.brand)+'</strong><small>'+esc(p.name)+'</small><p>'+(p.priceBasis==='from'?'A partir de ':'')+money(p.price)+'</p><small>'+esc(p.shop)+' · '+day(p.checkedAt)+'</small><a href="'+esc(p.url)+'" target="_blank" rel="noopener noreferrer">Ver na loja ↗</a></div>').join('')+'</div>';
 openLayer('compareModal','modalBackdrop');
}
function suggest(){
 const q=$('searchInput').value.trim(), el=$('suggestions');
 if(q.length<2){el.hidden=true;return}
 const found=store.all.filter(p=>score(p,q)>-900).slice(0,5);
 const brands=[...new Set(store.all.filter(p=>norm(p.brand).includes(norm(q))).map(p=>p.brand))].slice(0,2);
 const options=[...brands.map(b=>({label:'Marca: '+b,search:b})),...found.map(p=>({label:p.brand+' — '+p.name,search:p.name}))].slice(0,6);
 el.innerHTML=options.map(o=>'<button data-suggest="'+esc(o.search)+'">'+esc(o.label)+'</button>').join('');
 el.hidden=options.length===0;
}
function applySearch(){
 store.search=$('searchInput').value.trim().slice(0,120);store.shown=36;
 $('suggestions').hidden=true;render();updateUrl();
}
document.addEventListener('click',e=>{
 const b=e.target.closest('[data-action]');
 if(b){const id=b.dataset.id,action=b.dataset.action;
  if(action==='favorite'){toggleFavorite(id);return}
  if(action==='details'){showProduct(id);return}
  if(action==='compare'){toggleCompare(id,b.checked);return}
 }
 const r=e.target.closest('[data-remove]');if(r){
  const key=r.dataset.remove;
  if(key==='search'){store.search='';$('searchInput').value=''}
  if(key==='category')store.category='';
  if(key==='brand')store.brand='';
  if(key==='shop')store.shop='';
  if(key==='audience')store.audience='';
  if(key==='color')store.color='';
  if(key==='volume')store.volume='';
  if(key==='concentration')store.concentration='';
  if(key==='min')store.min='';
  if(key==='max')store.max='';
  if(key==='photos')store.photos=false;
  if(key==='fresh')store.fresh=false;
  if(key==='discount')store.discount=false;
  if(key==='favorites')store.favoritesOnly=false;
  store.shown=36;syncFields();render();updateUrl();return
 }
 const suggestBtn=e.target.closest('[data-suggest]');
 if(suggestBtn){$('searchInput').value=suggestBtn.dataset.suggest;applySearch();return}
 const cat=e.target.closest('[data-cat]');
 if(cat){store.category=cat.dataset.cat;store.brand='';store.favoritesOnly=false;store.shown=36;syncFields();render();updateUrl();document.getElementById('catalogo').scrollIntoView({behavior:'smooth'});return}
 const quick=e.target.closest('[data-quick]');
 if(quick){const v=quick.dataset.quick;store.category='';store.brand='';store.favoritesOnly=false;
  if(v==='favorites')store.favoritesOnly=true;
  else if(v==='discounts')store.discount=true;
  else if(['Bolsas','Calçados','Roupas','Acessórios','Perfumes','Perfumes de nicho','Perfumes árabes','Perfumes designer'].includes(v))store.category=v;
  else if(v!=='all')store.brand=v;
  if(v!=='discounts')store.discount=false;
  store.shown=36;syncFields();render();updateUrl();return
 }
});
$('searchInput').addEventListener('input',()=>{suggest();clearTimeout(store.searchTimer);store.searchTimer=setTimeout(applySearch,220)});
$('searchInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();applySearch()}if(e.key==='Escape'){$('suggestions').hidden=true; e.target.blur()}});
$('clearSearch').addEventListener('click',()=>{store.search='';$('searchInput').value='';render();updateUrl()});
$('filterToggle').addEventListener('click',()=>{const hidden=!$('filters').hidden;$('filters').hidden=hidden;$('filterToggle').setAttribute('aria-expanded',String(!hidden))});
$('applyFilters').addEventListener('click',()=>{
 Object.assign(store,{category:$('categorySelect').value,brand:$('brandSelect').value,shop:$('shopSelect').value,audience:$('audienceSelect').value,color:$('colorSelect').value,volume:$('volumeSelect').value,concentration:$('concentrationSelect').value,min:$('minPrice').value,max:$('maxPrice').value,photos:$('withImage').checked,fresh:$('onlyFresh').checked,discount:$('onlyDiscount').checked,shown:36});
 $('filters').hidden=true;$('filterToggle').setAttribute('aria-expanded','false');render();updateUrl();
});
$('resetFilters').addEventListener('click',reset);$('emptyReset').addEventListener('click',reset);
$('sortSelect').addEventListener('change',e=>{store.sort=e.target.value;store.shown=36;render();updateUrl()});
$('loadMore').addEventListener('click',()=>{store.shown+=store.pageSize;render()});
$('viewToggle').addEventListener('click',()=>{store.list=!store.list;render()});
$('favoriteButton').addEventListener('click',()=>{showFavorites();openLayer('favDrawer','drawerBackdrop')});
$('drawerClose').addEventListener('click',closeLayers);$('drawerBackdrop').addEventListener('click',closeLayers);
$('modalBackdrop').addEventListener('click',closeLayers);$('modalClose').addEventListener('click',closeLayers);$('compareModalClose').addEventListener('click',closeLayers);
$('compareOpen').addEventListener('click',showCompare);
$('compareClear').addEventListener('click',()=>{store.compare.clear();render()});
$('menuButton').addEventListener('click',()=>{const was=$('mobileMenu').hidden;$('mobileMenu').hidden=!was;$('menuButton').setAttribute('aria-expanded',String(was))});
$('mobileMenu').addEventListener('click',e=>{if(e.target.closest('a')){$('mobileMenu').hidden=true;$('menuButton').setAttribute('aria-expanded','false')}});
document.querySelectorAll('.search-focus').forEach(x=>x.addEventListener('click',()=>{document.getElementById('catalogo').scrollIntoView({behavior:'smooth'});setTimeout(()=>$('searchInput').focus(),320)}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLayers();if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('searchInput').focus()}});
window.addEventListener('pageshow',()=>{if(!store.started)load()});
if(document.readyState!=='loading')load();else document.addEventListener('DOMContentLoaded',load,{once:true});
})();