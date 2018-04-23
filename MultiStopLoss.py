# -*- coding: utf-8 -*-
'''
多目标综合止损
'''
import pandas as pd
import DATA_CONSTANTS as DC
import numpy as np
import os
import ResultStatistics as RS
import multiprocessing
from DynamicStopLoss import *
from OnceWinNoLoss import  *

def multiStopLosslCal(stratetyName,symbolInfo,K_MIN,setname,stopLossTargetDictList,positionRatio,initialCash,tofolder):
    print 'setname:', setname
    symbol=symbolInfo.symbol
    oprdf = pd.read_csv(symbol + str(K_MIN) + ' ' + setname + ' result.csv')
    oprlist=[]
    sltnum=len(stopLossTargetDictList)
    for i in range(sltnum):
        slt=stopLossTargetDictList[i]
        #遍历读取各止损目标的结果文件,按名称将结果写入oprdf中
        sltdf=pd.read_csv("%s%s %s%d %s %s"%(slt['folder'],stratetyName,symbol,K_MIN,setname,slt['fileSuffix']))
        sltName=slt['name']
        oprdf[sltName+'_closeprice'] = sltdf['new_closeprice']
        oprdf[sltName+'_closetime'] = sltdf['new_closetime']
        oprdf[sltName+'_closeindex'] = sltdf['new_closeindex']
        oprdf[sltName+'_closeutc'] = sltdf['new_closeutc']
        oprdf[sltName+'_ret'] = sltdf['new_ret']
        oprlist.append(sltdf)
    #dsloprname=stratetyName+' '+symbol + str(K_MIN) + ' ' + setname + ' resultDSL_by_tick.csv'
    #ownloprname=stratetyName+' '+symbol + str(K_MIN) + ' ' + setname + ' resultOWNL_by_tick.csv'
    #dsloprdf=pd.read_csv(dslFolder+dsloprname)
    #ownloprdf=pd.read_csv(ownlFolder+ownloprname)

    oprdf['new_closeprice'] = oprdf['closeprice']
    oprdf['new_closetime'] = oprdf['closetime']
    oprdf['new_closeindex'] = oprdf['closeindex']
    oprdf['new_closeutc'] = oprdf['closeutc']
    oprdf['min_closeutc']=oprdf['closeutc']
    for i in range(sltnum):
        #先取最早平仓的时间，再根据时间去匹配类型
        slt=stopLossTargetDictList[i]
        utcname=slt['name']+'_closeutc'
        oprdf['min_closeutc']=oprdf['min_closeutc',utcname].min(axis=1)
    #根据最早平仓时间的结果，匹配平仓类型,不处理时间相同的情况
    oprdf['closetype']='Normal'
    for i in range(sltnum):
        slt=stopLossTargetDictList[i]
        name=slt['name']
        utcname=name+'_closeutc'
        oprdf.loc[oprdf['min_closeutc']==oprdf[utcname],'closetype'] = slt['name']
        oprdf.loc[oprdf['min_closeutc']==oprdf[utcname], 'new_closeprice']= oprdf[name+'_closeprice']
        oprdf.loc[oprdf['min_closeutc']==oprdf[utcname],'new_closetime'] = oprdf[name+'_closetime']
        oprdf.loc[oprdf['min_closeutc']==oprdf[utcname],'new_closeindex'] = oprdf[name+'_closeindex']
        oprdf.loc[oprdf['min_closeutc']==oprdf[utcname],'new_closeutc'] = oprdf[name+'_closeutc']

    slip=symbolInfo.getSlip()
    # 2017-12-08:加入滑点
    oprdf['new_ret'] = ((oprdf['new_closeprice'] - oprdf['openprice']) * oprdf['tradetype']) - slip
    oprdf['new_ret_r'] = oprdf['new_ret'] / oprdf['openprice']
    oprdf['new_commission_fee'], oprdf['new_per earn'], oprdf['new_own cash'], oprdf['new_hands'] = RS.calcResult(oprdf,
                                                                                                      symbolInfo,
                                                                                                      initialCash,
                                                                                                      positionRatio,ret_col='new_ret')
    oprdf.to_csv(tofolder+stratetyName+' '+symbol + str(K_MIN) + ' ' + setname + ' result_multiSLT.csv')

    #计算统计结果
    oldendcash = oprdf['own cash'].iloc[-1]
    oldAnnual = RS.annual_return(oprdf)
    oldSharpe = RS.sharpe_ratio(oprdf)
    oldDrawBack = RS.max_drawback(oprdf)[0]
    oldSR = RS.success_rate(oprdf)
    newendcash = oprdf['new_own cash'].iloc[-1]
    newAnnual = RS.annual_return(oprdf,cash_col='new_own cash',closeutc_col='new_closeutc')
    newSharpe = RS.sharpe_ratio(oprdf,cash_col='new_own cash',closeutc_col='new_closeutc',retr_col='new_ret_r')
    newDrawBack = RS.max_drawback(oprdf,cash_col='new_own cash')[0]
    newSR = RS.success_rate(oprdf,ret_col='new_ret')
    slWorkNum=oprdf.loc[oprdf['closetype']!='Normal'].shape[0]
    return [setname,slWorkNum,oldendcash,oldAnnual,oldSharpe,oldDrawBack,oldSR,newendcash,newAnnual,newSharpe,newDrawBack,newSR]


if __name__ == '__main__':
    pass