# Tech Challenge — Fase 1 | Case NPS Preditivo

- **Grupo:** Gustavo Mainchein (RM377234), Gustavo Lopes, Gustavo Valentim
- **Curso:** POSTECH — FIAP

## Objetivo do projeto

A empresa do case coleta o NPS apenas após o encerramento da jornada de compra, o que impede ações preventivas. Este projeto tem dois objetivos:

1. **Entender**, a partir dos dados operacionais de pedidos, logística e atendimento, quais fatores mais influenciam a satisfação do cliente (Fases 1 a 3, obrigatórias).
2. **Propor e implementar** uma estratégia preditiva capaz de estimar o risco de um cliente se tornar detrator _antes_ da pesquisa de NPS ser respondida, permitindo ação proativa da área de Experiência do Cliente (Fase 4, opcional — implementada neste repositório).

## Descrição da base de dados

Arquivo: `data/desafio_nps_fase_1.csv` — 2.500 pedidos, 19 colunas, sem valores nulos ou duplicados. Principais campos:

| Campo                                         | Descrição                                                                            |
| --------------------------------------------- | ------------------------------------------------------------------------------------ |
| `nps_score`                                   | Nota de satisfação (0–10), coletada após a compra — variável-alvo                    |
| `delivery_delay_days`                         | Dias de atraso na entrega                                                            |
| `customer_service_contacts`                   | Nº de contatos do cliente com o atendimento                                          |
| `complaints_count`                            | Nº de reclamações registradas                                                        |
| `resolution_time_days`                        | Tempo de resolução de problemas                                                      |
| `csat_internal_score` / `repeat_purchase_30d` | Excluídos da modelagem por risco de vazamento de dado (ver notebook de EDA, seção 7) |

## Metodologia utilizada

O projeto seguiu o **CRISP-DM**, com as fases mapeadas da seguinte forma:

| Fase do projeto            | Fase do CRISP-DM                         | Artefato                                   |
| -------------------------- | ---------------------------------------- | ------------------------------------------ |
| Entendimento do negócio    | Business Understanding                   | `docs/01_entendimento_negocio_e_target.md` |
| Definição da target        | Business Understanding                   | `docs/01_entendimento_negocio_e_target.md` |
| Análise Exploratória (EDA) | Data Understanding                       | `notebooks/02_eda.ipynb`                   |
| Estratégia preditiva       | Data Preparation + Modeling + Evaluation | `notebooks/03_modelagem_preditiva.py`      |

### Principais achados:

- NPS geral da base: **-66** (74% detratores, 18% neutros, 8% promotores).
- **Atraso na entrega** é o fator isoladamente mais associado à insatisfação (correlação de -0,60 com `nps_score`). Ponto de ruptura: a partir de **3 dias de atraso, 93% dos clientes viram detratores**.
- **Reclamações e contatos com o atendimento** são o segundo fator mais relevante (correlação de -0,50 e -0,35, respectivamente).
- Valor do pedido, forma de pagamento, idade e região do cliente **não** explicam variações relevantes de NPS — o problema é operacional, não comercial ou demográfico.

### Modelo preditivo

Classificação binária (Detrator vs. Não-detrator), comparando Regressão Logística (baseline interpretável) e Random Forest (modelo final). Resultado no conjunto de teste (30% da base, estratificado):

| Modelo                        | Recall (Detrator) | F1 (Detrator) | AUC-ROC |
| ----------------------------- | ----------------- | ------------- | ------- |
| Regressão Logística           | 0,78              | 0,84          | 0,871   |
| **Random Forest (escolhido)** | **0,87**          | **0,88**      | 0,869   |

O Random Forest foi escolhido por priorizar o **recall da classe Detrator**. O custo de negócio de não identificar um cliente insatisfeito é maior do que o custo de um contato proativo desnecessário.

## Como reproduzir os resultados

```bash
# 1. Criar um ambiente virtual Python
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip3 install -r requirements.txt

# 3. Rodar a análise exploratória (gera os gráficos em reports/)
jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb

# 4. Rodar a pipeline de modelagem (treina, avalia e salva o modelo em models/)
python3 notebooks/03_modelagem_preditiva.py
```

O modelo final fica salvo em `models/modelo_risco_detrator_rf.pkl` e pode ser reutilizado via a função `prever_risco_detrator()` definida em `notebooks/03_modelagem_preditiva.py`, que recebe os dados de um pedido recém-entregue e retorna a probabilidade estimada de o cliente se tornar detrator.

## Estrutura de pastas

```
├── data/           # base de dados (CSV)
├── notebooks/      # EDA (.ipynb) e pipeline de modelagem (.py)
├── models/         # modelo treinado (.pkl)
├── reports/        # gráficos exportados da EDA
├── docs/           # entendimento do negócio e target
└── README.md
```

## Limitações e riscos:

- O NPS é coletado apenas para quem responde à pesquisa, o que pode introduzir viés de resposta.
- Correlação não implica causalidade, pois os achados indicam associação forte, mas ações corretivas devem ser validadas com testes controlados quando possível.
- `csat_internal_score` e `repeat_purchase_30d` foram excluídos da modelagem por vazamento de dado. Se reintroduzidos sem cautela, geram métricas artificialmente infladas e um modelo não tão útil em produção.
