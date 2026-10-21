# Maison Privé · Radar de preços

Monitor de preços em lojas selecionadas, com automação horária via GitHub Actions, histórico de preços e detecção de quedas verificadas.

**Estado:** a coleta só é confirmada quando a loja permite acesso e fornece preço em BRL identificável. Nunca inventar descontos, ignorar erros e respeitar robots.txt. Não é uma integração oficial com varejistas nem uma promessa de dados em tempo real.

Os arquivos do monitor, testes e workflow serão adicionados a este repositório. A vitrine pública já existente permanecerá publicada separadamente até a integração ser verificada.


## Status verificado em 21/10/2026
- **GitHub Actions:** automação horária com 10 testes passando.
- **OQVestir:** quatro páginas de produto acessíveis; quatro preços BRL confirmados e registrados em `data/prices.json`.
- **Farfetch:** GitHub recebe HTTP 403; esses links foram retirados do radar gratuito (sem bypass).
- **Sephora:** `robots.txt` indisponível a partir do runner; consulta omitida por segurança.
- **Site Maison Privé:** https://maison-prive-v6-ia-corrigida.vercel.app mostra painel **Radar grátis** consumindo o JSON público do repositório.
- **Quedas reais:** exigem pelo menos duas leituras válidas do mesmo produto. Até aqui não houve queda confirmada.

## Ampliar catálogo com dados oficiais Awin (opcional)
1. Cadastre seu canal/site como afiliado: https://www.awin.com/br/afiliados/content-creator-influencer
2. Na plataforma, acesse **Toolbox → Create-a-Feed**. Use um anunciante/loja cujo feed sua conta esteja autorizada a baixar. Selecione CSV, moeda BRL e colunas de nome, preço, moeda, loja e link.
3. Copie o link **privado** do feed, que contém credenciais. **Não publique a URL em commit ou chat.**
4. No repositório, vá em **Settings → Secrets and variables → Actions → New repository secret**. Nome: `AWIN_FEED_URL`. Valor: URL HTTPS gerada no painel Awin.
5. Próxima execução do GitHub executa `import_awin.py` e grava até 120 produtos autorizados em `data/affiliate-catalog.json`. URLs de feed são aceitas apenas de domínios oficiais permitidos; não enviamos a chave em logs.
6. Os preços de feed e o histórico em GitHub serão distintos dos 49 itens de referência na vitrine. A incorporação automática dessas novas ofertas exige validação da origem e do uso das imagens fornecidas.

Fontes oficiais: https://help.awin.com/developers/docs/product-feed-list-download e https://help.awin.com/developers/docs/downloading-feeds-using-create-a-feed
