import numpy as np
import pandas as pd
import sys
import copy
import gc
import multiprocessing as mp

import initialize as init
import simulator as sim
import fitness_count as fit_c
import fitness_item as fit_i
import archive as ac
import neighborsearch as ns


#引数
infile_prob_table = sys.argv[1]
input_proc = sys.argv[2]
input_price_grind = sys.argv[3]

#読み込み
INFILE_TABLE = str(infile_prob_table)

#並列化数
PROC = int(input_proc)

#適用するアイテムの設定
USE_SKIP = "None"
NAMES_ITEM = {
    "reducer": ["None", "+1", "+2"], 
    "booster": ["None", "+5%", "+10%", "+30%"]
}
NAMES_ITEM_ENONE = {x: NAMES_ITEM[x][1:] for x in NAMES_ITEM}

#一回の強化費用
PRICE_GRIND = float(input_price_grind)

#ハイパーパラメータ
#   N:ループ数, M: 蜂の数
N = 100
M_employed = 20
M_onlooker = 20

#蜂関係
LIMIT = 3

#強化シミュレータの設定
NUM_AVE = 100
DODO = sim.Grind(INFILE_TABLE)
DODO.set_skip(USE_SKIP)

#蜂の生成に使うインスタンスの設定
gen = init.Bee(INFILE_TABLE, NAMES_ITEM)
gen.calculate_weights()

#archiveの設定
arc = ac.Archive({'count': 'min', 'item': 'min'})

#収穫蜂のコロニーの初期化
colony_employed = [\
    {'sol': gen.generate_bee_sol(), 'fit': {'count': None, 'item': None}, 'Q': np.nan, 't': 0}\
    for x in range(M_employed)\
]

#シミュレータを動かす関数(並列化用)
def simulator(in_bee, num_ave=NUM_AVE):
    if None in in_bee["fit"].values():
        bee = copy.deepcopy(in_bee)
        
        #アイテムの適用タイミングを設定
        sim_instance = copy.deepcopy(DODO)
        sim_instance.set_reducers(bee['sol']['reducer'])
        sim_instance.set_boosters(bee['sol']['booster'])
        
        #結果をリストにまとめる
        results = [sim_instance.grind_to10() for x in range(num_ave)]
        
        #各評価関数の適用
        bee['fit']['count'] = fit_c.fit_count(results, PRICE_GRIND)
        bee['fit']['item'] = fit_i.fit_item(results, NAMES_ITEM_ENONE)
        
        return bee
    
    else:
        return in_bee
    

