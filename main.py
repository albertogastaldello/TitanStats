from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DateRangeSlider, Button
from bokeh.plotting import figure
from bokeh.layouts import column
import pandas as pd
from datetime import datetime

# Funzione per calcolare il saldo
def calculate_balance(start_date, end_date, risk_factor, rr_factor, partials_factor):
    statistiche = []
    formatori = ['NATE', 'REY', 'DAVID']
    
    # Carico i dati
    for k in range(len(formatori)):
        curr_stats = pd.read_excel('TitanPython.xlsx', sheet_name=f'{formatori[k]} XAUUSD' )
        curr_stats['FORMATORE'] = formatori[k]
        curr_stats['DATA_ORA'] = curr_stats.apply(lambda row: datetime.combine(row['GIORNO'].date(), row['ORA']), axis=1)
        statistiche.append(curr_stats)

    statistiche_unito = pd.concat([statistiche[j] for j in range(len(formatori))])
    statistiche_unito = statistiche_unito.sort_values(by='DATA_ORA')

    # Filtro per le date
    statistiche_filtered = statistiche_unito.copy()
    statistiche_filtered = statistiche_filtered[(statistiche_filtered['GIORNO'] >= start_date) & (statistiche_filtered['GIORNO'] <= end_date)]
    statistiche_filtered = statistiche_filtered.reset_index(drop=True)

    balance_array = []
    previous_balance = 10000  # Bilancio iniziale
    balance_array.append(previous_balance)

    # Simulazione della strategia
    for i in range(len(statistiche_filtered)):
        curr_date = statistiche_filtered['GIORNO'][i].date()
        curr_hour = statistiche_filtered['ORA'][i]
        curr_direction = statistiche_filtered['DIREZIONE'][i]
        curr_max_rr = statistiche_filtered['RR MAX'][i]
        curr_formatore = statistiche_filtered['FORMATORE'][i]
        risk = risk_factor[curr_formatore]
        rr_desired_list = rr_factor[curr_formatore]
        parziali = partials_factor[curr_formatore]

        curr_operation_pnl = 0
        percentage_open = 1

        for j in range(len(rr_desired_list)):
            curr_rr_desired = rr_desired_list[j]
            if curr_max_rr >= curr_rr_desired:
                percentage_open = percentage_open - parziali[j]
                curr_operation_pnl = curr_operation_pnl + (risk / 100) * curr_rr_desired * parziali[j] * previous_balance
            else:
                curr_operation_pnl = curr_operation_pnl - (risk / 100) * percentage_open * previous_balance
                break

        updated_balance = previous_balance + curr_operation_pnl
        previous_balance = updated_balance
        balance_array.append(updated_balance)

    return balance_array

# Funzione per aggiornare il grafico
def update_plot():
    # Prendo il range selezionato nel slider
    start_date = pd.to_datetime(start_date_slider.value[0])
    end_date = pd.to_datetime(start_date_slider.value[1])
    
    # Calcolo il bilancio per il range di date selezionato
    balance_data = calculate_balance(start_date, end_date, risk_factor, rr_factor, partials_factor)
    
    # Ora aggiorno i dati nel ColumnDataSource
    source.data = {
        'x': list(range(len(balance_data))),  # Lista con l'indice delle operazioni
        'y': balance_data  # Lista con i saldi aggiornati
    }

# Crea il range di date interattivo
start_date_slider = DateRangeSlider(
    title="Seleziona intervallo di date",
    start=pd.Timestamp('2025-01-01'),
    end=pd.Timestamp('2025-05-04'),
    value=(pd.Timestamp('2025-01-01'), pd.Timestamp('2025-05-04'))
)

# Crea il bottone per aggiornare il grafico
update_button = Button(label="Aggiorna Grafico", button_type="success")
update_button.on_click(update_plot)

# Crea il grafico
source = ColumnDataSource(data={'x': [], 'y': []})
p = figure(title="Andamento del bilancio", x_axis_label="Operazioni", y_axis_label="Saldo", width=800, height=400)
p.line(x='x', y='y', source=source, line_width=2)

# Layout
layout = column(start_date_slider, update_button, p)

# Aggiungi il layout alla pagina
curdoc().add_root(layout)

# Dati di esempio per il calcolo del saldo (fissi)
risk_factor = {'NATE': 1, 'REY': 1, 'DAVID': 1}
rr_factor = {'NATE': [1, 2], 'REY': [1, 2, 3], 'DAVID': [1]}
partials_factor = {'NATE': [0.5, 0.5], 'REY': [0.3, 0.3, 0.4], 'DAVID': [1]}

# Inizializzare il grafico con i dati predefiniti
initial_balance_data = calculate_balance(pd.Timestamp('2025-01-01'), pd.Timestamp('2025-05-04'), risk_factor, rr_factor, partials_factor)
source.data = {
    'x': list(range(len(initial_balance_data))),  # Convertiamo range in lista
    'y': initial_balance_data
}
