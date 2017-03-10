# pso2_grind_optimizer
PSO2(Phantasy Star Online 2(C))の旧式武器及びユニットの強化の際の補助アイテムの使用タイミングを最適化する試み

# 概要
旧式武器、及びユニットのアイテム強化時にトレードオフな問題となる
- 目的1: 強化回数の最小化(fit_count)
- 目的2: 使用する強化剤の最小化(fit_item)

を多目的最適化問題としてSPEAIIと人口蜂コロニーベースをベースとしたアルゴリズムで最適化を行います。

下の図は本プログラムによって最適化された解を目的1,2の平面にプロットした図です。
この図において例えば、次のようなことが言えます

| 解の番号（おおよその位置） | 強化回数     | 強化剤の消費 |
|----------------------------|--------------|--------------|
| 9(図左上)                  | 多数         | とても少ない |
| 1(図右下)                  | とても少ない | 大量         |
| 15(図左下)                 | まあまあ     | まあまあ     |

![解の出力例](https://raw.githubusercontent.com/wiki/curiburn/pso2_grind_optimizer/images/example/pareto_front.png  "解の出力例")

## 必要なもの
本プログラムはPython3で書かれています。使用しているPythonのライブラリは以下のとおりです。

- numpy
- pandas
- matplotlib
- seaborn
- sklearn
- progressbar2

## 使い方
###main.pyを使った方法
```bash
mkdir result
python3 py/main.py data/weapon_13.csv result -pg 192000 -np 6
```

###ipython等でインポートして使う方法
```python
#インポート
#import sys
#sys.append('py')
import optimizer

#インスタンスの作成
#	第1引数: 強化成功率テーブル
#	第2引数: 一回の強化に必要なメセタ
op = optimizer.MOABC('data/weapon_13.csv', 192000)

#並列化のスレッド数の設定
#	このプログラムはとっても重いので、並列化ができるならおすすめ
#	実行するマシンのCPUのコア数なりスレッド数と合わせる
op.proc = 6	#6スレッドで並列
#学習の実行
op.learn()

#結果の保存
#	引数には出力先のディレクトリを指定
#	事前にディレクトリを作っておかないと結果は書き込まれない
op.save_result('./test_result')	#test_resultというディレクトリに保存
```