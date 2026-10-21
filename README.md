# Maison Privé · Radar pessoal de preços

Este repositório é um monitor gratuito para **uso pessoal**, sem programa de afiliados, cadastro, comissões ou intenção de venda.

## Situação atual
- **11 produtos na OQVestir** (Vans, BOSS e Adidas Originals) monitorados por metadados públicos de preço em BRL.
- **16 produtos na Gringa** (Chanel e Louis Vuitton) consultados por JSON público de coleções Shopify, após checar robots.txt e confirmar a moeda BRL.
- Total inicial: **27 preços confirmados** na execução de 21/10/2026, armazenados em `data/prices.json`.
- Horário: **uma execução aproximada por hora**, agendada via `.github/workflows/radar-precos.yml`.
- Histórico de preço e quedas em `data/prices.json` e `data/events.json`; quedas só são registradas quando uma leitura válida é inferior a outra leitura válida do mesmo item.
- A vitrine Maison Privé existente permanece online em https://maison-prive-v6-ia-corrigida.vercel.app; o painel Radar grátis já consulta os dados públicos do GitHub.

## Como ver os preços
Acesse `data/prices.json` ou o painel Radar grátis na vitrine. Para conferir a última automação: **Actions → Maison Prive - Radar de Precos**.

## O que os números significam
Os preços da Gringa vêm do catálogo Shopify em BRL; **podem corresponder ao preço de cartão/padrão**, não necessariamente ao Pix nem a cupons ou promoções de checkout. São produtos de luxo de segunda mão, cujo estado e disponibilidade podem mudar rapidamente. Os demais preços são metadados públicos e podem variar com tamanho, CEP, cupom e forma de pagamento. Confira na loja antes de comprar.

Se houver erro de acesso, o script preserva o último preço com seu horário original, sem fingir que está atualizado. Nenhum preço é obtido burlando bloqueios, CAPTCHA ou robots.txt. O fato de o workflow terminar com sucesso não garante que todos os preços foram capturados; confirme `successfulChecks`, `shopifyVerifiedChecks` e `data/shopify-status.json`.

## Como adicionar produtos
- OQVestir: acrescente `id`, `brand`, `name`, `shop`, `url`, `currency=BRL` em `watchlist.json`. Apenas domínios permitidos no código serão acessados.
- Shopify: adicione coleções de uma loja aprovada na configuração `shopify_sources.json` e, se necessário, ajuste a allowlist de hosts no código; sempre valide primeiro moeda e robots.txt.

O monitoramento via Shopify atualmente utiliza uma amostra de produtos nas primeiras páginas das coleções. Produtos mais antigos podem sair da amostra; não é garantia de cobertura integral. O agendamento do GitHub Actions também pode atrasar.

## Custo
O workflow utiliza runners padrão de GitHub Actions em um repositório público. Normalmente isso não exige assinatura, sujeito a termos, limites de uso e possíveis alterações de política.

## Segurança
Não adicione senhas, cookies, tokens ou informações pessoais ao repositório público. O arquivo `import_awin.py` é um protótipo antigo, **não é executado** pelo workflow pessoal e não precisa de credenciais.
