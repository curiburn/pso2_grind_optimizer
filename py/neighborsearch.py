import pandas as pd
import numpy as np
import copy

#基本的な近傍探索
#upgrade: 使う強化剤を一段回引き上げる
#   level["None", "+1"]のように、安いの順に
def upgrade(in_bee, type_item, level_item):
    bee = copy.deepcopy(in_bee)
    
    #強化剤のランクのリスト変換
    sol = [level_item.index(x) for x in bee["sol"][type_item]]
    
    #1段階良い強化剤を使うようにする
    #   最高の強化剤を使っていたらそのまま
    sol_upgraded = [x+1 if x+1 < len(level_item) else x for x in sol]
    
    #蜂への変更の適用
    #   fitはすべてNoneにする
    bee["sol"][type_item] = [level_item[x] for x in sol_upgraded]
    bee["fit"] = {x: None for x in bee["fit"].keys()}
    
    return bee


#downgrade: 使う強化剤を一段階引き下げる
def downgrade(in_bee, type_item, level_item):
    bee = copy.deepcopy(in_bee)
    
    #強化剤のランクのリスト変換
    sol = [level_item.index(x) for x in bee["sol"][type_item]]
    
    #1段階低い強化剤を使うようにする
    #   強化剤未使用はそのまま
    sol_downgraded = [x-1 if x-1 >= 0 else x for x in sol]
    
    #蜂への変更の適用
    #   fitはすべてNoneにする
    bee["sol"][type_item] = [level_item[x] for x in sol_downgraded]
    bee["fit"] = {x: None for x in bee["fit"].keys()}
    
    return bee

#flatten: 使う強化剤を平滑化する
#   ["None", "+1", "None, "None", "+2", "+1"]
#   -> ["None", "+1", "+1", "+1", "+2", "+2"]みたいな
def flatten(in_bee, type_item, level_item):
    bee = copy.deepcopy(in_bee)
    
    #強化剤のランクのリスト変換
    sol = [level_item.index(x) for x in bee["sol"][type_item]]
    
    #平滑化の実行
    idx_current_item = 0
    sol_flattened = []
    for s in sol:
        if idx_current_item > s:
            #ランクの低い強化剤を使っていたら上書き
            sol_flattened.append(idx_current_item)
            
        else:
            #ランクの高い強化剤を使っていたらidx_current_item
            idx_current_item = s
            sol_flattened.append(idx_current_item)
    
    #蜂への変更の適用
    #   fitはすべてNoneにする
    bee["sol"][type_item] = [level_item[x] for x in sol_flattened]
    bee["fit"] = {x: None for x in bee["fit"].keys()}
    
    return bee

#flatten_: 使う強化剤を両方とも平滑化する
#   levels_item={'reducer': ["None", "+1"], 'booster': ["None", "+10%"]}みたいな
def flatten_both(in_bee, levels_item):
    bee = copy.deepcopy(in_bee)
    
    #各強化剤でflattenを実行
    bee['sol'] = {item: flatten(bee, item, levels_item[item])['sol'][item] for item in levels_item.keys()}
    
    #蜂のfitを消す
    bee["fit"] = {x: None for x in bee["fit"].keys()}
    
    return bee