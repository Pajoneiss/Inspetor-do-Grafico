# Capítulo 02: Price Action Avançado
## Lendo a Linguagem Pura do Mercado

> *"O preço é a única coisa que paga."* — Trader Anônimo

Price Action (Ação do Preço) é a arte de ler o mercado sem indicadores poluindo a tela. É entender a história que as velas (Candlesticks) estão contando em tempo real.

O **Inspetor do Gráfico** é, na sua essência, um bot de Price Action. Ele olha para *Highs*, *Lows*, *Opens* e *Closes* antes de olhar para qualquer média móvel.

---

## 1. Candlesticks: A Batalha em Tempo Real
Cada vela é um resumo de uma batalha entre Compradores (Touros) e Vendedores (Ursos) em um determinado período de tempo.

### Anatomia da Vela
*   **Corpo:** A distância entre Abertura e Fechamento. Corpo grande = Convicção. Corpo pequeno = Indecisão.
*   **Sombra (Wick/Pavio):** Rejeição. Mostra até onde o preço foi, mas não conseguiu ficar.

### Padrões de Reversão Poderosos (Que o Bot Detecta)

#### O Martelo (Hammer) e Pinbar
*   **Visual:** Corpo pequeno no topo e uma sombra longa embaixo (pelo menos 2x o tamanho do corpo).
*   **História:** Os vendedores derrubaram o preço com força, mas os compradores rejeitaram essa queda e empurraram tudo de volta para cima antes do fechamento.
*   **Significado:** Forte sinal de alta, especialmente se aparecer em um suporte ou Fundo Duplo.

#### Engolfo (Engulfing)
*   **Visual:** Uma vela pequena (ex: vermelha) é completamente "engolida" pela vela seguinte (ex: verde gigante).
*   **História:** A força oposta entrou com tanta violência que anulou completamente a negociação anterior.
*   **Significado:** Reversão imediata de tendência. O Engolfo de Alta no fundo é um dos sinais favoritos do Inspetor.

#### Doji
*   **Visual:** Abertura e fechamento quase iguais. Parece uma cruz.
*   **História:** Empate técnico. Touros e Ursos brigaram, mas ninguém ganhou.
*   **Significado:** Indecisão. Geralmente precede uma grande explosão de movimento ou uma reversão.

#### Estrela da Manhã (Morning Star) 
*   **Visual:** 3 Velas. (1) Vela vermelha forte -> (2) Vela pequena (pião/indecisão) -> (3) Vela verde forte que fecha dentro da primeira vermelha.
*   **História:** A queda cansou, o mercado parou para pensar, e a compra assumiu.

---

## 2. Padrões Gráficos Clássicos
O comportamento humano se repete, formando desenhos no gráfico que antecipam movimentos.

### Padrões de Continuação
Mostram que o mercado está apenas descansando antes de seguir a tendência.
*   **Bandeira (Flag):** Um mastro forte seguido de um canalzinho lateral contra a tendência. Rompimento a favor do mastro.
*   **Triângulo Ascendente:** Topos na mesma altura (resistência reta) e fundos cada vez mais altos. Compradores estão ficando agressivos. Rompe para cima.

### Padrões de Reversão
Mostram que a tendência acabou.
*   **OCO (Ombro-Cabeça-Ombro):** Um topo, um topo mais alto (cabeça), e um topo menor (ombro). Mostra que a força compradora falhou em fazer um novo topo mais alto na terceira tentativa. Queda iminente.
*   **Fundo Duplo (W) e Topo Duplo (M):** O preço bate duas vezes no mesmo nível e não passa.

---

## 3. Pivot Points & Suporte/Resistência
O mercado tem memória. Níveis onde houve muita briga no passado tendem a gerar briga no futuro.

### Pivot Points (Calculados Automaticamente pelo Bot)
São níveis matemáticos baseados no dia anterior (Máxima, Mínima, Fechamento).
*   **Pivot Central (P):** O equilíbrio do dia. Acima dele é Bullish, abaixo é Bearish.
*   **Suportes (S1, S2, S3):** Onde compradores devem aparecer.
*   **Resistências (R1, R2, R3):** Onde vendedores devem aparecer.
*   **O Segredo:** Se o preço rompe o R1, ele geralmente busca o R2. Se falha no R1, volta para o P.

### Suporte e Resistência Dinâmicos
Além de linhas horizontais, usamos linhas de tendência (LTA/LTB) para ver onde o preço está sendo "segurado" diagonalmente.

---

## 4. Como o Inspetor Aplica Price Action
Diferente de humanos que podem "imaginar" um padrão onde não existe, o Bot usa regras rígidas de geometria.
1.  Ele calcula o tamanho do corpo e da sombra em pixels/centavos exatos.
2.  Para ele, um Martelo só é um Martelo se a sombra for matematicamente maior que 2x o corpo.
3.  Ele combina isso com a região. Um Martelo no meio do nada é ignorado. Um Martelo em cima do Pivot S1 é um sinal de **Alta Probabilidade**.

Este é o poder da automação: **Precisão Cirúrgica sem Viés Emocional.**
