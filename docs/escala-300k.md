# Maison Privé — arquitetura para centenas de milhares de produtos

**Estado:** protótipo no GitHub; **Cloudflare D1 ainda não foi provisionado/publicado**. O site hoje usa JSON público do GitHub, adequado ao catálogo atual, não a 300 mil registros.

## Por que migrar
- O catálogo atual reúne registros em `data/catalog.json`, um arquivo crescente cuja API GitHub Contents deixa de fornecer conteúdo embutido acima de 1MB.
- Com 300 mil produtos, enviar todo o JSON ao navegador torna busca e atualização muito lentas.
- `cloudflare/schema.sql` define tabela, índices e FTS5 (busca textual sem acentos).
- `cloudflare/src/worker.js` implementa uma API pública de consulta **somente-leitura**, com paginação e filtros de marca, categoria, loja, volume, concentração, mínimo/máximo e descontos.
- `cloudflare/wrangler.example.toml` documenta o binding. É necessário **criar uma conta Cloudflare e um D1** antes de implantar; não colocar credenciais no GitHub.

## Limites reais de gratuidade
Conforme Cloudflare (outubro de 2026), o D1 Free tem **até 500 MB por banco**, **5 GB totais** na conta, **5 milhões de linhas lidas/dia** e **100 mil linhas escritas/dia**. Indexação FTS5 aumenta espaço e operações de escrita. Não é possível prometer atualização horária de *300 mil* ofertas em um dia na faixa gratuita; apenas um subconjunto priorizado por hora e renovação gradual. É necessário medir tamanho real por produto e crescimento do índice antes de prometer capacidade.

## Limites de fontes
Sem feeds oficiais/autorizações e respeito aos limites de cada loja, 300 mil itens não podem ser coletados e atualizados com confiabilidade. Farfetch retorna HTTP 403 ao GitHub Actions; não contornar bloqueio. Droper expõe preços "a partir de" entre vendedores, não preço final universal. Produtos de perfumes devem ser únicos por concentração, volume e variante, inclusive caixa/tampa.

## Etapas de migração
1. Criar banco D1 e vincular a Worker com binding DB.
2. Testar migração da base atual e consultas reais via `/api/search`.
3. Criar importador autenticado e sujeito a limites; **não disponibilizar rotas de gravação públicas**.
4. Passar o frontend para busca e filtros paginados via API, mantendo um fallback de JSON se a API cair.
5. Aumentar progressivamente fontes acessíveis e separar custo/atualização de cada fornecedor.

Referências:
- https://developers.cloudflare.com/d1/platform/limits/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/d1/sql-api/sql-statements/
