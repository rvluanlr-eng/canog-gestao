# CANOG Gestão — relatório verificável de execução

## Resultado
**Não liberado como versão 1.0 / não apto a produção.**

## Alterações desta execução
- Criado endpoint administrativo `GET /contracts/{id}/review-copy.pdf` para produzir cópia integral do texto contratual, com Anexo I, marcação visível dos campos ausentes e indicação de **NÃO ASSINAR**.
- Mantido o bloqueio de `legal-draft.pdf` quando existem dados ou marcadores jurídicos incompletos. A cópia para conferência **não** remove nem substitui esse bloqueio.
- Atualizado o botão de contratos na interface para baixar a cópia de conferência, sem alegar que seja contrato definitivo.
- Incluído teste automatizado que cria um contrato, gera o PDF, verifica seu conteúdo, o Anexo I e a presença dos campos pendentes.

## Evidências
- `python -m pytest -q`: **12 passed**.
- O teste da cópia contratual confirmou PDF válido e texto extraível, incluindo nome, fiador, aviso de não assinatura e Anexo I.
- `npm install --offline`: **falhou** por ausência de `lucide-react` no cache npm; build frontend não executado.

## Bloqueios objetivos
1. O contrato original possui campos genéricos não identificados e dados jurídicos que não podem ser preenchidos por suposição. Revisão jurídica e dados reais necessários para liberar assinatura.
2. O simulador Price ainda não tem resultados de referência comprovados equivalentes à planilha original.
3. O frontend não foi compilado; não há testes ponta a ponta comprovados.
4. PostgreSQL, R2 e implantação real não foram configurados/testados.
5. Relatórios financeiros ainda exigem conciliação de entradas, trocas, despesas e estornos.

**Não utilizar este código com dados reais nem emitir contratos para assinatura.**
