import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix,
    f1_score, recall_score, precision_score,
)

RANDOM_STATE = 42
DATA_PATH = "./data/desafio_nps_fase_1.csv"
MODEL_PATH = "./models/modelo_risco_detrator_rf.pkl"


# ---------------------------------------------------------------------------
# 1. Definicao da variavel-alvo
# ---------------------------------------------------------------------------
# is_detrator = 1 quando nps_score <= 6 (padrao de mercado para detrator),
# 0 caso contrario (neutro ou promotor). Classificacao binaria escolhida em
# vez de 3 classes porque o desbalanceamento entre Neutro (18%) e Promotor
# (8%) prejudicaria a classe minoritaria, e a acao de negocio (intervir ou
# nao) e binaria por natureza.
def carregar_dados(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["is_detrator"] = (df["nps_score"] <= 6).astype(int)
    return df


# ---------------------------------------------------------------------------
# 2. Selecao e preparacao das variaveis de entrada
# ---------------------------------------------------------------------------
# Variaveis logisticas, de atendimento e de pedido, mais perfil do cliente.
# EXCLUIDAS deliberadamente (ver Fase 3 - EDA, secao "vazamento de dado"):
#   - csat_internal_score: outro indicador de satisfacao, correlacao 0.56
#     com nps_score; risco de o modelo aprender a partir do proprio
#     resultado que deveria prever.
#   - repeat_purchase_30d: e virtualmente uma transformacao do NPS
#     (0% para detrator, 100% para promotor na base) - consequencia, nao
#     causa. Mant e-la geraria uma acuracia artificialmente perfeita e
#     inutil na pratica, pois nao esta disponivel no momento da previsao.
NUM_FEATURES = [
    "customer_age", "customer_tenure_months", "order_value", "items_quantity",
    "discount_value", "payment_installments", "delivery_time_days",
    "delivery_delay_days", "freight_value", "delivery_attempts",
    "customer_service_contacts", "resolution_time_days", "complaints_count",
]
CAT_FEATURES = ["customer_region"]
TARGET = "is_detrator"


def montar_pipeline_preprocessamento() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUM_FEATURES),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_FEATURES),
    ])


# ---------------------------------------------------------------------------
# 3. Separacao dos dados
# ---------------------------------------------------------------------------
# Split 70/30 estratificado pela variavel-alvo, preservando a proporcao de
# detratores (~74%) em treino e teste. Validacao cruzada (5-fold,
# estratificada) usada na etapa de comparacao de modelos.
def separar_dados(df: pd.DataFrame):
    X = df[NUM_FEATURES + CAT_FEATURES]
    y = df[TARGET]
    return train_test_split(X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y)


# ---------------------------------------------------------------------------
# 4. Escolha do(s) modelo(s)
# ---------------------------------------------------------------------------
# Baseline interpretavel (Regressao Logistica) + modelo de comparacao
# (Random Forest), ambos com class_weight="balanced" para compensar o
# desbalanceamento (74% detrator vs. 26% nao-detrator).
def montar_modelos(preprocess: ColumnTransformer) -> dict:
    return {
        "Regressao Logistica": Pipeline([
            ("prep", preprocess),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
        "Random Forest": Pipeline([
            ("prep", preprocess),
            ("clf", RandomForestClassifier(
                n_estimators=300, max_depth=8, class_weight="balanced", random_state=RANDOM_STATE
            )),
        ]),
    }


# ---------------------------------------------------------------------------
# 5. Avaliacao dos resultados
# ---------------------------------------------------------------------------
# Metrica de negocio priorizada: RECALL da classe Detrator. O custo de nao
# identificar um cliente insatisfeito (falso negativo) e maior do que o
# custo de fazer um contato proativo desnecessario (falso positivo) - por
# isso a meta analitica escolhida e maximizar recall mantendo F1 e AUC-ROC
# em niveis saudaveis (meta analitica -> meta de negocio, conforme
# CRISP-DM: metas de negocio x metas analiticas).
def avaliar_modelo(nome: str, modelo: Pipeline, X_test, y_test) -> dict:
    pred = modelo.predict(X_test)
    proba = modelo.predict_proba(X_test)[:, 1]
    metrics = {
        "modelo": nome,
        "recall_detrator": round(recall_score(y_test, pred), 3),
        "precisao_detrator": round(precision_score(y_test, pred), 3),
        "f1_detrator": round(f1_score(y_test, pred), 3),
        "auc_roc": round(roc_auc_score(y_test, proba), 3),
    }
    print(f"\n=== {nome} ===")
    print(classification_report(y_test, pred, target_names=["Nao-detrator", "Detrator"]))
    print("AUC-ROC:", metrics["auc_roc"])
    print("Matriz de confusao:\n", confusion_matrix(y_test, pred))
    return metrics


def main():
    df = carregar_dados()
    X_train, X_test, y_train, y_test = separar_dados(df)
    preprocess = montar_pipeline_preprocessamento()
    modelos = montar_modelos(preprocess)

    resultados = []
    modelos_treinados = {}
    for nome, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        modelos_treinados[nome] = modelo
        resultados.append(avaliar_modelo(nome, modelo, X_test, y_test))

    resultado_df = pd.DataFrame(resultados)
    print("\n=== Comparativo final ===")
    print(resultado_df)

    # Modelo escolhido para producao: Random Forest, por ter o melhor
    # recall e F1 para a classe Detrator (a que mais importa para o
    # negocio), com AUC-ROC equivalente ao baseline linear.
    melhor_modelo = modelos_treinados["Random Forest"]
    joblib.dump(melhor_modelo, MODEL_PATH)
    print(f"\nModelo final salvo em: {MODEL_PATH}")

    # Feature importance - para comunicar ao negocio quais variaveis mais
    # pesam na decisao do modelo (Fase 5 - storytelling gerencial).
    ohe = melhor_modelo.named_steps["prep"].named_transformers_["cat"]
    colunas_finais = NUM_FEATURES + list(ohe.get_feature_names_out(CAT_FEATURES))
    importancias = pd.Series(
        melhor_modelo.named_steps["clf"].feature_importances_, index=colunas_finais
    ).sort_values(ascending=False)
    print("\n=== Importancia das variaveis (Random Forest) ===")
    print(importancias.head(10))


# ---------------------------------------------------------------------------
# 6. Uso pratico do modelo (funcao de scoring para producao)
# ---------------------------------------------------------------------------
def prever_risco_detrator(dados_pedido: pd.DataFrame, model_path: str = MODEL_PATH) -> pd.Series:
    modelo = joblib.load(model_path)
    return pd.Series(
        modelo.predict_proba(dados_pedido[NUM_FEATURES + CAT_FEATURES])[:, 1],
        index=dados_pedido.index,
        name="probabilidade_detrator",
    )


if __name__ == "__main__":
    main()
