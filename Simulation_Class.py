# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 09:37:33 2023

@author: Francesco.Peria
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.stats import norm


#--------------------------------------------------------------------------

def write_results(path, text):
    with open(path, 'a') as file:
        file.write(text)

#--------------------------------------------------------------------------

class Product:
       
    
    """" This class represents a generic product whose inventory cycle is simulated.
    R is the replenishment interval, which refers to the average span of time between two
    consecutive productions of the same product.
    demand is the weekly series according to which the inventory is built. Thus it can be 
    a sales forecast, a sales order or simply a sale. 
    For simplicity I assumed that the demand which drives the inventory plan is equal to the actual sales
    and so everything is produced is also sold. 
    Of course this is a strong assumption that doesn't exist in the real world, since the inventory is
    usually based on a forecast, that lead to a forecast error and so to an efficiency in the planning process.
    Any inefficiency leads to an higher warehouse fill rate.
    But the aim of this model is just to link the replenishment frequency of many codes to the warehouse 
    fill rate day by day.
    The same class could be slightly modified to deal with other more realistic assumptions that of course
    create inefficiencies in the planning process (es. forecast error) and so increase the overall stock level.
    """
    
    def __init__(self, code, name, line, productivity, cases_PAL, stacking, demand, R, daily_sold):
        self.code = code # int
        self.name = name # string
        self.line = line # string
        self.productivity = productivity # int
        self.cases_PAL = cases_PAL # int
        self.stacking = stacking # int
        self.demand = demand # Pandas Series
        self.R = R # int, viene espresso in giorni
        self.daily_sold = daily_sold # Pandas Series
        
        
         
    def demand_mu(self, start, end, non_zero = True):
        
        # Se sto passando un intero, tratta il parametro "end" come se fosse uno step, sommandolo a "start"
        if type(end) == int:
            if non_zero:
                mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end)) & (self.demand != 0)
            else:
                mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end))
         
        # Se sto passando una datetime, allora "end" lo tratto da data di fine
        else:
            if non_zero:
                mask = (self.demand.index >= start) & (self.demand.index < end) & (self.demand != 0)
            else:
                mask = (self.demand.index >= start) & (self.demand.index < end)
                
        mu = self.demand[mask].mean(axis = 0)
            
        return mu
    
    
    #--------------------------------------------------------------------------
    
    def demand_sd(self, start, end, non_zero = True):
        
        # Se sto passando un intero, tratta il parametro "end" come se fosse uno step, sommandolo a "start"
        if type(end) == int:
            if non_zero:
                mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end)) & (self.demand != 0)
            else:
                mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end))
                
        # Se sto passando una datetime, allora "end" lo tratto da data di fine
        else:
            if non_zero:
                mask = (self.demand.index >= start) & (self.demand.index < end) & (self.demand != 0)
            else:
                mask = (self.demand.index >= start) & (self.demand.index < end)
        
        sd = self.demand[mask].std(axis = 0)
        
        return sd
    
    
    #--------------------------------------------------------------------------
    
    def demand_CV2(self, start, end, non_zero = True):
        
        CV = self.demand_sd(start, end, True) / self.demand_mu(start, end, True)
        
        return CV**2
    
    
    #--------------------------------------------------------------------------
    
    def demand_NZ_buckets(self, start, end):
        
        if type(end) == int:
            mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end)) & (self.demand != 0)
        else:
            mask = (self.demand.index >= start) & (self.demand.index < end) & (self.demand != 0)
        NZ_buckets = len(self.demand[mask])  # Numero di periodi totali Non Zero
        
        return NZ_buckets
    
    
    #--------------------------------------------------------------------------
    
    def demand_ADI(self, start, end):
        
        # Se sto passando un intero, tratta il parametro "end" come se fosse uno step, sommandolo a "start"
        if type(end) == int:
            mask = (self.demand.index >= start) & (self.demand.index < start + timedelta(days = end))
                
        # Se sto passando una datetime, allora "end" lo tratto da data di fine
        else:
            mask = (self.demand.index >= start) & (self.demand.index < end)
            
        Horizon = len(self.demand[mask]) # Numero di periodi totali nell'orizzonte
        NZ_buckets = self.demand_NZ_buckets(start, end) # Richiamo la funzione qui sopra per determinare il numero di periodi totali Non Zero
        
        try: # serve per ritornare nan nel caso in cui ci sia una divisione per 0
            ADI = Horizon / NZ_buckets
        except:
            ADI = np.nan
 
        return ADI
    
    
    #--------------------------------------------------------------------------
    
    def demand_segment(self, start, end, non_zero = True):
        
        ADI = self.demand_ADI(start, end)
        CV2 = self.demand_CV2(start, end, True)
        NZ_buckets = self.demand_NZ_buckets(start, end)
        
        segment = np.nan
        
        # Slow perché hanno meno di 5 osservazioni nel periodo scelto
        if NZ_buckets < 5:
            segment = 'SLOW'
        
        elif CV2 > 9:
            segment = 'XVARIABLE'
            
        # Classica categorizzazione su ADI e CV
        elif (CV2 <= 0.49) and (ADI <= 1.32):
            segment = 'SMOOTH'
        elif (CV2 <= 0.49) and (ADI > 1.32):
            segment = 'INTERMITTENT'
        elif (CV2 > 0.49) and (ADI <= 1.32):
            segment = 'ERRATIC'
        else:
            segment = 'LUMPY'
        
        return segment
    

    #--------------------------------------------------------------------------
    
    
    def daily_sold_tot(self, start, end, non_zero = True):
        
        # Se sto passando un intero, tratta il parametro "end" come se fosse uno step, sommandolo a "start"
        if type(end) == int:
            if non_zero:
                mask = (self.daily_sold.index >= start) & (self.daily_sold.index < start + timedelta(days = end)) & (self.daily_sold != 0)
            else:
                mask = (self.daily_sold.index >= start) & (self.daily_sold.index < start + timedelta(days = end))
         
        # Se sto passando una datetime, allora "end" lo tratto da data di fine
        else:
            if non_zero:
                mask = (self.daily_sold.index >= start) & (self.daily_sold.index < end) & (self.daily_sold != 0)
            else:
                mask = (self.daily_sold.index >= start) & (self.daily_sold.index < end)
        
        tot = self.daily_sold[mask].sum(axis = 0)
        return tot
  
    
    
    #--------------------------------------------------------------------------
    
    # Questo modello serve per settare i parametri del modello in maniera ACTUAL_SALES driven.
    # In pratica faccio l'assunzione di conoscere gli ordini futuri e quindi di programmare sempre la quantità ottimale
    # dato un periodo di replenishment self.R. Con questo approccio non serve la Ss
    def calc_simulation_params_on_daily_sold(self, start, Lro_days = 0):
        
        
        ###### CALCOLO Target_Stock ######
        # In questo approccio non serve la scorta di sicurezza perché
        # se uso i dati di sold per settare i parametri, è come se quando produco
        # conosco esattamente quello che venderò
        Target_Stock =  self.daily_sold_tot(start, self.R, non_zero = False)
        
        ###### CALCOLO Lro #######
        Lro = self.daily_sold_tot(start + timedelta(days = self.R - Lro_days), Lro_days, non_zero = False)
        
            
        return Lro, Target_Stock

    
    
    #--------------------------------------------------------------------------

    # simulate richiama il metodo soprastante ovvero calc_simulation_params_on_daily_sold
    def simulate(self, start, duration, verbose = True, Lro_days = 0, shift_week = 14,
                 work_days_week = 5, unit = 'NR', path_txt = ''):
        
        
        # ****************************************************************************
        # ******************** CREAZIONE VARIABILI DI SIMULAZIONE ********************
        # ****************************************************************************
        
        series_Sim_Days = pd.Series([start + timedelta(days = j) for j in range(duration)], name = 'Sim_Days')
        
        # Dice quanto stock ho in mano giorno dopo giorno
        series_On_Hand = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'On_Hand')

        # Contiene il quantitativo totale da produrre per raggingere la scorta target
        series_To_Prod = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'To_Prod')

        # Contiene il quantitativo che è stato possibile produrre in un giorno considerando la produttività
        series_Realized = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'Realized')
        
        # Contiene il livello di scorta a cui io devo innescare il prossimo riordino
        series_Lro = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'Lro')
        
        # Contiene il target di scorta che devo raggiongere nel successivo riordino
        series_Target_Stock = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'Target_Stock')
        
        # Contiene il valore dell'intervallo di replenishment giorno dopo giorno
        series_IR = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'Replenish_Int')
        
        # Contiene il conteggio dei giorni man mano che la simulazione prosegue
        series_Count_Days = pd.Series(np.full(duration, 0), index = series_Sim_Days.values, name = 'Count_Days')
        
        # Serie di valori tutti uguali pari alla produttività del singolo codice
        series_Productivity = pd.Series(np.full(duration, self.productivity), index = series_Sim_Days.values, name = 'Productivity')
        

        # Serie che contiene la variabile proxy scelta per far decrescere il dente di sega durante la simulazione, ovvero
        # l'attributo daily_sales di ogni oggetto Product
        series_daily_sold = pd.Series(index = [start + timedelta(days = j) for j in range(duration)], name = 'temp', dtype = np.float64)
        series_daily_sold = pd.merge(series_daily_sold.to_frame(), 
                                     self.daily_sold.to_frame(),
                                     how = 'left',
                                     left_index = True,
                                     right_index = True).drop(columns = ['temp']).fillna(0).squeeze()
        series_daily_sold.name = 'Daily_Sold'
        
        
        # Serie che contiene i valori di Demand settimanali riempita con l'attributo FCST di ogni oggetto Product
        series_d = pd.Series(index = [start + timedelta(days = j) for j in range(duration)], name = 'temp', dtype = np.float64)
        series_d = pd.merge(series_d.to_frame(),
                            self.demand.to_frame(),
                            how = 'left', 
                            left_index = True,
                            right_index = True).drop(columns = ['temp']).fillna(method = 'ffill').fillna(method = 'bfill').squeeze()
        series_d.name = 'Demand'
        
        # ****************************************************************************
        # **************** INIZIALIZZAZIONE VARIABILI DI SIMULAZIONE *****************
        # ****************************************************************************
       
        
        # Richiamo il metodo d'istanza "calc_simulation_params_on_daily_sold" che deve accettare come parametri i parametri forniti nell'argomento 
        # di questo metodo "simulate" e mi calcola Lro e Target_Stock
        (Lro, Target) = self.calc_simulation_params_on_daily_sold(start = start, Lro_days = Lro_days)
        
        # Definisco l'intervallo di replenishment IR, che è pari al review period self.R
        IR = self.R
                                                    
        # Assegno la produttività, che è un attributo della classe Product
        r = self.productivity
        
        # Faccio l'approssimazione che le linee lavorino work_days_week giorni alla settimana
        shift_day = shift_week / work_days_week
        
        # Inizializzo i parametri di simulazione da aggiornare iterativamente:
        # Ho in mano esattamente il massimo livello di scorta Target, a cui si sottrae la domanda che si è verificata
        series_On_Hand[0] = Target - series_daily_sold[0]
        series_Count_Days[0] = 0
        series_Lro[0] = Lro
        series_Target_Stock[0] = Target
        series_IR[0] = IR
        
        # *****************************************************************************
        # ** FACCIO GIRARE "calc_simulation_params_on_daily_sold" ad ogni iterazione **
        # *****************************************************************************
        
        idx_replenishment = 0
        
        # Qui dentro al for loop in cui si riempiono le serie che rappresentano le variabili di simulazione
        # e si lancia iterativamente iL metodi d'istanza "calc_simulation_params_on_daily_sold" che deve accettare come input i 
        # parametri forniti nell'argomento di questo metodo "simulate" e mi calcola i parametri di stock
        
        # parti dal giorno 1 e non dal giorno 0 sennò con (idx-1) succede casino
        for idx in range(1, duration): 
            
            series_To_Prod[idx] = max(series_To_Prod[idx-1] - series_Realized[idx-1], 0)

            if series_On_Hand[idx-1] <= series_Lro[idx-1]:
                
                # Richiamo il metodo d'istanza "calc_simulation_params_on_daily_sold" che deve accettare come parametri i parametri forniti nell'argomento 
                # di questo metodo "simulate" e mi calcola i parametri di stock
                (Lro, Target) = self.calc_simulation_params_on_daily_sold(start = series_Sim_Days[idx], Lro_days = Lro_days)
                series_To_Prod[idx] = Target - series_On_Hand[idx-1] # Delta da produrre per arrivare a Target quando series_On_Hand[idx-1] scende sotto Lro
                
                # Se ho effettivamente un replenishment e non è solo che la scorta è a 0 perché semplicemente
                # non ci sono valori daily_sold > 0 da sommare
                if Target > 0:
                    
                    idx_replenishment += 1
                    
                    to_print1 = '\n' + 20*'*' + ' ' + series_Sim_Days[idx].strftime('%Y-%m-%d') + ' '  + ' <---> ' + f' Code {self.code} <---> REPLENISHMEN N° {idx_replenishment} ' + 20*'*' + '\n'
                    write_results(path_txt, to_print1)
                    print(to_print1) if verbose else None
                    to_print1 = '\n' + 18*'_' + ' METODO: calc_simulation_params_on_daily_sold ' + 17*'_' +'\n' 
                     
                    to_print2 = '\n' + str(self.code) + ' - ' + str(self.name) + f'\nLro: {Lro:.2f}  |  \nTarget_Stock: {Target:.2f}' + '\n'
                    write_results(path_txt, to_print1)
                    write_results(path_txt, to_print2)
                    
                    if verbose:
                        print(to_print1)
                        print(to_print2)
                
                
                
                
        ####################
        
            # Se la quantità di produzione supera un'intera giornata di produzione (e quindi automaticamente anche il lotto minimo)    
            if (series_To_Prod[idx] >= shift_day * r): 
                series_Realized[idx] = shift_day * r
                # La scorta cresce della produttività r e decresce della domanda d[j]  
                series_On_Hand[idx] = series_On_Hand[idx-1] + series_Realized[idx] - series_daily_sold[idx] 
                # series_On_Hand[idx] = max(0, series_On_Hand[idx]) togli dal commento se al posto dei back-order si vuole considerare i lost-sales
                
            # Se devo produrre qualcosa che non supera la giornata di produzione 
            elif (series_To_Prod[idx] > 0):
                series_Realized[idx] = series_To_Prod[idx]
                series_On_Hand[idx] = series_On_Hand[idx-1] + series_Realized[idx] - series_daily_sold[idx]
                # series_On_Hand[idx] = max(0, series_On_Hand[idx]) togli dal commento se al posto dei back-order si vuole considerare i lost-sales
                    
            else: # Se non devo produrre nulla
                series_On_Hand[idx] = series_On_Hand[idx-1] - series_daily_sold[idx]
                # series_On_Hand[idx] = max(0, series_On_Hand[idx]) togli dal commento se al posto dei back-order si vuole considerare i lost-sales
                   
            series_Count_Days[idx] = idx
            series_Lro[idx] = Lro
            series_Target_Stock[idx] = Target
            series_IR[idx] = IR
            
        # ****************************************************************************
        # ************************ CREO df_simulation finale *************************
        # ****************************************************************************
        
        list_series_simulation = [series_Count_Days, series_Productivity, series_daily_sold, series_On_Hand, series_d,
                                  series_To_Prod, series_Realized, series_Lro, series_Target_Stock, series_IR]
        
        df_simulation = pd.DataFrame({s.name: s for s in list_series_simulation})
        
        # Rendo lo stock non negativo in caso serva
        #df_simulation['On_Hand'] = df_simulation['On_Hand'].apply(lambda x: 0 if x < 0 else x)
        
        # Restituisco i risultati nell'unità di misura desiderata
        dict_unit = {'NR': 1, 'PAL' : 1/self.cases_PAL, 'PP' : 1/(self.cases_PAL*self.stacking)}
        
        df_simulation[['Daily_Sold', 'On_Hand', 'Demand', 'To_Prod', 
                       'Realized', 'Lro', 'Target_Stock', 'Productivity']] = df_simulation[['Daily_Sold', 'On_Hand', 'Demand', 'To_Prod', 
                                                                                            'Realized', 'Lro', 'Target_Stock', 'Productivity']] * dict_unit[unit]
       
        return(df_simulation)
        
        
    
        
        
        
        
        
        




























    

     
     
     
     
     
     
     
     
     
     
        
    