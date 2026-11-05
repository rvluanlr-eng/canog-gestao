# CANOG Gestão — integração do fluxo de comprovantes PIX

## Alteração implementada
A tela Financeiro agora diferencia as operações:
- Parcela `pending`: confirmação manual do recebimento, com confirmação explícita do operador.
- Parcela `review`: aprovação do comprovante e quitação através do endpoint `POST /installments/{id}/approve-proof`, ou rejeição com motivo.
- Parcela `paid`: estorno com motivo.

O fluxo exige conferência humana do crédito na conta bancária. O envio de comprovante, por si só, não quita a parcela.

## Validação
- 17 testes de backend e consistência da interface passaram.
- Foi adicionado teste estático para garantir que os endpoints financeiros acionados pela interface existem na API.
- A compilação do frontend **não foi realizada**: `npm install` falhou com `EAI_AGAIN` ao acessar `registry.npmjs.org`.
- Não foram realizados testes no navegador ou com PostgreSQL/R2 reais.

## Bloqueios de homologação
Compilação e teste ponta a ponta do frontend; revisão jurídica do contrato; implantação em ambiente de testes e verificação de permissões e armazenamento privado em infraestrutura real.

**Este pacote não é uma versão de produção homologada.**
