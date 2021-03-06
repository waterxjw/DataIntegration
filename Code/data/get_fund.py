import requests
import tushare as ts
import retrying
import time
import pandas as pd
ts.set_token('ed713a2e27e3930b752d0638476753e267a66c1a6addd2bcf41659b7')
pro = ts.pro_api()
from sqlalchemy import create_engine
engine=create_engine('mysql+pymysql://root:767443924@119.3.210.244/data_integration')

def get_tscodes_list():
    sql='select distinct ts_code from company '
    ts_codes=pd.read_sql(sql,engine)
    return ts_codes['ts_code']

from retrying import retry
@retry(stop_max_attempt_number=500, wait_random_min=1000, wait_random_max=5000)
def request_data(code):
    headers={
    "Host": "stock.xueqiu.com",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    'Upgrade-Insecure-Requests': '1',
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36",
    "Referer": "http://www.chinamoney.com.cn/chinese/sddsintigy/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": "device_id=78f58a46931405dae848938b8685d4eb; s=cj1chc2hyh; xq_a_token=ea139be840cf88ff8c30e6943cf26aba8ad77358; xqat=ea139be840cf88ff8c30e6943cf26aba8ad77358; xq_r_token=863970f9d67d944596be27965d13c6929b5264fe; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTU5NDAwMjgwOCwiY3RtIjoxNTkzNDk0OTUwNDc1LCJjaWQiOiJkOWQwbjRBWnVwIn0.Bp8Y6-LJ8c7w0MoWieQqc3UDfNkQVa3l3eat6YR4OyCB_p8e2_ktyt_3cHjWxZNkut2udMZJMs5x9klZIAdwtfWawWrAFBhJqy1aecftQ6DpM8pzQrUcLp-SEXgCKv_8bnfmeSWYIw69ab6MjVuESaqlHG4uiyCUPRhtTFsHM3MZeXkpVVIrjJgJ8C0tl2xDBIULdc53Iay5yQEljvDACSDQu39XOpgXwA_pl9vYaxgVjseleO3juQ459FqgPDTZPdz7d89pt2NIbrYiwCId-bSjIyVYikrE3Zo2RgxfP7kP1ClvsZSgnD5vbw4hvRO5DAW44t-5T_YqbthxQfp5Yw; u=831593494981746; Hm_lvt_1db88642e346389874251b5a1eded6e3=1593135130,1593418227,1593437602,1593494982; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1593495638"
}
    
    symbol=code.split('.')[1]+code.split('.')[0]
    
    params={'symbol':symbol,'extend':'true'}

    url="https://stock.xueqiu.com/v5/stock/f10/cn/org_holding/detail.json"
    res=requests.get(url=url,params=params,headers=headers)
    print(res)
    data=res.json()
    return data

tscodes=get_tscodes_list()
df_list=[]
for i in range(len(tscodes)):
    code=tscodes[i]
    res=request_data(code)
    
    if len(res['data'])==0:
        continue
    fund_df=pd.DataFrame(res['data']['fund_items'])[1:11]
    fund_df.rename(columns={'org_name_or_fund_name':'fund_name'},inplace=True)
    fund_df.rename(columns={'to_float_shares_ratio':'share_ratio'},inplace=True)
    fund_df['hold_ts_code']=code
    fund_df=fund_df[[ 'fund_name', 'hold_ts_code','held_num', 'share_ratio']]
    df_list.append(fund_df)
    print(str(i)+" done")
result=pd.concat(df_list)
result=result.reset_index(drop=True)
result.to_sql('hold_fund', con=engine,index=True,index_label='id', if_exists='append')