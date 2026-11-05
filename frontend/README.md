# CANOG Gestão — versão 0.1 (protótipo funcional de interface)

Primeira entrega do sistema de gestão CANOG, com identidade visual inspirada na marca fornecida.

## Executar

Requer Node.js 20.19+ ou 22.12+ e npm.

```bash
npm install
npm run dev
```

Abrir o endereço exibido pelo Vite (normalmente http://localhost:5173).

Para gerar os arquivos estáticos: `npm run build`.

## O que funciona nesta versão

- Navegação responsiva, dashboard demonstrativo e menu.
- Cadastro temporário de clientes e aparelhos (apenas na memória da página).
- Busca nas tabelas de clientes e estoque.
- Simulador inicial com cálculo demonstrativo de parcelas pelo método Price, taxa por período e resumo financeiro.

## Limitações importantes

- **Não é um sistema pronto para produção.** Não possui autenticação, banco de dados, API, isolamento entre empresas, upload seguro ou geração de contrato.
- Cadastros desaparecem ao recarregar a página. Não inserir CPF, RG, dados bancários ou dados reais.
- Dados do dashboard e tabelas iniciais são fictícios.
- O simulador original exibido nas imagens não fornece a fórmula completa. O cálculo Price é provisório e **não deve ser utilizado para fechar negociações** até a validação com o proprietário.
- O modelo contratual fornecido exige revisão jurídica antes de automatização e uso real.
- Logo original não foi incorporada: o arquivo recebido era uma captura de tela; foi criada uma marca tipográfica provisória.

## Próximas etapas técnicas

1. Backend FastAPI, banco PostgreSQL e isolamento por organização em cada consulta.
2. Autenticação com perfis de administrador e cliente, trilha de auditoria.
3. Cadastros persistentes, aparelhos por IMEI, fiadores e negociações em rascunho.
4. Upload privado de documentos, com validação obrigatória antes da ativação.
5. Simulador homologado, geração de contrato e termo de vistoria.
6. Parcelas, baixa administrativa, anexos de comprovantes e portal do cliente com PIX.

Não hospedar arquivos de documentos pessoais em diretórios públicos.
