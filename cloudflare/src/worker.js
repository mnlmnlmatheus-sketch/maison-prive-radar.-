/**
 * Maison Privé: API de busca com D1, paginação no servidor (PROTÓTIPO NÃO PUBLICADO).
 * Rotas GET /api/search e /api/health. Sem gravação pública.
 */
const SORTS = {
 newest:"p.checked_at DESC,p.id ASC",
 "price-asc":"p.price_cents ASC,p.id ASC",
 "price-desc":"p.price_cents DESC,p.id ASC",
 brand:"p.brand COLLATE NOCASE,p.id ASC",
 discount:"(COALESCE(p.original_price_cents,0)-p.price_cents) DESC,p.id ASC",
 "unit-asc":"CAST(p.price_cents AS REAL)/NULLIF(p.volume_ml,0) ASC,p.id ASC",
};
const FIELDS="p.id,p.name,p.brand,p.shop,p.category,p.audience,p.color,p.volume_ml,p.concentration,p.price_cents,p.original_price_cents,p.price_basis,p.url,p.image,p.checked_at";
function buildWhere(u){
 const parts=[],args=[];
 const push=(sql,value)=>{parts.push(sql);args.push(value)};
 for(const [key,field] of [["brand","p.brand"],["shop","p.shop"],["color","p.color"],["audience","p.audience"],["concentration","p.concentration"]]){
  const v=u.searchParams.get(key); if(v)push(field+"=?",v.slice(0,100));
 }
 const cat=u.searchParams.get("category");
 if(cat){if(cat==="Perfumes")push("p.category LIKE ?","Perfumes%");else push("p.category=?",cat.slice(0,100))}
 const amount=(key,op)=>{
  const raw=u.searchParams.get(key),v=Number(raw);
  if(raw!==null && raw!==""&&Number.isFinite(v)&&v>=0 && v<=1000000)push("p.price_cents "+op+" ?",Math.round(v*100));
 };
 amount("min",">=");amount("max","<=");
 const volume=Number(u.searchParams.get("volume"));
 if(u.searchParams.get("volume")&&Number.isFinite(volume)&&volume>0&&volume<=1000)push("p.volume_ml=?",volume);
 if(u.searchParams.get("discount")==="true")parts.push("p.original_price_cents>p.price_cents");
 if(u.searchParams.get("photos")==="true")parts.push("p.image IS NOT NULL AND p.image<>''");
 const q=u.searchParams.get("q")||"";
 const tokens=(q.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(x=>x.length>1).slice(0,5);
 if(tokens.length)push("p.rowid IN(SELECT rowid FROM products_fts WHERE products_fts MATCH ?)",tokens.map(x=>'"'+x.slice(0,32)+'"*').join(" AND "));
 return {where:parts.length?" WHERE "+parts.join(" AND "):"",args};
}
function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"public, max-age=30","access-control-allow-origin":"*"}})}
export default {async fetch(req,env){
 const u=new URL(req.url);
 if(req.method!=="GET")return json({error:"Method not allowed"},405);
 if(u.pathname==="/api/health")return json({ok:!!env.DB,version:"prototype-0.1"});
 if(u.pathname!=="/api/search")return json({error:"Not found"},404);
 if(!env.DB)return json({error:"Database D1 not connected"},503);
 const limit=Math.max(1,Math.min(48,Number(u.searchParams.get("limit"))||24));
 const page=Math.max(1,Math.min(1000,Number(u.searchParams.get("page"))||1));
 const {where,args}=buildWhere(u);
 const by=SORTS[u.searchParams.get("sort")]||SORTS.newest;
 try{
  const results=await env.DB.prepare("SELECT "+FIELDS+" FROM products p"+where+" ORDER BY "+by+" LIMIT ? OFFSET ?").bind(...args,Math.floor(limit),Math.floor((page-1)*limit)).all();
  const items=(results.results||[]).map(p=>({id:p.id,name:p.name,brand:p.brand,shop:p.shop,category:p.category,audience:p.audience,color:p.color,volumeMl:p.volume_ml,concentration:p.concentration,price:p.price_cents/100,originalPrice:p.original_price_cents?p.original_price_cents/100:null,priceBasis:p.price_basis,currency:"BRL",url:p.url,image:p.image,checkedAt:p.checked_at}));
  return json({items,page,limit,hasMore:items.length===Math.floor(limit)});
 }catch(e){return json({error:"Database search unavailable"},500)}
}};
