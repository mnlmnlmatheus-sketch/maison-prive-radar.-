# MAISON PRIVÉ — The Private Edit

Catálogo pessoal de moda e luxo, com **fotografias de anúncios reais**, pesquisa avançada e um radar de preços em BRL. Sem imagens geradas por inteligência artificial, cadastro de afiliados ou anúncios pagos.

**Site:** https://maison-prive-v6-ia-corrigida.vercel.app

## O que já funciona

- Vitrine premium responsiva com fotografias fornecidas pelos anúncios de origem; sem imagens geradas por IA. Se uma imagem estiver indisponível, ela não é substituída por uma imagem sintética.
- Busca tolerante a acentos e com sugestão de produtos, filtros combináveis por categoria, marca, loja, público, cor, faixa de preço, fotografia disponível, atualidade da leitura e quedas reais.
- Ordenação, lista ou grade, favoritos salvos no navegador, comparação de até quatro produtos e links diretamente para as respectivas lojas.
- Dois conjuntos de dados: `data/prices.json` (monitor pontual e histórico de 27 produtos, 11 deles OQVestir) e `data/catalog.json` (catálogo extenso, incremental).
- O radar da OQVestir consulta páginas públicas em que `robots.txt` permite acesso, extrai imagens e preços de JSON-LD e identifica marcas declaradas nas páginas. A importação acontece em **lotes de até oito categorias**, uma execução por hora (sujeita a atrasos do GitHub Actions).
- Também existem 16 produtos históricos da loja Gringa capturados no passado. O catálogo público dessa loja pode bloquear novas consultas com HTTP 429; registros anteriores nunca recebem uma nova data falsa.

**Último marco validado:** 1.714 produtos no catálogo incremental, além dos registros individuais, em 21/10/2026. A quantidade atual pode mudar; confirme em `data/oq-progress.json` e `data/catalog.json`.

## Como funciona a atualização

O workflow `.github/workflows/radar-precos.yml` executa `monitor.py` (preços individuais) e `oq_listings.py` (categorias da OQVestir). Os dados são versionados automaticamente no GitHub, e a vitrine busca os arquivos públicos da branch `main`.

- `oq_categories.json`: páginas de categorias aprovadas para descoberta gradual. Há 30 categorias cadastradas; não significa que todas estejam disponíveis em cada execução.
- `watchlist.json`: URLs de produtos específicos a acompanhar, dentro de domínios explicitamente permitidos.
- `data/catalog.json`: todos os produtos fotografados e verificados em até 30 dias; até 3.500 itens.
- `data/oq-progress.json`: últimas fontes consultadas, erros e quantidade de produtos incluídos na rodada.
- `data/events.json`: quedas reais entre duas observações válidas do mesmo produto.

### Limitações importantes

- **Preço registrado não é promessa de estoque ou valor final no checkout.** Frete, tamanho, cupom, Pix, condições de pagamento e disponibilidade podem alterar o valor.
- Fontes podem limitar acessos, mudar páginas e proibir robôs; o monitor não contorna essas restrições e mantém os preços antigos com seus horários originais.
- Não há comissão, venda, redirecionamento pago ou controle de estoque. O site serve para pesquisa e comparação pessoal.
- O horário de GitHub Actions é **aproximado**, não garantia de atualização em tempo real.
- As fotos permanecem hospedadas pelos sites de origem. Se retirarem uma imagem, a vitrine mostra um espaço neutro.

## Testes e manutenção

Os testes de extratores e fluxo encontram-se em `tests/`, executados a cada rodada junto de `node --check site/app.js`. A vitrine está nos arquivos `site/index.html`, `site/styles.css`, `site/app.js`.

Em caso de erro, consulte a aba **[Actions](https://github.com/mnlmnlmatheus-sketch/maison-prive-radar.-/actions)** e o `data/oq-progress.json`.

As credenciais, caso algum serviço venha a ser usado no futuro, devem ficar em **GitHub Secrets**. Não inserir senhas, tokens ou dados privados nos arquivos deste repositório público.

O protótipo antigo `import_awin.py` não é executado pelo workflow atual e **não é necessário** para o Maison Privé pessoal.

© Maison Privé — projeto pessoal independente, sem afiliação às lojas ou marcas.
