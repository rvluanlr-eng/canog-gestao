# CANOG Gestão — integração da vistoria digital

## Implementado
- Nova tabela `device_inspections`, vinculada a contrato e empresa.
- `GET /contracts/{id}/inspection` para recuperar a vistoria e `PUT /contracts/{id}/inspection` para gravá-la.
- Treze itens de verificação, cada um com situação *Conforme*, *Com problema* ou *Não testado*.
- Observações obrigatórias quando qualquer item apresenta problema.
- Vistoria editável somente durante o rascunho e somente pelo administrador.
- Registro de auditoria e indicação da existência de vistoria no checklist contratual.
- Tela de vistoria digital integrada à página de contratos.

## Verificação executada
- `pytest -q`: **15 testes passaram**, incluindo o teste específico de vistoria com autenticação, persistência e validação.
- `python -m compileall`: passou.
- Compilação do frontend: **não executada**, pois o npm não conseguiu obter `lucide-react` (DNS `EAI_AGAIN`), e o pacote também não estava no cache offline. A interface requer validação após instalação das dependências.

## Implantação em banco existente
1. Fazer backup do banco.
2. Configurar `DATABASE_URL` e as variáveis da API.
3. Executar `python backend/migrate_inspection.py` a partir da raiz do projeto.
4. Instalar as dependências do frontend e executar `npm run build` dentro de `frontend`.

## Limitações
- A vistoria digital não substitui a assinatura física/eletrônica do Anexo I, nem a revisão jurídica.
- A ativação ainda não exige a vistoria digital; ela é informativa no checklist para preservar o comportamento existente até validação operacional.
- O PDF contratual ainda não incorpora os valores da vistoria digital automaticamente.
- O frontend não foi validado por compilação ou teste em navegador.
- Não é uma versão pronta para homologação comercial.
