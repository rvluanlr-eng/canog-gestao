# CANOG Gestão — código integrado v0.5 (pré-homologação)

Sistema web React/Vite + FastAPI/SQLAlchemy. O projeto inclui painel, cadastros, estoque por IMEI, simulador Price **provisório**, rascunhos, documentação, parcelas, PIX estático, portal do cliente, relatórios iniciais, registro de aparelho recebido como entrada, encerramento por devolução ou aquisição e trilha de auditoria.

**Não é uma versão pronta para uso com clientes reais.** Não foram executados testes end-to-end em navegador, nem auditoria de segurança, nem conferência integral do simulador e do contrato. O PDF gerado é uma **minuta**, não um contrato final validado. O encerramento por aquisição registra confirmação administrativa do valor residual, mas ainda não gera um termo de transferência juridicamente validado.

## Execução local

1. Python 3.11+ e Node.js 20+. Criar banco PostgreSQL. Para testes locais isolados, pode-se usar SQLite.
2. Backend: `cd backend && pip install -r requirements.txt`. Configure variáveis conforme `.env.example`. Crie `JWT_SECRET` longo e aleatório, `ADMIN_EMAIL` e `ADMIN_PASSWORD` forte. Execute `python bootstrap.py` **apenas uma vez em banco novo** e depois `uvicorn main:app --host 0.0.0.0 --port 8000`.
3. Frontend: `cd frontend && npm install && npm run build` (ou `npm run dev`). Configure `VITE_API_URL` com a URL pública da API.
4. API: `/docs` e `/health`.

## Hospedagem futura

