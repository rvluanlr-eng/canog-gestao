# CANOG Gestão — correções de integração da interface

## Alterações realizadas
- Login administrativo e do portal deixam de chamar a rotina de atualização de dados com o token antigo. A atualização administrativa é acionada pelo efeito associado ao novo token.
- Upload de documentos reinicializa o formulário após a resposta HTTP de sucesso, sem depender de um corpo de resposta truthy; atualiza a listagem e o painel.
- Dois testes de regressão estática verificam esses comportamentos.

## Evidências e limitações
- `python -m pytest -q`: 19 testes aprovados (incluindo os dois novos).
- `npm install --fetch-retries=0 --fetch-timeout=12000`: falhou com EAI_AGAIN no acesso a registry.npmjs.org/lucide-react.
- Não foi possível executar `vite build` nem teste visual de navegador.
- Testes estáticos de interface não substituem testes funcionais reais.
- Contrato definitivo, revisão jurídica e implantação real continuam pendentes.

## Próximo passo para homologação
Instalar dependências em ambiente com acesso ao npm, executar `npm run build`, iniciar API e frontend com dados fictícios e percorrer login, cadastro, documentos, contrato, pagamento e portal do cliente.
