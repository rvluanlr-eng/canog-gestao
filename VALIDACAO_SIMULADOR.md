# Validação do simulador CANOG

## O que foi implementado

- `price`: Tabela Price com juros por período de parcela, arredondamento em centavos e ajuste da última parcela.
- `negotiated`: parcela fixa informada pelo operador, sem inferir juros contratuais; o sistema calcula saldo, total das parcelas e margem bruta projetada.
- Entrada em dinheiro e avaliação de aparelho recebido são exibidas separadamente.
- Bloqueio de entrada maior que o preço e de parcelamento negociado inferior ao saldo financiado.
- Ambos os modos declaram `validated_against_original: false` porque a fórmula original não está disponível.

## Exemplo de referência

Preço R$ 2.500,00; custo R$ 1.800,00; entrada em dinheiro R$ 875,00; 12 parcelas negociadas de R$ 265,00.

- Saldo: R$ 1.625,00
- Parcelas: R$ 3.180,00
- Total econômico da negociação: R$ 4.055,00
- Margem bruta projetada: R$ 2.255,00

A diferença para o lucro de R$ 2.260,00 mostrado na referência original permanece **não explicada**. Não foi introduzido ajuste fictício de R$ 5,00.

## Limites

- A margem não é lucro realizado nem caixa recebido; a avaliação do aparelho na troca não equivale a dinheiro.
- A modalidade negociada não atribui juros nem amortização por parcela sem taxa definida.
- Não foram validados o payback e o ROI do simulador original.
- Os testes automatizados da API passaram; a compilação do frontend não foi verificada neste ciclo.
- Este pacote **não é uma versão pronta para homologação**.