- Cloudflare Pages: publicar `frontend/dist`, build `npm run build`, diretório base `frontend`, variável `VITE_API_URL` definida **durante o build**.
- Render: serviço Python, diretório base `backend`, comando `uvicorn main:app --host 0.0.0.0 --port $PORT`, configurar variáveis de ambiente e URL PostgreSQL. Banco não deve ser criado por `bootstrap.py` em toda inicialização.
- Cloudflare R2: criar bucket **privado**, preencher `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. Nunca publicar chaves no frontend. Sem R2, os uploads usam disco local (apenas para desenvolvimento).
- Configurar `CORS_ORIGINS` com a origem exata do frontend, HTTPS, backups, alertas, políticas de retenção e migrações antes de produção.

## Restrições e pendências obrigatórias

1. Conferir as fórmulas do simulador com a ferramenta original (juros, entrada parcelada, periodicidade, margem e ROI). O endpoint `/simulate` ainda usa Price provisória.
2. Rever juridicamente o contrato completo, substituir campos restantes e aprovar a geração final, incluindo o Anexo I e termo de transferência. Não assinar a minuta como contrato definitivo.
3. Implementar migrações versionadas (Alembic), política de backup/restauração, recuperação de senha, proteção contra força bruta, varredura de malware, limites de upload de vídeo e testes de autorização/segurança. Para vídeos grandes, usar upload direto privado com credenciais temporárias.
4. Corrigir o fluxo de portal multiempresa: autenticação por CPF isoladamente não é adequada para diferentes lojas com o mesmo cliente; exigir identificador da loja.
5. Executar build frontend, testes integrados em navegador, testes de carga, acessibilidade, homologação com dados fictícios e revisão LGPD antes de clientes reais.
6. A integração de emissão/confirmação bancária foi deliberadamente excluída. Baixa é exclusivamente administrativa.

## Testes automatizados

Executados com SQLite e FastAPI TestClient: login, rascunho, bloqueio de ativação incompleta, minuta PDF, acesso de portal, proteção de token, registro de aparelho de entrada, prevenção de duplicidade, checklist e trilha de auditoria. Arquivos de teste em `tests/`.

## Correção v0.6 — isolamento do portal
O login do cliente exige agora `tenant_id` (código da loja) além de CPF e senha. Isso evita autenticação ambígua quando o mesmo CPF consta em lojas diferentes. O frontend e o teste de login foram atualizados. Os testes de API passaram; o build do frontend não foi validado porque a instalação de dependências não concluiu neste ambiente. **Ainda não é uma versão completa ou liberada para produção.**


## Revisão v0.7 — proteções adicionais
- Upload de arquivos em `APP_ENV=production` exige R2 configurado; não grava em disco efêmero.
- Download/listagem de documentos e geração de minuta restritos ao administrador.
- Conferência documental utiliza o envio mais recente por categoria, evitando que um arquivo aprovado antigo encubra uma substituição pendente/rejeitada.
- Minuta detecta marcadores `{{...}}` não substituídos e impede a emissão nesse caso. Outros placeholders `XXXXX` do documento original ainda requerem revisão jurídica e preenchimento.
- **Ainda não está liberado para produção:** revisão jurídica, cálculos, testes completos de navegador, migrações, proteção contra abuso e backups.

## Revisão v0.8 — correções aplicadas em 04/11/2026
- Corrigida a execução conjunta dos testes: `python -m pytest -q` agora executa os cenários em processos isolados, cada um com banco temporário, sem colisão de CPF nem reutilização de imports.
- Caminhos dos testes tornados relativos ao projeto (não dependem de `/mnt/data`).
- Portal não aceita novo comprovante enquanto um comprovante anterior da mesma parcela aguarda conferência; evita substituição silenciosa.
- Resultado verificado localmente: **2 cenários integrados passaram**.
- Tentativa de `npm install` falhou por indisponibilidade de acesso DNS ao npm (`EAI_AGAIN`); frontend **não compilado**.
- **Ainda não é candidato à homologação**: fórmula do simulador sem validação, minuta contratual não definitiva, segurança de produção e testes no navegador pendentes. Não usar dados reais.

## Revisão v0.9 — continuidade da implementação
- Simulador: cálculo em `Decimal` com arredondamento monetário explícito, ROI informativo e rejeição de entradas superiores ao preço; a fórmula **continua provisória** até validação com a ferramenta original.
- Portal: contratos ainda em rascunho não são exibidos ao cliente.
- Teste automatizado adicional: juros zero, juros positivos, entrada inválida e identificação da fórmula provisória.
- Testes de API: três cenários isolados aprovados. Frontend e segurança de produção **não homologados**.

## Atualização v0.10 — 04/11/2026
- Corrigida a lista de conferência documental para usar somente o upload mais recente de cada categoria, assim como a validação de ativação.
- Impedido acesso do portal do cliente ao resumo de contratos ainda em rascunho.
- Restringidas operações de criação de cliente, aparelho, contrato e aprovação geral de documentos a administradores.
- Corrigidos o cálculo de vencidos com datas que possuem fuso horário e os estados de contratos apresentados no relatório financeiro.
- Verificação de duplicidade de aparelho recebido na troca agora inclui o identificador da empresa.
- Adicionado teste isolado de regressão para regras de permissão, documentos substituídos e visibilidade de rascunhos.
- Comando verificado: `python -m pytest -q` — 4 testes passaram.
- Frontend ainda NÃO validado: `npm install` falhou devido a indisponibilidade de acesso ao registry.npmjs.org (`EAI_AGAIN`); a instalação offline também falhou (`ENOTCACHED`).
- **Não é uma versão homologada:** simulador continua explicitamente provisório; contrato segue como minuta; exigem-se testes ponta a ponta, revisão jurídica e hardening de produção.

## Revisão v0.11 — integridade de minutas jurídicas
- `GET /contracts/{id}/legal-readiness` informa tokens `{{...}}` e marcadores legados `XXXXX` no modelo. Não substitui revisão jurídica.
- `GET /contracts/{id}/legal-draft.pdf` agora bloqueia geração (HTTP 422) se o modelo contiver campos genéricos, em vez de emitir documento potencialmente enganoso.
- **Pendente:** substituir os campos legados com dados verificados e revisar integralmente o contrato com profissional jurídico; o modelo atual NÃO está pronto para assinatura.

## Revisão v0.12 — alertas de vencimento e comprovantes
- `GET /reports/upcoming-due?days=7`: vencimentos dos próximos 7 dias e parcelas vencidas, com totais separados, isolados por loja, apenas contratos ativos; período permitido 1–31 dias.
- Portal impede novos comprovantes de contratos devolvidos/adquiridos/cancelados, além dos rascunhos.
- Rejeição administrativa de comprovante limpa a referência da parcela ao comprovante rejeitado; o arquivo e a trilha de auditoria permanecem preservados.
- Ainda pendente: contrato final, validação do simulador original, frontend compilado e auditoria de produção.

- Testes de cenário independentes agora usam prefixo `scenario_` para evitar colisões de importação durante coleta completa do pytest. Execute `python -m pytest -q`.

## Revisão v0.13 — simulação com cronograma e diagnóstico contratual
- `/simulate` devolve agora um cronograma Price **provisório**, parcela a parcela, com juros e amortização em centavos e ajuste de arredondamento na última prestação. Inclui total de juros e total das parcelas; a taxa informada é **por parcela**. `validated_against_original=false` continua obrigatório.
- O cronograma foi testado em seis cenários matemáticos (incluindo juros zero, saldo zero e 60 parcelas). Isso **não valida a equivalência com a planilha original**, que ainda precisa ser aferida.
- `/contracts/{id}/legal-readiness` informa também campos cadastrais ausentes (endereço, telefone, fiador, dados do aparelho e vencimento). A emissão jurídica continua bloqueada por marcadores legados e revisão jurídica pendente.
- **Importante:** o contrato da loja contém placeholders não estruturados e qualificações pessoais não armazenadas no banco. Não foi feita substituição automática insegura nem alteradas cláusulas jurídicas. O sistema **ainda não está pronto para homologação**.

## v0.15 — Verificação pré-implantação
- `GET /admin/deployment-readiness` (JWT administrativo) mostra **apenas flags** de configuração: segredo JWT, PostgreSQL, credenciais R2 presentes, CORS explícito e integridade de placeholders do contrato. Não verifica conexão R2 nem revela segredos.
- `GET /contracts/{id}/legal-readiness` e `GET /contracts/{id}/legal-draft.pdf` usam o mesmo checklist de dados essenciais. O PDF permanece bloqueado quando faltam dados ou quando o modelo possui marcadores genéricos.
- Testes: executar `pytest -q` na raiz; 8 testes passaram nesta revisão.
- **Não homologado:** contrato ainda possui placeholders, frontend sem build confirmado (npm EAI_AGAIN), cálculos não comparados com a planilha original, falta revisão de segurança em produção e revisão jurídica.

## Atualização v0.16 — comprovantes PIX
- `POST /installments/{id}/approve-proof`: administrador aprova comprovante pendente e registra quitação com auditoria.
- `POST /installments/{id}/reject-proof`: documento rejeitado permanece no histórico; parcela volta a pendente.
- `POST /installments/{id}/confirm`: não permite pular análise de comprovante.
- Execute `pytest -q` para verificar os testes, incluindo o fluxo de aprovação e rejeição.
