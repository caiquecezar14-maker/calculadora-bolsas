import streamlit as st
import pandas as pd
from io import StringIO

# Função utilitária para formatar em R$ no estilo brasileiro (milhares com . e decimais com ,)
def format_brl(value: float) -> str:
    s = f"{value:,.2f}"           # e.g. 1,234,567.89
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

st.set_page_config(page_title="Precificador de Bolsas", layout="centered")
st.title("👜 Precificador de Bolsas")
st.subheader("Ferramenta de Consultoria — Versão aprimorada")

with st.sidebar.form("custos_form"):
    st.header("Custos de Produção")
    peso_material = st.number_input(
        "Peso do material usado (g)", value=200.0, min_value=0.0, step=1.0, format="%.2f"
    )
    custo_grama = st.number_input(
        "Custo do fio (R$ por grama)", value=0.05, min_value=0.0, step=0.001, format="%.4f"
    )
    custo_acessorios = st.number_input(
        "Custo de acessórios (botões/fechos R$)", value=15.0, min_value=0.0, step=0.5, format="%.2f"
    )
    tempo_horas = st.number_input(
        "Tempo de fabricação (horas)", value=5.0, min_value=0.0, step=0.25, format="%.2f"
    )
    valor_hora = st.number_input(
        "Quanto vale sua hora? (R$)", value=15.0, min_value=0.0, step=1.0, format="%.2f"
    )
    margem_lucro = st.slider("Margem de Lucro (%)", 0, 200, 50)
    quantidade = st.number_input("Quantidade produzida por lote (peças)", value=1, min_value=1, step=1)
    incluir_overhead = st.checkbox("Incluir overhead (%)", value=False)
    overhead_pct = 0.0
    if incluir_overhead:
        overhead_pct = st.number_input("Overhead (% sobre custo total)", value=10.0, min_value=0.0, max_value=100.0, step=1.0)
    submitted = st.form_submit_button("Calcular")

if not submitted:
    st.info("Preencha os custos no menu lateral e clique em 'Calcular'.")
    st.stop()

# Validações básicas
if peso_material < 0 or custo_grama < 0 or custo_acessorios < 0 or tempo_horas < 0 or valor_hora < 0 or quantidade < 1:
    st.error("Valores inválidos detectados. Verifique os campos (devem ser não-negativos).")
    st.stop()

# Cálculos
custo_material = peso_material * custo_grama
custo_mao_de_obra = tempo_horas * valor_hora
custo_total = custo_material + custo_acessorios + custo_mao_de_obra

if overhead_pct:
    custo_total = custo_total * (1 + overhead_pct / 100)

custo_por_peca = custo_total / quantidade
preco_venda_por_peca = custo_por_peca * (1 + margem_lucro / 100)
lucro_por_peca = preco_venda_por_peca - custo_por_peca
margem_real_pct = (lucro_por_peca / preco_venda_por_peca) * 100 if preco_venda_por_peca else 0.0

# Exibição dos resultados
col1, col2, col3 = st.columns(3)
col1.metric("Preço Sugerido / peça", format_brl(preco_venda_por_peca))
col2.metric("Custo / peça", format_brl(custo_por_peca))
col3.metric("Lucro / peça", format_brl(lucro_por_peca))

st.write("---")
st.write("### Detalhamento do Custo (total e por peça)")
data = [
    ["Material (total)", format_brl(custo_material)],
    ["Acessórios (total)", format_brl(custo_acessorios)],
    ["Mão de Obra (total)", format_brl(custo_mao_de_obra)],
]
if overhead_pct:
    data.append([f"Overhead ({overhead_pct}%)", format_brl(custo_total - (custo_material + custo_acessorios + custo_mao_de_obra))])
data.append(["Custo Total (lote)", format_brl(custo_total)])
data.append(["Quantidade no lote", f"{int(quantidade)} peças"])
data.append(["Custo por peça", format_brl(custo_por_peca)])
data.append(["Preço sugerido por peça", format_brl(preco_venda_por_peca)])
data.append(["Lucro por peça", format_brl(lucro_por_peca)])
data.append(["Margem desejada (%)", f"{margem_lucro}%"])
data.append(["Margem real sobre venda (%)", f"{margem_real_pct:.2f}%"])

df = pd.DataFrame(data, columns=["Item", "Valor"])
st.table(df)

st.success(f"Com essa margem de {margem_lucro}%, você lucra {format_brl(lucro_por_peca)} por peça.")

# Preparar CSV para download
csv_buf = StringIO()
download_df = pd.DataFrame({
    "item": [r[0] for r in data],
    "valor": [r[1] for r in data],
})
download_df.to_csv(csv_buf, index=False, sep=";")
st.download_button("⤓ Baixar relatório (CSV)", csv_buf.getvalue(), file_name="precificacao_bolsas.csv", mime="text/csv")