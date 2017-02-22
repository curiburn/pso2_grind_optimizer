import pandas as pd
import numpy as np
import sys

import flat

 
class Bee:
    def __init__(self, infile_prob_table, in_names_item):
        #強化成功テーブルの読み込み
        self.set_prob_table(infile_prob_table)
        self.grind_length = len(self.prob_table.index)
        
        #扱うアイテムの設定
        self.names_booster = in_names_item["booster"]
        self.names_reducer = in_names_item["reducer"]
        
        #ヒューリスティクスの計算(初期化)
        self.init_heuristics()
        
        #フェロモンの初期化
        self.update_pheromone()
        
        #付与されるフェロモン量
        self.d_pheromone = 1.0
        
        #フェロモンの蒸発率
        self.roh = 0.1
        
        #ヒューリスティクスとフェロモンの重み
        self._weight_h = 1
        
        #解生成時の選択アルゴリズムの重み
        self.Q0 = 0.5
        
        #初期化時の重みを計算
        self.is_weight_calculated = False
        self.calculate_weights()
    
    
    def set_prob_table(self, infile_prob_table):
        in_prob_table = pd.read_csv(infile_prob_table, header=0, index_col=0)
        #行の和が100%になってるかチェック
        for row in in_prob_table.values:
            if(sum(row) != 100):
                sys.exit("sum is not 100")
        self.prob_table = in_prob_table
        
    
    #初期化時の重みの計算
    def calculate_weights(self):
        #重みの計算
        self.weights_booster = (self.heuristics["booster"] ** self._weight_h) * self.pheromones["booster"]
        self.weights_reducer = (self.heuristics["reducer"] ** self._weight_h) * self.pheromones["reducer"]
        self.weights_flat = (1.0 ** self._weight_h) * self.pheromones["flat"]
        
        #重みの正規化(行方向)
        for i in range(self.grind_length):
            #0割防止
            if sum(self.weights_booster.iloc[i]) != 0:
                self.weights_booster.iloc[i] /= sum(self.weights_booster.iloc[i])
            if sum(self.weights_reducer.iloc[i]) != 0:
                self.weights_reducer.iloc[i] /= sum(self.weights_reducer.iloc[i])
        
        #重みの正規化(flat)
        self.weights_flat["value"] /= sum(self.weights_flat["value"])
        
        #フラグを立てる
        self.is_weight_calculated = True
    
    #計算した重みで蜂を生成
    def generate_bee_sol(self):
        #重みの計算を確認
        if not self.is_weight_calculated:
            sys.exit("weight is not calated")
            
        #解の生成
        #   重み付ランダムか、最大重みか
        if np.random.rand() > self.Q0:
            sol_booster = [np.random.choice(self.names_booster, p=self.weights_booster.iloc[i]) for i in range(self.grind_length)]
            sol_reducer = [np.random.choice(self.names_reducer, p=self.weights_reducer.iloc[i]) for i in range(self.grind_length)]
        else:
            sol_booster = [self.names_booster[np.argmax(self.weights_booster.iloc[i].values)] for i in range(self.grind_length)]
            sol_reducer = [self.names_reducer[np.argmax(self.weights_reducer.iloc[i].values)] for i in range(self.grind_length)]
        sol_obj = {"booster": sol_booster, "reducer": sol_reducer, "flat_init": False}
        
        #flatの処理
        is_do_flatted = np.random.choice(self.weights_flat.index, p=self.weights_flat["value"]) == "True"
        print(is_do_flatted)
        if is_do_flatted:
            sol_obj["booster"] = flat.flatten_sol(sol_obj, "booster", list(self.pheromones["booster"].columns))
            sol_obj["reducer"] = flat.flatten_sol(sol_obj, "reducer", list(self.pheromones["reducer"].columns))
            sol_obj["flat_init"] = True
        
        #返す
        return sol_obj

    
    def init_heuristics(self):
        heuristics_booster = []
        heuristics_reducer = []
        for i in self.prob_table.index:
            #失敗発生
            #   失敗が発生したら使っても良い
            if(sum(self.prob_table.iloc[i]["Fail-0":]) != 0):
                tmp_booster = [1 for i in self.names_booster]
            else:
                tmp_booster = [0 for i in self.names_booster]
                tmp_booster[0] = 1
            heuristics_booster.append(tmp_booster)
            
            #リスク発生
            if(sum(self.prob_table.iloc[i]["Fail-1":]) != 0):
                tmp_reducer = [1 for i in self.names_reducer]
            else:
                tmp_reducer = [0 for i in self.names_reducer]
                tmp_reducer[0] = 1
            heuristics_reducer.append(tmp_reducer)
        
        #データフレームに変換
        heuristics_booster = pd.DataFrame(heuristics_booster, columns=self.names_booster)
        heuristics_reducer = pd.DataFrame(heuristics_reducer, columns=self.names_reducer)
        
        self.heuristics = {"booster": heuristics_booster, "reducer": heuristics_reducer}
        
        #蜂の初期化の重みフラグをおる
        self.is_weight_calculated = False
        
        
    #フェロモンの更新
    def update_pheromone(self, bee_best=None):
        #初期化
        if bee_best == None:
            #1で埋める
            pheromones_booster = pd.DataFrame(np.ones((self.grind_length, len(self.names_booster))), columns=self.names_booster)
            pheromones_reducer = pd.DataFrame(np.ones((self.grind_length, len(self.names_reducer))), columns=self.names_reducer)
            pheromones_flat = pd.DataFrame(np.ones(2), index=['True', 'False'], columns=['value'])
            
            #データ構造整理して突っ込む
            self.pheromones = {"booster": pheromones_booster, "reducer": pheromones_reducer, "flat": pheromones_flat}
        
        #フェロモンの更新
        else:
            #最適解の取得
            boosters_best = bee_best["sol"]["booster"]
            reducers_best = bee_best["sol"]["reducer"]
            is_flat = \
                flat.is_flattened_sol(bee_best["sol"], "booster", list(self.pheromones["booster"].columns)) and \
                flat.is_flattened_sol(bee_best["sol"], "reducer", list(self.pheromones["reducer"].columns))
            
            #フェロモンの蒸発
            for key in self.pheromones.keys():
                self.pheromones[key] *= self.roh
            
            #フェロモンの付与
            for i in range(self.grind_length):
                self.pheromones["booster"].loc[i][boosters_best[i]] += bee_best['Q']
                self.pheromones["reducer"].loc[i][reducers_best[i]] += bee_best['Q']
            self.pheromones["flat"].loc[str(is_flat)] += bee_best['Q']
        
        #蜂の初期化の重みフラグをおる
        self.is_weight_calculated = False
