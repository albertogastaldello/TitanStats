import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Andamento del Balance per Formatore")

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
start_date = st.date_input("Data Inizio", df["GIORNO"].min())
end_date = st.date_input("Data Fine", df["GIORNO"].max())

if start_date > end_date:
    st.error("La data di inizio non può essere dopo quella di fine.")
else:
    # Filtro
    mask = (df['GIORNO'] >= pd.to_datetime(start_date)) & (df['GIORNO'] <= pd.to_datetime(end_date))
    df_filtered = df.loc[mask].reset_index(drop=True)

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
            risk = formatore_risk[formatore]
            rr_list = formatore_rr[formatore]
            parziali = formatore_parziali[formatore]

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
