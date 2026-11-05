# Validação de build do CANOG Gestão no GitHub

Este pacote contém `.github/workflows/validacao.yml`, que executa em paralelo:

1. Testes automatizados da API em Python 3.11;
2. Instalação de dependências e build do React/Vite em Node.js 22.

## Como executar

1. Crie um **repositório privado** no GitHub e envie o conteúdo desta pasta para a raiz do repositório (incluindo a pasta oculta `.github`). **Não envie arquivos `.env`, credenciais, documentos de clientes ou banco real**.
2. Abra **Actions** > **CANOG - validacao tecnica** > **Run workflow**.
3. Aguarde os jobs `backend` e `frontend`. O resultado só será considerado aprovado se ambos estiverem verdes.
4. Se o frontend passar, baixe o artefato `canog-frontend-build` na página da execução. É um build técnico com URL de API fictícia, **não deve ser publicado como site de produção**.
5. Se algum job falhar, consulte os logs do job correspondente para corrigir a causa antes da homologação.

## Verificação executada neste ambiente

- `python -m pytest -q`: **20 passed**.
- `npm install --no-audit --no-fund --fetch-retries=0`: falhou com `EAI_AGAIN registry.npmjs.org`; build React ainda **não verificado**.
- Workflow YAML analisado sintaticamente; execução no GitHub **não realizada**.

## Critérios ainda pendentes

- Build React executado com sucesso e teste em navegador com API real de homologação.
- Teste completo dos fluxos com dados fictícios.
- Revisão jurídica do contrato e controles de produção (backups, segurança, LGPD).

**Não liberar para uso comercial apenas porque o workflow passou.**
