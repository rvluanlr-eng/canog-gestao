# Integração da vistoria digital ao PDF de conferência

- A cópia de conferência do contrato (`GET /contracts/{id}/review-copy.pdf`) agora inclui uma página complementar com os 13 itens da vistoria digital, seus estados, acessórios, observações e data de registro.
- Se não houver vistoria, o PDF informa explicitamente que ela não foi registrada.
- O texto do Anexo I original é preservado. O relatório digital é um complemento e **não** preenche automaticamente as caixas de seleção ou assinaturas do anexo jurídico.
- A consulta continua restrita a administradores da mesma loja.
- Teste de integração extrai texto do PDF e confere os campos e a presença do Anexo I.
- O contrato definitivo continua sujeito à revisão jurídica e a validação do frontend em ambiente real permanece pendente.
