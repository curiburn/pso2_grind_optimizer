import pandas as pd
import sys

#ネカフェポイント換算
#成功率アップ(100%は別処理)
_BOOSTERS = {
    "+5%": 45, 
    "+10%": 150, 
    "+20%": 400, 
    "+30%": 600
}

#リスク軽減(Fullは別処理)
_REDUCERS = {
    "+1": 45, 
    "+2": 180
}

#成功率アップとリスク軽減の重み
#   FUNスクラッチの排出率的にも、
#   成功率アップ > リスク軽減
#   な重みがあってもいいと思う
_WEIGHT_BOOSTER = 20


def fit_booster(in_df):
    in_dict = in_df.to_dict('records')[0]
    if False in [i in _BOOSTERS.keys() for i in in_dict.keys()]:
        sys.exit("unavailable booster used(\"%s\" is available)" % ",".join(_BOOSTERS.keys()))
    
    score = sum([_BOOSTERS[i] * in_dict[i] for i in in_dict])
    return score


def fit_reducer(in_df):
    in_dict = in_df.to_dict('records')[0]
    if False in [i in _REDUCERS.keys() for i in in_dict.keys()]:
        sys.exit("unavailable reducer used(\"%s\" is available)" % ",".join(_REDUCERS.keys()))
    
    score = sum([_REDUCERS[i] * in_dict[i] for i in in_dict])
    return score


#実際に呼び出すのはこれ
def fit_item(results, names_item):
    #結果から必要なデータを取ってくる
    cons_booster = [x["consumed_boosters"] for x in results]
    cons_reducer = [x["consumed_reducers"] for x in results]
    
    #平均を取ってくる
    ave_cons_booster = (sum(cons_booster).multiply(1.0) / len(cons_booster)).copy()
    ave_cons_reducer = (sum(cons_reducer).multiply(1.0) / len(cons_reducer)).copy()
    
    score = _WEIGHT_BOOSTER * fit_booster(ave_cons_booster[names_item['booster']]) + fit_reducer(ave_cons_reducer[names_item['reducer']])
    return score
