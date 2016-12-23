import numpy as np
import pandas as pd
import sys
import copy
import gc
import multiprocessing as mp
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ptick

import initialize as init
import simulator as sim
import fitness_count as fit_c
import fitness_item as fit_i
import archive as ac
import neighborsearch as ns


class MOABC:
    def __init__(self, infile_prob_table, input_price_grind):
        #読み込み
        self.infile_table = str(infile_prob_table)

        #並列化数
        self.proc = 1

        #適用するアイテムの設定
        self.use_skip = "None"
        self.names_item = {
            "reducer": ["None", "+1", "+2"], 
            "booster": ["None", "+5%", "+10%", "+30%"]
        }
        self.names_item_enone = {x: self.names_item[x][1:] for x in self.names_item}

        #一回の強化費用
        self.price_grind = float(input_price_grind)

        #ハイパーパラメータ
        #   N:ループ数, M: 蜂の数
        self.N = 60
        self.M_employed = 10
        self.M_onlooker = 20

        #蜂関係
        self.LIMIT = 3

        #強化シミュレータの設定
        self.num_average = 100
        self.dodo = sim.Grind(self.infile_table)
        self.dodo.set_skip(self.use_skip)

        #蜂の生成に使うインスタンスの設定
        self.gen = init.Bee(self.infile_table, self.names_item)
        self.gen.calculate_weights()

        #self.archiveの設定
        self.arc = ac.Archive({'count': 'min', 'item': 'min'})
        
        #archivesの初期化
        self.archives = []

    #シミュレータを動かす関数(並列化用)
    def simulator(self, in_bee):
        if None in in_bee["fit"].values():
            bee = copy.deepcopy(in_bee)
            
            #アイテムの適用タイミングを設定
            sim_instance = copy.deepcopy(self.dodo)
            sim_instance.set_reducers(bee['sol']['reducer'])
            sim_instance.set_boosters(bee['sol']['booster'])
            
            #結果をリストにまとめる
            results = [sim_instance.grind_to10(reset=True) for x in range(self.num_average)]
            
            #各評価関数の適用
            bee['fit']['count'] = fit_c.fit_count(results, self.price_grind)
            bee['fit']['item'] = fit_i.fit_item(results, self.names_item_enone)
            
            return bee
        
        else:
            return in_bee
        

    #メインループ
    def learn(self):
        #収穫蜂の初期化
        self.gen.calculate_weights()
        colony_employed = [\
            {'sol': self.gen.generate_bee_sol(), 'fit': {'count': None, 'item': None}, 'Q': np.nan, 't': 0}\
            for x in range(self.M_employed)\
        ]
        
        for i in range(self.N):
            #収穫蜂のフェーズ
            sys.stderr.write("%d th employed phase...\n" % i)
            #各オペレータの適用
            #   適用するオペレータがアップグレードとダウングレードのみ
            #   適用したオペレータごとにコロニーが生成
            tmp_colony_whole = copy.deepcopy(colony_employed)
            tmp_colony_whole.extend([ns.flatten_both(bee, self.names_item) for bee in colony_employed])
            
            #全コロニーの適応値を計算
            #   シミュレータにかける
            #   各目的関数で結果をparse
            p = mp.Pool(self.proc)
            tmp_colony_whole = p.map(self.simulator, tmp_colony_whole)
            p.close()
            
            #全コロニーを用いてself.archiveを更新
            #   Qが計算されたものが帰ってくる
            tmp_colony_whole = self.arc.update_archive_from_colony(tmp_colony_whole)
            
            #コロニーの連結を解除
            #   オペレータ適用前、適用後で分ける
            #   収穫蜂の数でぴったり割り切れるはず
            colonies = [tmp_colony_whole[x: x + self.M_employed] for x in range(int(len(tmp_colony_whole) / self.M_employed))]
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
            
            #追従蜂のフェーズ
            sys.stderr.write("%d th onlooker phase...\n" % i)
            #追従蜂の初期化
            #   収穫蜂のコロニーのQ(i)を重みとしてランダムに選択
            weights_colony_employed = np.array([bee['Q'] for bee in colony_employed])
            weights_colony_employed /= sum(weights_colony_employed)
            colony_onlooker = [\
                copy.deepcopy(np.random.choice(colony_employed, p=weights_colony_employed))\
                for x in range(self.M_onlooker)\
            ]
            
            #各オペレータの適用
            #   適用するオペレータがアップグレードとダウングレードと平滑化
            #   適用したオペレータごとにコロニーが生成
            tmp_colony_whole = copy.deepcopy(colony_onlooker)
            tmp_colony_whole.extend([ns.upgrade(bee, "booster", self.names_item['booster']) for bee in colony_onlooker])
            tmp_colony_whole.extend([ns.downgrade(bee, "booster", self.names_item['booster']) for bee in colony_onlooker])
            tmp_colony_whole.extend([ns.upgrade(bee, "reducer", self.names_item['reducer']) for bee in colony_onlooker])
            tmp_colony_whole.extend([ns.downgrade(bee, "reducer", self.names_item['reducer']) for bee in colony_onlooker])

            
            #全コロニーの適応値を計算
            #   シミュレータにかける
            #   各目的関数で結果をparse
            p = mp.Pool(self.proc)
            tmp_colony_whole = p.map(self.simulator, tmp_colony_whole)
            p.close()
            
            #全コロニーを用いてself.archiveを更新
            #   Qが計算されたものが帰ってくる
            tmp_colony_whole = self.arc.update_archive_from_colony(tmp_colony_whole)
            
            #コロニーの連結を解除
            #   オペレータ適用前、適用後で分ける
            #   追従蜂の数でぴったり割り切れるはず
            colonies = [tmp_colony_whole[x: (x + self.M_onlooker)] for x in range(int(len(tmp_colony_whole) / self.M_onlooker))]
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
            
            #偵察蜂のフェーズ
            sys.stderr.write("%d th scout phase...\n" % i)
            #   LIMITに達した収穫蜂をジェネレータを使って最初期化
            self.gen.calculate_weights()
            for bee in colony_employed:
                if bee['t'] >= self.LIMIT:
                    bee['sol'] = self.gen.generate_bee_sol()
                    bee['fit'] = {'count': None, 'item': None}
                    bee['Q'] = np.nan
                    bee['t'] = 0
            
            
            #収穫蜂と追従蜂からもっともQが高い蜂を選び、世代の最適解としてフェロモンを更新
            sys.stderr.write("%d th pheromone updating phase...\n" % i)
            colony_all = colony_employed + colony_onlooker
            idx_gbest_bee = np.nanargmax([bee['Q'] for bee in colony_all])
            gbest_bee = colony_all[idx_gbest_bee]
            self.gen.update_pheromone(gbest_bee)
            
            #現在のアーカイブを保存する
            self.archives.append(self.arc.get_archive())

    #fin
    #   self.archiveにいる蜂を出力して終わり
    def save_result(self, out_dirname):
        #archiveを取ってくる
        self.archived_bee = self.arc.get_archive()
        
        #出力データの生成
        columns = ['fit_count', 'fit_item', 'reducer', 'booster']
        data = [\
            [bee['fit']['count'], bee['fit']['item'], bee['sol']['booster'], bee['sol']['reducer']]\
            for bee in self.archived_bee\
        ]
        data_df = pd.DataFrame(data, columns=columns)
        
        #CSVに出力
        data_df.to_csv('%s/summary.csv' % out_dirname)
        
        #散布図の生成
        #   snsで生成したあとに、各データ番号のラベルをつける
        plot = sns.lmplot('fit_item', 'fit_count', data_df, fit_reg=False)
        for idx in data_df.index:
            plot.ax.text(\
                data_df.loc[idx, 'fit_item'], data_df.loc[idx, 'fit_count'], '%s' % idx\
            )
        plot.ax.ticklabel_format(style='sci',axis='both', scilimits=(1e4,-1e4))
        plot.ax.yaxis.set_major_formatter(ptick.ScalarFormatter(useMathText=True))
        plot.ax.xaxis.set_major_formatter(ptick.ScalarFormatter(useMathText=True))
            
        #散布図の出力
        plt.savefig('%s/pareto_front.png' % out_dirname, dpi=600)

if __name__ == '__main__':
    #引数の処理
    infile_prob_table = sys.argv[1]
    input_proc = sys.argv[2]
    input_price_grind = sys.argv[3]
    out_dirname = sys.argv[4]
    
    #最適化の実行
    op = MOABC(infile_prob_table, int(input_price_grind))
    op.proc = int(input_proc)
    op.learn()
    op.save_result(out_dirname)
    
