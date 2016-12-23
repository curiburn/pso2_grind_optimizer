import pandas as pd 
import numpy as np
import copy
import sys

#成功率アップ(100%は別処理)
_BOOSTERS = {
    "+5%": 5, 
    "+10%": 10, 
    "+20%": 20, 
    "+30%": 30, 
    "100%": np.nan
}

#リスク軽減(Fullは別処理)
_REDUCERS = {
    "+1": 1, 
    "+2": 2, 
    "Full": np.nan
}

#スキップ
_SKIPS = {
    "→5": 5, 
    "→7": 7
}

class Grind:
    def __init__(self, infile_prob_table):
        #強化関連の初期化
        self.reset()
        
        #強化成功テーブルの設定
        self.set_prob_table(infile_prob_table)
        
        #使用する強化剤の初期化（セットは別のメソッドでやる）
        self.reducers = []
        self.boosters = []
        self.skip = ""
    
    
    def reset(self):
        self.level_grinded = 0
        self.count_grind = 0
        self.log_level_grinded = []
        self.consumed_reducers = {x: 0 for x in _REDUCERS.keys()}
        self.consumed_boosters = {x: 0 for x in _BOOSTERS.keys()}
        self.consumed_skips = {x: 0 for x in _SKIPS.keys()}
        
    
    def set_prob_table(self, infile_prob_table):
        in_prob_table = pd.read_csv(infile_prob_table, header=0, index_col=0)
        #行の和が100%になってるかチェック
        for row in in_prob_table.values:
            if(sum(row) != 100):
                sys.exit("sum is not 100")
        self.prob_table = in_prob_table
            
    
    
    def set_reducers(self, in_reducers):
        if(len(in_reducers) != len(self.prob_table.index)):
            sys.exit("length of reducer is not matched with probability table")
        else:
            self.reducers = in_reducers
    
    
    def set_boosters(self, in_boosters):
        if(len(in_boosters) != len(self.prob_table.index)):
            sys.exit("length of booster is not matched with probability table")
        else:
            self.boosters = in_boosters
            
            
    def set_skip(self, in_skip):
        if(in_skip not in _SKIPS.keys() and in_skip != "None"):
            sys.exit("skip %s is not available" % in_skip)
        self.skip = in_skip
    
    def grind_once(self):
        reducer = self.reducers[self.level_grinded]
        booster = self.boosters[self.level_grinded]
        
        #強化剤の消費カウント
        if reducer != "None":
            self.consumed_reducers[reducer] += 1
        if booster != "None":
            self.consumed_boosters[booster] += 1
        
        #強化回数のカウント
        self.count_grind += 1
        
        #強化成功100%の処理(処理が省けるから先にやっとく)
        if(booster == "100%"):
            self.level_grinded += 1
            self.log_level_grinded.append(self.level_grinded)
            return
        
        #現強化値の確率テーブルの取得
        prob_row = self.prob_table.iloc[self.level_grinded].copy()
        
        #リスク軽減の適用
        if reducer != "None":
            if reducer == "Full":
                #リスク軽減(完全)の処理
                prob_row["Fail-0"] += sum(prob_row["Fail-1":])
                prob_row["Fail-1":] = 0
            else:
                #軽減分だけ繰り返す
                for i in range(_REDUCERS[reducer]):
                    #リスク軽減(+1)分の処理
                    for j in range(len(prob_row)-1, 1, -1):
                        if prob_row[j] != 0:
                            prob_row[j-1] += prob_row[j]
                            prob_row[j] = 0
                            break
                
        
        #成功率アップの適用
        if booster != "None":
            prob_row["Success+1"] += _BOOSTERS[booster]
            tmp_booster_effect = _BOOSTERS[booster]
            for i in range(len(prob_row)-1, 0, -1):
                if prob_row[i] != 0:
                    if prob_row[i] > tmp_booster_effect:
                        prob_row[i] -= tmp_booster_effect
                        tmp_booster_effect = 0
                        break
                    else:
                        tmp_booster_effect -= prob_row[i]
                        prob_row[i] = 0
        
        #強化結果
        prob_row /= prob_row.sum()
        result = np.random.choice(a=range(len(prob_row)), p=prob_row)
        if(result == 0):
            self.level_grinded += 1
        else:
            self.level_grinded -= result - 1
        self.log_level_grinded.append(self.level_grinded)
    
    def grind_to10(self, reset=False):
        #スキップの適用
        if self.skip != "None":
            self.consumed_skips[skip] += 1
            self.level_grinded += _SKIPS[skip]
            self.count_grind += 1
        
        #ハゲるループ
        while self.level_grinded < 10:
            self.grind_once()
        
        #結果を保持
        result = copy.deepcopy(self.get_logging())
        
        #resetの実行
        if reset:
            self.reset()
            
        return result
    
    
    def get_logging(self):
        #成功率上昇の消費
        consumed_boosters = pd.DataFrame([self.consumed_boosters.values()], columns=self.consumed_boosters.keys())
        
        #リスク軽減の消費
        consumed_reducers = pd.DataFrame([self.consumed_reducers.values()], columns=self.consumed_reducers.keys())
        
        #スキップの消費
        consumed_skips = pd.DataFrame([self.consumed_skips.values()], columns=self.consumed_skips.keys())
        
        #データ構造を整える
        return_obj = {
            "count_grind": self.count_grind, 
            "consumed_boosters": consumed_boosters, 
            "consumed_reducers": consumed_reducers, 
            "consumed_skips": consumed_skips, 
            "log_level_grinded": self.log_level_grinded
        }
        
        return return_obj
