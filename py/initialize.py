import pandas as pd
import numpy as np
import sys

 
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
        
        #フェロモンの付与
        self.d_pheromone = 1
        
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
        
        #重みの正規化(行方向)
        for i in range(self.grind_length):
            #0割防止
            if sum(self.weights_booster.iloc[i]) != 0:
                self.weights_booster.iloc[i] /= sum(self.weights_booster.iloc[i])
            if sum(self.weights_reducer.iloc[i]) != 0:
                self.weights_reducer.iloc[i] /= sum(self.weights_reducer.iloc[i])
        
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
        
        #返す
        return {"booster": sol_booster, "reducer": sol_reducer}
        
    
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
            
            #データ構造整理して突っ込む
            self.pheromones = {"booster": pheromones_booster, "reducer": pheromones_reducer}
        
        #フェロモンの更新
        else:
            #解を取ってくる
            boosters_best = bee_best["sol"]["booster"]
            reducers_best = bee_best["sol"]["reducer"]
            
            #解に該当するところにフェロモンを付与
            for i in range(self.grind_length):
                self.pheromones["booster"].iloc[i][boosters_best[i]] += self.d_pheromone
                self.pheromones["reducer"].iloc[i][reducers_best[i]] += self.d_pheromone
        
        #蜂の初期化の重みフラグをおる
        self.is_weight_calculated = False
