# Próxima etapa: feeds oficiais de afiliados

O monitor GitHub Actions funciona, mas a Farfetch retorna HTTP 403; nenhum preço foi confirmado. Não contornar bloqueios.

1. Cadastrar o Maison Privé como publisher na Awin e solicitar participação em anunciantes de moda e beleza com feeds para o Brasil.
2. Em Toolbox > Create-a-Feed, obter URL de feed CSV. A chave de feed difere do token normal de API.
3. Guardar URL e chave SOMENTE em GitHub Settings > Secrets and variables > Actions, com nome AWIN_FEED_URL. Nunca publicar credenciais.
4. Ler CSV e validar moeda BRL, ID, nome, marca, preço, preço antigo, estoque, imagem, link e data.
5. Executar consulta pelo workflow horário; comparar apenas preços confirmados do mesmo produto.
6. Atualizar a vitrine e ativar alertas somente após uma consulta real bem-sucedida.

Alternativa: Admitad com feeds XML para programas aprovados. Lomadee pode ajudar com links e cupons; verificar disponibilidade de feed.

Status: planejamento técnico, sem credenciais ou feed de afiliado conectado. Manter Firecrawl até validar a substituição.

Fontes: https://www.awin.com/br/faq ; https://help.awin.com/developers/docs/product-feed-list-download
