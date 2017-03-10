import pandas as pd
import numpy as np
import copy
import math

OBJ_AVAILABLE = ['max', 'min']


class Archive:
    def __init__(self, max_or_min):
        self._length = 0
        self._archive = {}
        self._current_colony = []
        self._tmp_whole_colony = []
        
        #目的関数の最小化、最大化を
        for obj in max_or_min:
            if max_or_min[obj] not in OBJ_AVAILABLE:
                sys.exit('unnavailable object "%s" (%s is surported)' % (obj, str(OBJ_AVAILABLE)))
        self.max_or_min = max_or_min
        
        #kth-nearist なんとか
        self.D = 0.5
        
    
    #archiveに追加
    #支配の検査はしていない
    def _add_bee(self, bee):
        #解をそのままkeyにして重複を弾く
        key = str(bee["sol"].values)
        
        if key not in self._archive.keys():
            self._archive.update({key: bee})
    
    
    #コロニーの追加
    def update_archive_from_colony(self, colony):
        #解の評価に使うコロニーの更新
        self._tmp_whole_colony = []
        self._tmp_whole_colony.extend(copy.deepcopy(colony))
        self._tmp_whole_colony.extend(copy.deepcopy(list(self._archive.values())))
        
        #archiveの更新
        #   archiveを一旦消す
        #   Q(bee)をtmp_whole_colonyに対して計算
        #   Q(bee)>1であればarchiveに追加
        self._archive = {}
        tmp_whole_colony = []
        for bee in self._tmp_whole_colony:
            bee = self.Q(bee)
            if bee['Q'] > 1:
                self._add_bee(bee)
            tmp_whole_colony.append(bee)
        print("archived bee: %s" % len(self._archive))
        
        #archiveの更新に伴う解の評価に使うコロニーの更新
        self._tmp_whole_colony = tmp_whole_colony[0:len(colony)]
        self._tmp_whole_colony.extend(copy.deepcopy(list(self._archive.values())))
        
        #k-th nearest なんとかの更新
        self.D = 1.0 / (math.sqrt(len(colony) + len(self._archive)) + 2)
        
        #Qを計算したコロニーを返す
        return copy.deepcopy(self._tmp_whole_colony[0:len(colony)])
    
    #多分使わない、デバッグ用
    def remove_bee(self, bee):
        key = str(best_bee["sol"])
        
        if key in self._archive.keys():
            del self._archive[key]
    
    
    def get_archive(self):
        colony_archived = copy.deepcopy(list(self._archive.values()))
        return colony_archived
    
    
    def is_dominating(self, dominator, dominatee, weak=True):
        if weak:
            #弱支配であれば、一つだけ(dominator)>(dominatee)で、他は(dominator)>=(dominatee)
            dominated = False
            for obj in dominator['fit'].keys():
                #弱い意味でのパレート支配
                #一つだけ満たせばいい条件(dominator)>(dominatee)
                if \
                    (self.max_or_min[obj] == 'max' and dominator['fit'][obj] > dominatee['fit'][obj]) or \
                    (self.max_or_min[obj] == 'min' and dominator['fit'][obj] < dominatee['fit'][obj]):
                    dominated = True
                
                #全てにおいて満たすべき条件(dominator)>=(dominatee)
                if \
                    (self.max_or_min[obj] == 'max' and dominator['fit'][obj] < dominatee['fit'][obj]) or \
                    (self.max_or_min[obj] == 'min' and dominator['fit'][obj] > dominatee['fit'][obj]):
                    dominated = False
                    break
        else:
            #パレート支配
            #   ふつうの支配であれば、全てにおいて(dominator)>(dominatee)を満たす
            dominated = True
            for obj in dominator['fit'].keys():
                if \
                    (self.max_or_min[obj] == 'max' and dominator['fit'][obj] <= dominatee['fit'][obj]) or \
                    (self.max_or_min[obj] == 'min' and dominator['fit'][obj] >= dominatee['fit'][obj]):
                    dominated = False
                    break
        
        return dominated
    
    
    def get_dominator(self, bee, weak=False):
        dominator = [x for x in self._tmp_whole_colony if self.is_dominating(x, bee, weak)]
        return dominator
    
    
    def get_dominatee(self, bee, weak=False):
        dominatee = [x for x in self._tmp_whole_colony if self.is_dominating(bee, x, weak)]
        return dominatee
    
    
    def S(self, bee):
        #beeが支配している解の個数
        #   弱支配にしておく
        S = len(self.get_dominatee(bee, weak=True))
        
        return S
    
        
    def R(self, bee):
        #beeを支配している解を取ってくる
        dominator = self.get_dominator(bee)
        
        #calc R(i) from sum of S
        #   支配している解のStrengthの総和
        R = sum([self.S(bee) for bee in dominator])
        
        return R
        
        
    def Q(self, in_bee):
        bee = copy.deepcopy(in_bee)
        
        Q = 1.0 / (self.D + self.R(bee))
        bee["Q"] = Q
        return bee
    
