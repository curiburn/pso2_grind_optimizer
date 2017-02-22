

def flatten_sol(sol_obj, type_item, level_item):
    #type_indexで数値に変換
    sol = [level_item.index(x) for x in sol_obj[type_item]]
    
    #flatの実行
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
    
    return [level_item[x] for x in sol_flattened]


def is_flattened_sol(sol_obj, type_item, level_item):
    #type_indexで数値に変換
    sol = [level_item.index(x) for x in sol_obj[type_item]]
    
    result = True
    idx_current_item = 0
    for s in sol:
        if idx_current_item > s:
            result = False
            break
        else:
            idx_current_item = s
    
    return result