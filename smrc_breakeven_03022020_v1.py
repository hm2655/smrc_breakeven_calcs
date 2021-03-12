# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 09:07:30 2020

@author: harshit.mahajan
"""

import pandas as pd
import numpy as np 
from datetime import datetime, date, timedelta 
import time 
import xlrd
import matplotlib.pyplot as plt


#Start the timer
start = time.time()

today = date.today()

#File Path
filePath = 'XXXX'
fileName = 'XXXX'
fileRoute = filePath + fileName 

# Reading the excel file 
excelFile = pd.ExcelFile(fileRoute)
sheetList = excelFile.sheet_names

#Prices
actualPrices = excelFile.parse('bbg_qry', header = None).iloc[3:,].reset_index(drop=True)
actualPrices=actualPrices.iloc[:, [1,3,5,7,9,11,13]]
actualPrices.columns=['date_id','waha','ethane','propane','nbutane','ibutane','pentanes']
actualPrices['date_id'] = pd.to_datetime(actualPrices['date_id'])
actualPrices['butane'] = (actualPrices['nbutane']+ actualPrices['ibutane'])/2
start_date = '2020-02-01'

#Well Unshrunk Gas Prod
production = excelFile.parse('wellProd',header=0).iloc[:,0:22].dropna().reset_index(drop=True)
wellProd = pd.melt(production, id_vars = ['Bucket','Asset','Type Curve','stream','ethane','propane','butane','pentane','shrinkage', 'type'], var_name=['date_id'], value_name='unshrunkgas')
#wellProd = wellProd[wellProd['date_id'] > start_date]
wellProd = wellProd[wellProd['date_id'] == '2020-03-01']
#wellProd = wellProd[wellProd['shrinkage'] > 0.12].reset_index(drop=True)
wellProd = wellProd[wellProd['unshrunkgas'] > 0].reset_index(drop=True)

#Lean Gas 
ep_lean_gas_cost = 0.523 
midstream_lean_gas_fee = 0.424

lean_wells = wellProd[wellProd['type']=='Lean']
well_lean_list = lean_wells.Asset.unique()

all_lean_wells = pd.DataFrame()

price_list  = np.linspace(-1,1,41)
for i in well_lean_list:
    for waha_prices in price_list:
        tempDf = lean_wells[lean_wells['Asset'] == i] 
        tempDf  = pd.merge(tempDf, actualPrices[['date_id','waha','ethane','propane','butane','pentanes']], how='left',left_on='date_id', right_on='date_id').reset_index(drop=True)
        tempDf['days'] = tempDf['date_id'].dt.daysinmonth
        tempDf['leanGas'] = tempDf['unshrunkgas'] * (1-tempDf['shrinkage'])
        tempDf['ethane_yield'] = tempDf['unshrunkgas'] * tempDf['ethane_x']
        tempDf['propane_yield'] = tempDf['unshrunkgas'] * tempDf['propane_x']
        tempDf['butane_yield'] = tempDf['unshrunkgas'] * tempDf['butane_x']
        tempDf['pentane_yield'] = tempDf['unshrunkgas'] * tempDf['pentane']
        tempDf['ngl_yield'] = tempDf['ethane_yield'] + tempDf['propane_yield'] + tempDf['butane_yield'] + tempDf['pentane_yield']
        
        ## EP Total Cost
        tempDf['total_cost'] = (tempDf['unshrunkgas']* apa_lean_gas_cost)*tempDf['days']/1000000
        
        ## Midstream Rev
        tempDf['total_altm_rev'] = (tempDf['unshrunkgas'] * altm_lean_gas_fee)*tempDf['days']/1000000
                
        ## Total Sales Rev
        tempDf['total_sales_rev'] = (tempDf['leanGas'] * waha_prices)*tempDf['days']/1000000
                      
        tempDf['gas_net'] = np.where(waha_prices<0, tempDf['leanGas'] * waha_prices * tempDf['days']/1000000, (tempDf['leanGas'] * waha_prices * tempDf['days']/1000000 * 0.75))
                      
        tempDf['ngl_net'] = 0
                            
        tempDf['net_sales'] = tempDf['gas_net'] + tempDf['ngl_net']
                            
        tempDf['apa_net_income'] = - tempDf['total_cost'] + tempDf['total_altm_rev'] *0.79 + tempDf['net_sales']
                            
        tempDf['price_type'] = waha_prices
        
        all_lean_wells = all_lean_wells.append(tempDf)
                           
        print(waha_prices)

    print(i)


#Rich Gas 
##ep_gas_cost = 0.956
##midstream_gas_fee = 0.816
##ep_ngl_cost = 4.207
##midstream_ngl_fee = 0.196

rich_wells = wellProd[wellProd['type']=='Rich']
well_rich_list = rich_wells.Asset.unique()

all_rich_wells = pd.DataFrame()

price_list  = np.linspace(-2,1,61)
for i in well_rich_list:
    for waha_prices in price_list:
        tempDf = rich_wells[rich_wells['Asset'] == i] 
        tempDf  = pd.merge(tempDf, actualPrices[['date_id','waha','ethane','propane','butane','pentanes']], how='left',left_on='date_id', right_on='date_id').reset_index(drop=True)
        tempDf['days'] = tempDf['date_id'].dt.daysinmonth
        tempDf['leanGas'] = tempDf['unshrunkgas'] * (1-tempDf['shrinkage'])
        tempDf['ethane_yield'] = tempDf['unshrunkgas'] * tempDf['ethane_x']
        tempDf['propane_yield'] = tempDf['unshrunkgas'] * tempDf['propane_x']
        tempDf['butane_yield'] = tempDf['unshrunkgas'] * tempDf['butane_x']
        tempDf['pentane_yield'] = tempDf['unshrunkgas'] * tempDf['pentane']
        tempDf['ngl_yield'] = tempDf['ethane_yield'] + tempDf['propane_yield'] + tempDf['butane_yield'] + tempDf['pentane_yield']
        
        ## APA Total Cost
        tempDf['total_cost'] = (tempDf['unshrunkgas']* apa_gas_cost + tempDf['ngl_yield']*apa_ngl_cost)*tempDf['days']/1000000
        
        ## ALTM Rev
        tempDf['total_altm_rev'] = (tempDf['unshrunkgas'] * altm_gas_fee + tempDf['ngl_yield']*altm_ngl_fee)*tempDf['days']/1000000
                
        ## Total Sales Rev
        tempDf['total_sales_rev'] = (tempDf['leanGas'] * waha_prices +
                                      tempDf['ethane_yield']* tempDf['ethane_y']*42 + 
                                      tempDf['propane_yield'] * tempDf['propane_y']*42 + 
                                      tempDf['butane_yield']*tempDf['butane_y']*42 + 
                                      tempDf['pentane_yield']*tempDf['pentanes']*42)*tempDf['days']/1000000
                      
        tempDf['gas_net'] = np.where(waha_prices<0, tempDf['leanGas'] * waha_prices * tempDf['days']/1000000, (tempDf['leanGas'] * waha_prices * tempDf['days']/1000000 * 0.75))
                      
        tempDf['ngl_net'] = (tempDf['ethane_yield']* tempDf['ethane_y']*42 + 
                                      tempDf['propane_yield'] * tempDf['propane_y']*42 + 
                                      tempDf['butane_yield']*tempDf['butane_y']*42 + 
                                      tempDf['pentane_yield']*tempDf['pentanes']*42)*0.75*tempDf['days']/1000000
                            
        tempDf['net_sales'] = tempDf['gas_net'] + tempDf['ngl_net']
                            
        tempDf['apa_net_income'] = - tempDf['total_cost'] + tempDf['total_altm_rev'] *0.79 + tempDf['net_sales']
                            
        tempDf['price_type'] = waha_prices
        all_rich_wells = all_rich_wells.append(tempDf)
                           
        print(waha_prices)

    print(i)
    

all_wells = pd.DataFrame()
all_wells  = all_wells.append(all_rich_wells, ignore_index=True)
all_wells  = all_wells.append(all_lean_wells, ignore_index=True)
all_wells = all_wells[['Bucket','Asset', 'Type Curve', 'ethane_x', 'propane_x', 'butane_x','pentane', 'shrinkage', 'type', 'date_id', 'unshrunkgas','leanGas','ethane_yield', 'propane_yield', 'butane_yield', 'pentane_yield',
                       'ngl_yield', 'total_cost', 'total_altm_rev', 'total_sales_rev','gas_net', 'ngl_net', 'net_sales', 'apa_net_income', 'price_type']]


## Create a df of assets with positive revenue and their breakeven prices 
positive_prod = all_wells[(all_wells['apa_net_income'] > 0)]
bkvn_values = positive_prod.groupby(['Bucket','Asset', 'Type Curve', 'ethane_x', 'propane_x', 'butane_x','pentane', 'shrinkage', 'type', 'date_id', 'unshrunkgas','leanGas','ethane_yield', 'propane_yield', 'butane_yield', 'pentane_yield',
                       'ngl_yield']).min()['price_type'].reset_index()
bkvn_values = bkvn_values.sort_values(by=['price_type','unshrunkgas'], ascending= False).reset_index(drop=True)


# Saving the output
path = 'XXXX'
name = 'smrc_breakeven_' + str(today) + '.xlsx'
filepath = path + name 
    
dfs = {'all_well_sim_data': all_wells, 'bkvn_data':bkvn_values }
writer = pd.ExcelWriter(filepath, engine = 'xlsxwriter')
for sheetname in dfs.keys():
    print(sheetname)
    dfs[sheetname].to_excel(writer, sheet_name=sheetname, index = False)
writer.save()    

##############################################################################
##############################################################################
