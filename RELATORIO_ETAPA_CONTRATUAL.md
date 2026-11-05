# CANOG Gestão — etapa contratual

## Base
Projeto derivado de `CANOG_Gestao_simulador_duas_modalidades.zip`.

## Implementado
- Marcadores explícitos no modelo contratual extraído do PDF original, substituindo os campos genéricos X identificados sem reescrever cláusulas.
- Tabela `contract_legal_details`, segregada por loja, para CEP, estado civil, profissão, taxa de ativação, data de assinatura prevista, término e vistoria.
- Endpoint `PUT /contracts/{id}/legal-details` limitado a administradores e contratos em rascunho.
- Emissão da minuta somente após preenchimento dos dados obrigatórios e ausência de marcadores não resolvidos.
- Tela de contratos com formulário de dados jurídicos e botão para baixar minuta.
- Teste novo com cliente e fiador fictícios que verifica gravação dos dados, substituição dos campos e geração de PDF contendo o Anexo I.

## Testes
- `pytest -q`: 14 passaram.
- `npm run build`: não executou; o comando `vite` não está instalado no ambiente. Não há confirmação de compilação do frontend.

## Limites importantes
- O PDF é uma minuta para revisão, não um contrato juridicamente aprovado ou pronto para assinatura.
- A extração do texto original foi preservada, mas a diagramação/paginação do PDF gerado pode divergir das 16 páginas do documento de origem.
- O Anexo I mantém campos de vistoria manual e não é um checklist digital preenchido automaticamente.
- Datas e taxa de ativação são informadas explicitamente, não presumidas.
- O modelo original contém nomes/dados fixos de representantes e testemunhas que devem ser revisados antes de uso real.
- Não houve homologação em hospedagem real.
