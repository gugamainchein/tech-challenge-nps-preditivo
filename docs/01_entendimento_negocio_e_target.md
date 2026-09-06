# Fase 1 e 2 — Entendimento do Negócio e Definição da Target

**Projeto:** Tech Challenge Fase 1 — Case NPS Preditivo
**Grupo:** Gustavo Mainchein, Gustavo Lopes, Gustavo Valentim
**Correspondência no CRISP-DM:** Business Understanding

---

## Fase 1 — Entendimento do negócio

### Qual problema de negócio está sendo resolvido?

A empresa cresceu em volume de pedidos, mas hoje mede a satisfação do cliente apenas de forma reativa, por meio de uma pesquisa de NPS aplicada após o fim da jornada de compra. Essa abordagem não permite antecipar problemas nem agir antes que o cliente já esteja insatisfeito.

A análise da base de 2.500 pedidos confirma que esse não é um problema teórico: o **NPS geral da empresa está em -66** (74% de detratores, 18% de neutros e apenas 8% de promotores) — um cenário crítico e generalizado, não um conjunto de incidentes isolados.

O problema de negócio central é: **identificar, a partir de dados operacionais já disponíveis no momento da entrega, quais clientes estão em risco de se tornar detratores, para permitir intervenção proativa antes da aplicação da pesquisa de NPS.**

### Por que o NPS é importante para um e-commerce?

Em um mercado de baixa fidelidade e alta comoditização como o e-commerce nacional, o produto muitas vezes é o mesmo em qualquer loja, o
diferencial está na experiência de compra. O NPS funciona como termômetro dessa experiência e está diretamente ligado a três consequências de negócio:

- **Recompra:** clientes promotores tendem a comprar novamente com maior frequência, elevando o LTV; detratores reduzem a recorrência e aumentam o churn. Isso é visível na própria base: entre os promotores, o indicador de recompra em 30 dias é de 100%, contra 0% entre os detratores.
- **Boca a boca:** promotores recomendam espontaneamente a marca, reduzindo o CAC via indicação orgânica; detratores geram propaganda negativa, elevando o CAC de novos clientes e a exposição reputacional.
- **Market share:** em mercados competitivos, a experiência do cliente é um diferencial competitivo tão relevante quanto preço. Com 74% de detratores, a empresa está estruturalmente vulnerável a perder participação de mercado para concorrentes com operação logística e atendimento mais consistentes.

### Quais áreas poderiam se beneficiar desses insights?

- **Logística:** priorização de rotas, transportadoras e centros de distribuição com maior taxa de atraso — fator identificado como o principal driver de insatisfação (ver Fase 3).
- **Atendimento ao cliente:** redesenho de SLA de resolução e de scripts de contato proativo, já que cada contato adicional do cliente com o atendimento reduz a nota média de NPS.
- **Produto:** identificação de categorias com maior índice de reclamação (quando o dado de categoria estiver disponível em versões futuras da base).
- **Pricing/Comercial:** embora a EDA tenha mostrado que valor do pedido, desconto e parcelamento não impactam o NPS nesta base, a área comercial ainda se beneficia de acompanhar esse indicador para não confundir estratégia de preço com estratégia de experiência.
- **Estratégia/C-level:** uso do NPS e do score de risco de detrator como parte de OKRs de experiência do cliente e como insumo para priorização de investimentos operacionais.

### Reflexão: como o NPS impacta recompra, boca a boca e market share?

Na base analisada, o padrão é claríssimo: recompra em 30 dias é praticamente binária em função da categoria de NPS (0% entre detratores,
~4% entre neutros, 100% entre promotores). Isso significa que, se a empresa não reverter o quadro atual de 74% de detratores, a maior parte da base de clientes tende a não recomprar — um risco direto de receita recorrente. O boca a boca negativo tende a amplificar esse efeito, elevando o custo de reposição desses clientes por meio de aquisição paga. Em conjunto, isso pressiona o market share, pois a empresa passa a depender de aquisição cara para repor uma base que não se sustenta organicamente.

### Quais indicadores de mercado poderiam complementar essa análise?

- Benchmark de NPS do setor de e-commerce brasileiro, para dimensionar o quão abaixo da média a empresa está (um NPS de -66 é, de forma geral, considerado crítico em qualquer benchmark de mercado).
- Indicadores de SLA logístico do setor (prazo médio de entrega e taxa de atraso da concorrência).
- Dados de reclamações públicas (ex.: Reclame Aqui) como proxy de percepção de mercado.
- CAC e LTV setoriais, para traduzir a perda de recompra identificada na base em impacto financeiro estimado.

---

## Fase 2 — Definição da target

### Qual variável representa a satisfação do cliente?

A variável **`nps_score`** (nota de 0 a 10) representa diretamente a satisfação do cliente. É a métrica que o próprio negócio já usa oficialmente como termômetro de experiência, e foi a base de toda a análise deste projeto.

### Por que ela foi escolhida?

O NPS é um padrão de mercado amplamente reconhecido, fácil de comunicar para qualquer área do negócio e permite comparação com benchmarks externos do setor. Duas outras variáveis da base — `csat_internal_score` e `repeat_purchase_30d` — também se correlacionam com satisfação, mas foram descartadas como alvo ou como preditoras (ver `02_eda.ipynb`, seção "vazamento de dado"), pois `csat_internal_score` é outro indicador de satisfação (correlação de 0,56 com `nps_score`) e `repeat_purchase_30d` comporta-se como consequência quase determinística do NPS (0% de recompra entre detratores e 100% entre promotores na base), não como uma causa independente.

### Em que momento da jornada essa informação é coletada?

A pesquisa de NPS é aplicada **após o encerramento da jornada de compra**, depois que o pedido já foi entregue. Esse é o ponto de dor identificado no case: a coleta é tardia, o que limita a ação preventiva. É exatamente essa limitação que justifica a Fase 4 deste projeto: um modelo preditivo que estima o risco de detrator a partir de dados já disponíveis no momento da entrega, antes da pesquisa ser respondida.

### Existe algum risco de usar essa variável de forma inadequada?

- **Viés de resposta:** nem todo cliente responde à pesquisa; tendem a responder mais os extremos, o que pode distorcer a distribuição real do NPS.
- **Defasagem temporal:** por ser coletado logo após a entrega, o NPS pode refletir um evento pontual (um atraso isolado) e não necessariamente a relação de longo prazo do cliente com a marca.
- **Correlação vs. causalidade:** os fatores identificados na EDA (atraso, reclamações, contatos de atendimento) estão fortemente associados a notas baixas, mas associação não é prova de causa única, outros fatores não capturados na base podem influenciar ambos.
- **Risco de otimização de métrica:** se a empresa passar a agir apenas para "melhorar o número" (ex.: incentivar respostas só de clientes satisfeitos), perde-se o valor do indicador como termômetro real da experiência.
- **Uso indevido do modelo preditivo:** tratar a probabilidade estimada pelo modelo (Fase 4) como certeza absoluta, em vez de uma estimativa de risco que apoia — mas não substitui — o julgamento humano da equipe de atendimento.