#メインループ
for i in range(N):
    #収穫蜂(SPEAでいう1世代)
    sys.stderr.write("%d th employed phase...\n" % i)
    #各オペレータの適用
    #   適用するオペレータがアップグレードとダウングレードのみ
    #   適用したオペレータごとにコロニーが生成
    tmp_colony_whole = copy.deepcopy(colony_employed)
    tmp_colony_whole.extend([ns.upgrade(bee, "booster", NAMES_ITEM['booster']) for bee in colony_employed])
    tmp_colony_whole.extend([ns.downgrade(bee, "booster", NAMES_ITEM['booster']) for bee in colony_employed])
    tmp_colony_whole.extend([ns.upgrade(bee, "reducer", NAMES_ITEM['reducer']) for bee in colony_employed])
    tmp_colony_whole.extend([ns.downgrade(bee, "reducer", NAMES_ITEM['reducer']) for bee in colony_employed])
    
    #全コロニーの適応値を計算
    #   シミュレータにかける
    #   各目的関数で結果をparse
    p = mp.Pool(PROC)
    tmp_colony_whole = p.map(simulator, tmp_colony_whole)
    p.close()
    
    #全コロニーを用いてarchiveを更新
    #   Qが計算されたものが帰ってくる
    tmp_colony_whole = arc.update_archive_from_colony(tmp_colony_whole)
    
    #コロニーの連結を解除
    #   オペレータ適用前、適用後で分ける
    #   収穫蜂の数でぴったり割り切れるはず
    colonies = [tmp_colony_whole[x: x + M_employed] for x in range(int(len(tmp_colony_whole) / M_employed))]
    colony_employed = colonies[0]
    colonies_employed_operated = colonies[1:]
    
    #収穫蜂のコロニーの更新
    #   Q(i)が上がったもの(改良された解)のみオペレータを適用
    for (j, bee) in enumerate(colony_employed):
        #オペレータを適用した蜂を取ってくる
        bees_operated = [colony[j] for colony in colonies_employed_operated]
        
        #オペレータを適用した中で最もQが高い蜂を取ってくる
        idx_best_bee_operated = np.argmax([bee['Q'] for bee in bees_operated])
        best_bee_operated = bees_operated[idx_best_bee_operated]
        
        #オペレータ適用前と比較して更新
        #   tのリセットもする
        if best_bee_operated['Q'] > bee['Q']:
            colony_employed[j] = copy.deepcopy(best_bee_operated)
            colony_employed[j]['t'] = 0
        else:
            colony_employed[j]['t'] += 1
    
    
    #追従蜂
    sys.stderr.write("%d th onlooker phase...\n" % i)
    #追従蜂の初期化
    #   収穫蜂のコロニーのQ(i)を重みとしてランダムに選択
    weights_colony_employed = np.array([bee['Q'] for bee in colony_employed])
    weights_colony_employed /= sum(weights_colony_employed)
    colony_onlooker = [\
        copy.deepcopy(np.random.choice(colony_employed, p=weights_colony_employed))\
        for x in range(M_onlooker)\
    ]
    
    
    #各オペレータの適用
    #   適用するオペレータがアップグレードとダウングレードと平滑化
    #   適用したオペレータごとにコロニーが生成
    tmp_colony_whole = copy.deepcopy(colony_onlooker)
    tmp_colony_whole.extend([ns.upgrade(bee, "booster", NAMES_ITEM['booster']) for bee in colony_onlooker])
    tmp_colony_whole.extend([ns.downgrade(bee, "booster", NAMES_ITEM['booster']) for bee in colony_onlooker])
    tmp_colony_whole.extend([ns.upgrade(bee, "reducer", NAMES_ITEM['reducer']) for bee in colony_onlooker])
    tmp_colony_whole.extend([ns.downgrade(bee, "reducer", NAMES_ITEM['reducer']) for bee in colony_onlooker])
    tmp_colony_whole.extend([ns.flatten(bee, "reducer", NAMES_ITEM['reducer']) for bee in colony_onlooker])
    tmp_colony_whole.extend([ns.flatten(bee, "booster", NAMES_ITEM['booster']) for bee in colony_onlooker])
    
    #全コロニーの適応値を計算
    #   シミュレータにかける
    #   各目的関数で結果をparse
    p = mp.Pool(PROC)
    tmp_colony_whole = p.map(simulator, tmp_colony_whole)
    p.close()
    
    #全コロニーを用いてarchiveを更新
    #   Qが計算されたものが帰ってくる
    tmp_colony_whole = arc.update_archive_from_colony(tmp_colony_whole)
    
    #コロニーの連結を解除
    #   オペレータ適用前、適用後で分ける
    #   追従蜂の数でぴったり割り切れるはず
    colonies = [tmp_colony_whole[x: (x + M_employed)] for x in range(int(len(tmp_colony_whole) / M_employed))]
    colony_onlooker = colonies[0]
    colonies_onlooker_operated = colonies[1:]
    
    #追従蜂のコロニーの更新
    #   Q(i)が上がったもの(改良された解)のみオペレータを適用
    for (j, bee) in enumerate(colony_onlooker):
        #オペレータを適用した蜂を取ってくる
        bees_operated = [colony[j] for colony in colonies_onlooker_operated]
        
        #オペレータを適用した中で最もQが高い蜂を取ってくる
        idx_best_bee_operated = np.argmax([bee['Q'] for bee in bees_operated])
        best_bee_operated = bees_operated[idx_best_bee_operated]
        
        #オペレータ適用前と比較して更新
        if best_bee_operated['Q'] > bee['Q']:
            colony_onlooker[j] = copy.deepcopy(best_bee_operated)
    
    #偵察蜂
    sys.stderr.write("%d th scout phase...\n" % i)
    #   LIMITに達した収穫蜂をジェネレータを使って最初期化
    gen.calculate_weights()
    for bee in colony_employed:
        if bee['t'] >= LIMIT:
            bee['sol'] = gen.generate_bee_sol()
            bee['fit'] = {'count': None, 'item': None}
            bee['Q'] = np.nan
            bee['t'] = 0
    
    
    #収穫蜂と追従蜂からもっともQが高い蜂を選び、世代の最適解としてフェロモンを更新
    sys.stderr.write("%d th pheromone updating phase...\n" % i)
    colony_all = colony_employed + colony_onlooker
    idx_gbest_bee = np.nanargmax([bee['Q'] for bee in colony_all])
    gbest_bee = colony_all[idx_gbest_bee]
    gen.update_pheromone(gbest_bee)
    


#fin
#   archiveにいる蜂を出力して終わり
archived_bee = arc.get_archive()
print(archived_bee)