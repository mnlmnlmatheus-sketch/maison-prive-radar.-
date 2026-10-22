'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('site/app.js','utf8');
const expose=source.replace(/\}\)\(\);\s*$/, '\nglobalThis.__maisonTest={normalizeProduct,filterAll,score,store};\n})();');
assert.notEqual(expose,source,'Exposição das funções de teste');
const dummy={addEventListener(){},setAttribute(){},focus(){},classList:{add(){},remove(){},toggle(){}}};
const ctx={document:{readyState:'loading',addEventListener(){},querySelectorAll(){return []},getElementById(){return dummy}},window:{addEventListener(){}},localStorage:{getItem(){return null},setItem(){}},console,URL,URLSearchParams,Date,Set,Map,Intl,Number,Math,String,RegExp,Array,Promise};
vm.createContext(ctx);vm.runInContext(expose,ctx);
const {normalizeProduct,filterAll,store}=ctx.__maisonTest;
const sample=[
{id:'one',brand:'Adidas Originals',name:'Tênis Unissex Samba OG - Preto',shop:'OQVestir',price:560.9,currency:'BRL',url:'https://www.oqvestir.com.br/item-100000',image:'https://oqvestir.fbitsstatic.net/x.jpg',checkedAt:new Date().toISOString(),category:'Calçados'},
{id:'two',brand:'Chanel',name:'Bolsa Clássica - Marrom',shop:'Gringa',price:12500,currency:'BRL',url:'https://gringa.com.br/item-200000',image:'https://cdn.shopify.com/x.jpg',checkedAt:new Date().toISOString(),category:'Bolsas'},
{id:'three',brand:'BOSS',name:'Calça Masculina P-Genius - Azul',shop:'OQVestir',price:640,currency:'BRL',url:'https://www.oqvestir.com.br/item-300000',image:'',checkedAt:new Date().toISOString(),category:'Roupas'}
];
store.all=sample.map(p=>normalizeProduct(p,'teste'));
assert.equal(store.all[0].color,'Preto');assert.equal(store.all[0].audience,'Unissex');
assert.equal(store.all[1].color,'Marrom');assert.equal(store.all[2].audience,'Masculino');
store.search='samba preto';assert.equal(filterAll().length,1,'Pesquisa de duas palavras');
store.search='TENIS';assert.equal(filterAll().length,1,'Busca sem acento');
store.search='';store.brand='Chanel';store.category='Bolsas';store.min='10000';store.max='13000';
assert.equal(filterAll().length,1,'Marca categoria e preços');
store.color='Preto';assert.equal(filterAll().length,0,'Cor adicional');
store.brand='';store.category='';store.min='';store.max='';store.color='';store.photos=true;
assert.equal(filterAll().length,2,'Fotografia');
store.photos=false;store.audience='Masculino';assert.equal(filterAll().length,1,'Público');
store.audience='';store.sort='price-desc';assert.equal(filterAll()[0].brand,'Chanel','Ordenação');
assert.equal(normalizeProduct({...sample[0],url:'javascript:alert(1)'},'teste'),null,'HTTPS apenas');
assert.equal(normalizeProduct({...sample[0],currency:'USD'},'teste'),null,'BRL apenas');
assert.equal(normalizeProduct({...sample[0],price:0},'teste'),null,'Preço válido');
const db=JSON.parse(fs.readFileSync('data/catalog.json','utf8'));
assert.ok(db.products.length>1000,'Mais de 1000 produtos');
const normalized=db.products.map(p=>normalizeProduct(p,'arquivo'));
assert.equal(normalized.filter(Boolean).length,db.products.length,'Produtos válidos');
assert.equal(normalized.filter(p=>p.image).length,db.products.length,'Fotos originais');
assert.equal(new Set(normalized.map(p=>p.id)).size,normalized.length,'IDs únicos');
console.log('OK: pesquisa, filtros, segurança e',normalized.length,'produtos originais.');
