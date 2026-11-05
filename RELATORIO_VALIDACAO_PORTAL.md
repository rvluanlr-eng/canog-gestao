# CANOG Gestão — verificação do Portal do Cliente

## Alteração aplicada
O envio de comprovante PIX no portal foi separado do fluxo `act()` do painel administrativo. Após o upload, o portal consulta `/portal/me` usando exclusivamente o token do cliente, atualiza a lista de parcelas e apresenta mensagem de sucesso somente após confirmação da API. A ausência de arquivo selecionado não dispara envio.

## Verificações realizadas
- 4 testes direcionados passaram: fluxo do portal, regressão de login/upload e integração financeira por correspondência de endpoints.
- `npm install` falhou com `EAI_AGAIN` ao consultar `registry.npmjs.org`. **A compilação React/Vite e os testes no navegador não foram realizados.**
- A execução conjunta da suíte de testes foi iniciada, mas não concluiu dentro do tempo disponível; não é correto informar aprovação da suíte completa nesta etapa.

## Pendências para homologação
1. Instalar dependências, executar `npm run build` e testar no navegador.
2. Testar fluxo real de ponta a ponta com banco PostgreSQL e armazenamento R2 configurados.
3. Revisão jurídica final do contrato e validação de assinatura/transferência.

Este pacote **não é uma versão homologada**.
