import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(layout="wide")
st.title("NOVA SGMTitanStats")

# Parametri iniziali
formatori = ['NATE', 'REY', 'DAVID']
formatore_risk = {'NATE': 1, 'REY': 1, 'DAVID': 1}
formatore_rr = {'NATE': [1, 2], 'REY': [1, 2, 3], 'DAVID': [1]}
formatore_parziali = {'NATE': [0.5, 0.5], 'REY': [0.3, 0.3, 0.4], 'DAVID': [1]}

# Caricamento dati
statistiche = []
for formatore in formatori:
    curr_stats = pd.read_excel('TitanPython.xlsx', sheet_name=f'{formatore} XAUUSD')
    curr_stats['FORMATORE'] = formatore
    curr_stats['DATA_ORA'] = curr_stats.apply(lambda row: datetime.combine(row['GIORNO'].date(), row['ORA']), axis=1)
    statistiche.append(curr_stats)

df = pd.concat(statistiche)
df = df.sort_values(by='DATA_ORA').reset_index(drop=True)

# Interfaccia Streamlit
st.sidebar.header("Filtri")
selected_formatori = st.sidebar.multiselect(
    "Seleziona i formatori",
    options=formatori,
    default=formatori  # Tutti selezionati di default
)

st.sidebar.markdown("### Rischio per formatore (%)")
user_risk={}
for formatore in selected_formatori:
    rischio = st.sidebar.number_input(
        f"Rischio per {formatore}",
        min_value = 0.0,
        max_value = 5.0,
        value = float(formatore_risk[formatore]),
        step=0.5,
        key=f"rischio_{formatore}"
    )
    user_risk[formatore]=rischio

st.sidebar.markdown("### RR e parziali per formatore")
user_rr={}
user_parziali={}

for formatore in selected_formatori:
    st.sidebar.markdown(f"**{formatore}**")

    rr_input=st.sidebar.text_input(
        f"RR per {formatore} (ad es. 1:1 e 1:2, scrivere 1,2)",
        value=",".join(map(str, formatore_rr[formatore])),
        key=f"rr_{formatore}"
    )
    parziali_input=st.sidebar.text_input(
        f"Parziali per {formatore} (es 0.3,0.3,0.4. La somma deve fare 1!)",
        value=",".join(map(str, formatore_parziali[formatore])),
        key=f"parziali_{formatore}"
    )

    try:
        rr_list = [float(x.strip()) for x in rr_input.split(",")]
        parziali_list = [float(x.strip()) for x in parziali_input.split(",")]

        if len(rr_list) != len(parziali_list):
            st.sidebar.warning(f"{formatore}: RR e Parziali devono avere la stessa lunghezza.")
        elif not abs(sum(parziali_list) - 1.0) < 0.01:
            st.sidebar.warning(f"{formatore}: La somma dei parziali deve essere 1.0.")
        else:
            user_rr[formatore] = rr_list
            user_parziali[formatore] = parziali_list
    except Exception:
        st.sidebar.warning(f"{formatore}: Formato non valido.")

start_date = st.date_input("Data Inizio", df["GIORNO"].min())
end_date = st.date_input("Data Fine", df["GIORNO"].max())

if not selected_formatori:
    st.warning("Seleziona almeno un formatore per visualizzare i dati.")
elif start_date > end_date:
    st.error("La data di inizio non può essere dopo quella di fine.")
else:
    # Filtro
    df_filtered = df[df["FORMATORE"].isin(selected_formatori)]
    mask = (df_filtered['GIORNO'] >= pd.to_datetime(start_date)) & (df_filtered['GIORNO'] <= pd.to_datetime(end_date))
    df_filtered = df_filtered.loc[mask].reset_index(drop=True)

    if df_filtered.empty:
        st.warning("Nessun dato disponibile per l'intervallo selezionato.")
    else:
        # Simulazione strategia
        balance_array = []
        balance = 10000
        balance_array.append(balance)

        for i in range(len(df_filtered)):
            curr = df_filtered.loc[i]
            curr_rr_max = curr['RR MAX']
            formatore = curr['FORMATORE']
            risk = user_risk[formatore]
            rr_list = user_rr.get(formatore, formatore_rr[formatore])
            parziali = user_parziali.get(formatore, formatore_parziali[formatore])

            pnl = 0
            open_percent = 1

            for j in range(len(rr_list)):
                rr = rr_list[j]
                if curr_rr_max >= rr:
                    pnl += (risk / 100) * rr * parziali[j] * balance
                    open_percent -= parziali[j]
                else:
                    pnl -= (risk / 100) * open_percent * balance
                    break

            balance += pnl
            balance_array.append(balance)

        # Grafico
        st.subheader("Andamento del Balance")
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(balance_array, linewidth=2, color='blue')
        ax.set_xlabel("Numero di Operazioni")
        ax.set_ylabel("Balance")
        ax.grid(True)
        st.pyplot(fig)

        # Statistiche finali generali
        max_balance = max(balance_array)
        min_balance = min(balance_array)
        final_balance = balance_array[-1]

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Balance Finale", f"{final_balance:,.2f}")
        col2.metric("📈 Balance Massimo", f"{max_balance:,.2f}")
        col3.metric("📉 Balance Minimo", f"{min_balance:,.2f}")


        st.subheader("📊 Riepilogo per Formatore")

        summary_data = []

        for formatore in selected_formatori:
            df_f = df_filtered[df_filtered["FORMATORE"] == formatore]
            num_operazioni = len(df_f)
            rischio = user_risk[formatore]
            rr = user_rr.get(formatore, formatore_rr[formatore])
            parz = user_parziali.get(formatore, formatore_parziali[formatore])

            summary_data.append({
                "Formatore": formatore,
                "Operazioni": num_operazioni,
                "Rischio (%)": rischio,
                "RR": ", ".join(map(str, rr)),
                "Parziali": ", ".join(map(str, parz))
            })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df)


        st.subheader("📉 Distribuzione RR MAX per Formatore")

        for formatore in selected_formatori:
            df_f = df_filtered[df_filtered["FORMATORE"] == formatore].copy()

            if df_f.empty or "RR MAX" not in df_f.columns:
                st.warning(f"Nessun dato per il formatore {formatore}.")
                continue

            # Assicuriamoci che i valori siano numerici e senza NaN
            df_f["RR MAX"] = pd.to_numeric(df_f["RR MAX"], errors="coerce")
            df_f = df_f.dropna(subset=["RR MAX"])

            # Ottieni la soglia di stop
            rr_configurati = user_rr.get(formatore, formatore_rr[formatore])
            if not rr_configurati:
                st.warning(f"Nessuna RR configurata per {formatore}.")
                continue

            soglia_stop = min(rr_configurati)
            df_f["RR_DISPLAY"] = df_f["RR MAX"].apply(lambda x: -1 if x < soglia_stop else x)

            if not df_f["RR_DISPLAY"].empty:
                fig = px.histogram(
                    df_f,
                    x="RR_DISPLAY",
                    nbins=20,
                    title=f"Distribuzione RR MAX - {formatore}",
                    labels={"RR_DISPLAY": "RR MAX (Stop = -1)", "count": "Frequenza"},
                    color_discrete_sequence=["orange"]
                )
                fig.update_layout(bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Nessun RR MAX valido per {formatore}.")




