# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 23:37:10 2023

@author: peria
"""

#%% # IMPORTAZIONE LIBRERIE GENERALI


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
#sns.set_style('darkgrid', {'axes.facecolor': '0.9'})
sns.set_style('whitegrid')
from scipy.stats import norm
from datetime import timedelta
#from Simulation_Class import Product
import random

from Simulation_Class import Product

#%%


def create_df(n_prod):
    
    prod = ['prod_' + str(n) for n in range(n_prod)]
    
    # Distribuisco i prodotti su 3 linee produttive con produttività diverse per ogni linea

    
    n_prod_1 = int(0.5*n_prod)
    n_prod_2 = int(0.3*n_prod)
    n_prod_3 = n_prod - n_prod_1 - n_prod_2

    productivity = []
    machine = []
    for j in range(1, n_prod+1):
        
        if j <= n_prod_1:
            machine.append('L1')
            productivity.append(np.random.normal(300, 30))
            
        elif j <= n_prod_1 + n_prod_2:
            machine.append('L2')
            productivity.append(np.random.normal(200, 25))
            
        else:
            machine.append('L3')
            productivity.append(np.random.normal(100, 15))
     
    
    # Battezzo il fattore di replenishment considerando che il 10% dei prodotti sono high runners
    n_prod_high = int(0.1*n_prod)
    n_prod_upper_mediumn = int(0.2*n_prod)
    n_prod_lower_mediumn = int(0.3*n_prod)
    n_prod_low = n_prod - n_prod_high - n_prod_upper_mediumn - n_prod_lower_mediumn
    
    
    R = list(np.concatenate([np.random.normal(15, 3, n_prod_high), np.random.normal(20, 4, n_prod_upper_mediumn),
                             np.random.normal(30, 10, n_prod_lower_mediumn), np.random.normal(40, 25, n_prod_low)]))
    
    R = [abs(x) for x in R] # Faccio in modo che nessun periodo di replenishment sia negativo
    
    A = pd.DataFrame({'Code': prod,
                      'Machine': machine,
                      'Productivity': productivity,
                      'R': R})
    A['R'] = A['R'].apply(lambda x: int(x))
    
    A.set_index('Code', inplace = True)
    
    return(A)

    
numero_prodotti = 20
df = create_df(numero_prodotti)

#%% CREAZIONE DATAFRAME CON DAILY SOLD


def create_daily_sales(n_prod, n_days, start, df):
    
    prod = list(df.index)
    days = [start + timedelta(days = j) for j in range(n_days)]
    
    q1 = df['R'].quantile(0.2)
    q2 = df['R'].quantile(0.4)
    q3 = df['R'].quantile(0.6) 
    q4 = df['R'].quantile(0.8) 
    
    list_daily_sales_series = []
    for j in prod:
        
        if df.loc[j, 'R'] < q1:
            mu = random.randint(100, 120) # generate random number 0-100
            sd = random.randint(5, 10) # generate random number 0-40
            
        elif df.loc[j, 'R'] < q2:
            mu = random.randint(50, 80) # generate random number 0-100
            sd = random.randint(5, 10) # generate random number 0-40
            
        elif df.loc[j, 'R'] < q2:
            mu = random.randint(20, 40) # generate random number 0-100
            sd = random.randint(5, 10) # generate random number 0-40
            
        else:
            mu = random.randint(0, 20) # generate random number 0-100
            sd = random.randint(5, 10) # generate random number 0-40
    
        values = pd.Series(np.random.normal(mu, sd, n_days), index = days, name = j) # avoid negative daily sales
        values = values.apply(lambda x: 0 if x < 0 else x)
        list_daily_sales_series.append(values)
    
    A = list_daily_sales_series[0]
    for values in list_daily_sales_series[1:]:
        A = pd.concat([A, values], axis = 1)
        
    A = A.astype(int)
    
    return(A)
    

df_daily_sold = create_daily_sales(numero_prodotti, 800, pd.to_datetime('2022.01.01'), df)



#%% CREAZIONE DATAFRAME CON WEEKLY SOLD

# Aggiungo il giorno della settimana a cui associare la settimana, sulla base del dict_giorno_scelto
dict_giorno_scelto = {'lun': '1',
                      'mar': '2',
                      'mer': '3', 
                      'gio': '4',
                      'ven': '5',
                      'sab': '6',
                      'dom': '0'}


df_weekly_sold = df_daily_sold.copy(deep = True)


# Queste righe servono a creare una colonna che per ogni giorno del dataframe data mi dica il lunedì (o comunque il 
# giorno scelto in esame) che fa capo alla relativa settimana
df_weekly_sold['Week'] = df_weekly_sold.index.isocalendar().week.astype(str) + '.' + df_weekly_sold.index.isocalendar().year.astype(str)
df_weekly_sold['Week'] = df_weekly_sold['Week'].apply(lambda x: ('0' + str(x)).replace('.' , '') if len(str(x)) == 6 else str(x).replace('.' , ''))
giorno_scelto = 'lun'
df_weekly_sold['Week'] = dict_giorno_scelto[giorno_scelto] + df_weekly_sold['Week']
df_weekly_sold['Week'] = pd.to_datetime(df_weekly_sold['Week'], format = '%w%W%Y')


# Creo il dataframe con i SALES ORDERS week-by-week
df_weekly_sold = df_weekly_sold.groupby(by = 'Week').sum()

print('\n\nWeekly Sales --> df_weekly_sold creato:\n', df_weekly_sold)



#%% CALCOLO STATS SU SOLD PER TUTTI I CODICI

# Sulla base delle stats sui Sales Orders poi creo la segmentazione
# Uso la classe Product creata appositamente

start = pd.to_datetime('2022-05-01')
end = pd.to_datetime('2023-04-30')


for j in df.index: 
    # Estraggo dai dataframe di input gli attributi che ad ogni iterazione mi servono per creare un oggetto della classe Product
    code_name = None
    line = df.loc[j, 'Machine']
    p = df.loc[j, 'Productivity']
    cases_PAL = None
    stacking = None
    series_d = df_weekly_sold[j] # series_d corrisponde alla proxy della domanda che si vuole usare
    R = df.loc[j, 'R'] # I metodi di istanza della classe Product necessitano che R sia int e in giorni
    series_daily_sold = df_daily_sold[j]
    
    # Ad ogni iterazione del ciclo istanzio un oggetto della classe Product
    P = Product(j, code_name, line, p, cases_PAL, stacking, series_d, R, series_daily_sold)
    
    # Uso i metodi della classe Product per inserire in df le colonne sulle statistiche calcolare sui SO
    df.loc[j, 'demand_mu'] = P.demand_mu(start, end, non_zero = True)
    df.loc[j, 'demand_sd'] = P.demand_sd(start, end, non_zero = True)
    df.loc[j, 'demand_NZ_buckets'] = P.demand_NZ_buckets(start, end)
    df.loc[j, 'demand_ADI'] = P.demand_ADI(start, end)
    df.loc[j, 'demand_CV2'] = P.demand_CV2(start, end, non_zero = True)
    df.loc[j, 'demand_segment'] = P.demand_segment(start, end, non_zero = True)

    

#%% PLOT PRODUCT SEGMENTATION


dict_color = {'SMOOTH': 'steelblue',
              'ERRATIC': 'darkorange',
              'INTERMITTENT': 'crimson',
              'LUMPY': 'green',
              'XVARIABLE': 'cyan',
              'SLOW': 'purple'}

fig, ax = plt.subplots(1,2, figsize = (16,6))

sns.countplot(x = df['demand_segment'], ax = ax[0], palette = dict_color)
ax[0].set_title('Countplot of Segments', fontsize = 15)

sns.scatterplot(x = df['demand_ADI'], y = df['demand_CV2'], hue = df['demand_segment'], palette = dict_color, ax = ax[1])


ax[1].legend(facecolor = 'white', loc= 'upper right', fontsize = 13)
ax[1].set_title('Plot demand_ADI e demand_CV2', fontsize = 15)

ax[0].set_xlabel('demand_segment', fontsize = 15)
ax[0].set_ylabel('Count', fontsize = 15)
ax[1].set_xlabel('demand_ADI', fontsize = 15)
ax[1].set_ylabel('demand_CV2', fontsize = 15)
  
plt.show()


print('\n', 80*'~', '\n\n')


#%% TEST METODO "calc_simulation_params" DELLA CLASSE Product

print('\n\nEsempio di output di calc_simulation_params:\n')


code = 'prod_1'
code_name = None
line = df.loc[code, 'Machine']
p = df.loc[code, 'Productivity']
cases_PAL = 1
stacking = 1
series_d = df_weekly_sold[code]
R = int(df.loc[code, 'R']) # I metodi di istanza della classe Product necessitano che R sia int e in giorni
series_daily_sold = df_daily_sold[code]

# Istanzio prodotto della classe Product
P = Product(code, code_name, line, p, cases_PAL, stacking, series_d, R, series_daily_sold)

print(P.calc_simulation_params_on_daily_sold(start = pd.to_datetime('2023-01-10'), Lro_days = 4))


print('\n', 80*'~', '\n\n')


#%% TEST METODO "simulate" DELLA CLASSE Product

path_txt = r'C:\Users\peria\Desktop\GitHub\Warehouse_Simulation\Results.txt'

with open(path_txt, 'w') as file: # Pulisco il file
        pass


# dict_simulation è il dizionario che ha come chiavi i codici e che contiene per ogni codice 
# il dataframe del relativo profilo di scorta simulato una volta a partire da START_simulation
dict_simulation = {}

for code in df.index:

    code_name = None
    line = df.loc[code, 'Machine']
    p = df.loc[code, 'Productivity']
    cases_PAL = 1           
    stacking = 1
    series_d = df_weekly_sold[code]
    R = int(df.loc[code, 'R']) # I metodi di istanza della classe Product necessitano che R sia int e in giorni
    series_daily_sold = df_daily_sold[code]
    
    # Istanzio prodotto della classe Product
    P = Product(code, code_name, line, p, cases_PAL, stacking, series_d, R, series_daily_sold)

    dict_simulation[code] = P.simulate(start = pd.to_datetime('2023-01-01'), 
                                       duration = 100, 
                                       verbose = True,
                                       Lro_days = 4,
                                       shift_week = 14,
                                       work_days_week = 5, 
                                       unit = 'NR',
                                       path_txt = path_txt)



#%% PLOT SIMULATION ONE SHOT

# Estraendo i df_simulation in corrispondenza della relativa chiave "code" dal dizionario dict_simulation
# plotto le variabili della smulazione contenute per ogni codice. Come detto in precedenza, tutti i profili
# di scorta di ogni codice inizieranno nella stessa data START_simulation

for code in dict_simulation.keys():
    fig, ax = plt.subplots(1, figsize = (15,7))
    # Profilo di scorta
    ax.fill_between( dict_simulation[code].index, dict_simulation[code]['On_Hand'], label = 'OH Inventory', color = 'navy')
    # Quantità realizzata in un determinato giorno
    ax.fill_between( dict_simulation[code].index, dict_simulation[code]['Realized'], color = 'darkorange', label = 'Prod Realized')
    #Livello di ricostituzione
    ax.plot(dict_simulation[code].index, dict_simulation[code]['Target_Stock'], color = 'dodgerblue', label = 'Replenishment Level', lw = 3)
    #Livello di Riordino
    ax.plot(dict_simulation[code].index, dict_simulation[code]['Lro'], color = 'red', label = 'Lro', linestyle = '--')
    # Forecast del mese in cui quel determinato giorno è contenuto
    ax.plot( dict_simulation[code].index, dict_simulation[code]['Productivity'], color = 'darkgrey', label = 'Productivity')
    # Domanda settimanale
    ax.plot(dict_simulation[code].index, dict_simulation[code]['Demand'], color = 'green', label = 'Weekly Demand')
    # Forecast del mese in cui quel determinato giorno è contenuto
    ax.plot( dict_simulation[code].index, dict_simulation[code]['Daily_Sold'], color = 'limegreen', label = 'Daily Sold')
    # Params
    plt.xlabel('Days', fontsize = 15)
    plt.xticks(fontsize = 12)
    plt.ylabel('Cases [NR]', fontsize = 15)
    plt.yticks(fontsize = 12)
    ax.legend(fontsize = 11, loc = 'best')
    plt.title(f'Simulation {code}', fontsize = 15)
    
    plt.savefig(rf'C:\Users\peria\Desktop\GitHub\Warehouse_Simulation\Plots\{code}.png')

    plt.show()
    
    
    
#%%

n_exp = 15

dict_experiment = {}
dict_simulation = {}

for n in range(n_exp):
    
    with open(path_txt, 'a') as file: 
            file.write('\n\n' + 95*'#' + '\n' + 45*' ' + f'Experiment_{n}' + '\n' + 95*'#' +  '\n\n')
    
    dict_on_hand = {}
    #df[df.index.isin([420572])].index:
    for code in df.index:
        random = np.random.randint(0, 20)
        
        code_name = None
        line = df.loc[code, 'Machine']
        p = df.loc[code, 'Productivity']
        cases_PAL = 1
        stacking = 1
        series_d = df_weekly_sold[code]
        R = int(df.loc[code, 'R']) # I metodi di istanza della classe Product necessitano che R sia int e in giorni
        series_daily_sold = df_daily_sold[code]
        
        # Istanzio prodotto della classe Product
        P = Product(code, code_name, line, p, cases_PAL, stacking, series_d, R, series_daily_sold)


        dict_simulation[str(code)+'_exp'+str(n)] = P.simulate(start = pd.to_datetime('2023-01-01') + timedelta(days = random), 
                                                              duration = 100,
                                                              verbose = True,
                                                              Lro_days = 4,
                                                              shift_week = 14,
                                                              work_days_week = 5, 
                                                              unit = 'PAL',
                                                              path_txt = path_txt)
        
        dict_on_hand[str(code)+'_exp'+str(n)] = dict_simulation[str(code)+'_exp'+str(n)]['On_Hand']
    
    dict_experiment['Experiment_'+str(n)] = pd.DataFrame(dict_on_hand).sum(axis = 1)


#%%

df_experiment = pd.DataFrame(dict_experiment)
df_experiment['Mean_Exp'] = df_experiment.mean(axis = 1)


#%%

fig, ax = plt.subplots(figsize =(15, 6))

df_experiment.plot(ax = ax, legend = False, ylim =[0, 1.15*max(df_experiment.max())])
df_experiment['Mean_Exp'].plot(ax = ax, legend = False, lw = 4, c = 'black', ylim =[0, 1.15*max(df_experiment.max())])
ax.set_title('Monte Carlo Simulation - Warehouse Occupation', fontsize=20)

plt.show()













