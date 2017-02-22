import sys
import argparse
import time

sys.path.append('./bin/moabc')
import optimizer


#引数の処理
#parserの初期化
parser = argparse.ArgumentParser(description='This script optimizes bayesian network graph structure by MOABC')

#強化成功率表
parser.add_argument("infile_pt", type=str)

#一回の強化費用
parser.add_argument("-pg","--pricegrind", type=int)

#強化シミュレータの実行回数
parser.add_argument("-na","--num_average", type=int, default=100)

#結果の出力先
#   最後のスラッシュいらない
#   OK: test, ./test
#   NG: test/, ./test/
parser.add_argument("out_dir", type=str)

#学習中の結果の保存
group_sp = parser.add_mutually_exclusive_group()
group_sp.add_argument('-sp', '--saveprogress', action='store_true')
group_sp.add_argument('-n-sp', '--no-saveprogress', action='store_false')
parser.set_defaults(saveprogress=False)


#並列化のプロセス数
parser.add_argument("-np","--num_proc", type=str, default=1)

#画像出力の有無
#   sshログインとかだと無理なので、Falseを入れる
group_wi = parser.add_mutually_exclusive_group()
group_wi.add_argument('-wi', '--withimage', action='store_true')
group_wi.add_argument('-n-wi', '--no-with_image', action='store_false')
parser.set_defaults(withimage=True)

#蜂の数
parser.add_argument('-me', '--m_employed', type=int, help='収穫蜂の数', default=40)
parser.add_argument('-mo', '--m_onlooker',type=int, help='追従蜂の数', default=40)
parser.add_argument('-li', '--limit',type=int, help='偵察蜂の閾値', default=3)

#ループ数
parser.add_argument('-n', type=int, help='ループ数', default=50)

#ALPHA
parser.add_argument('-a', '--alpha', type=float, help='ALPHAの値', default=1)

#変数のparse
#   下のやり方でdictになるっぽい
args = vars(parser.parse_args())
print("parsed argments from argparse\n%s\n" % str(args))

#出力先ディレクトリ
out_dir = args['out_dir']

#実行中の結果保存
save_progress = args['saveprogress']

#インスタンスの作成
infile_pt = args['infile_pt']
input_price_grind = args['pricegrind']
op = optimizer.MOABC(infile_pt, input_price_grind)

#ハイパーパラメータの設定
op.M_employed = args['m_employed']
op.M_onlooker = args['m_onlooker']
op.LIMIT = args['limit']
op.N = args['n']
op.weight_h = args['alpha']
op.proc = args['num_proc']
op.num_average = args['num_average']

#パラメータを適用
op.gen.calculate_weights()

#学習の処理
dir_save_progress = ''
if save_progress:
    dir_save_progress = out_dir
start = time.time()
op.learn(out_dirname=dir_save_progress)
end = time.time()

#経過時間の出力
str_time = "time: ", "{0}".format(end - start)
print(str_time)
f = open('%s/time.log' % out_dir, 'w')
f.writelines(str_time)
f.close()

#学習結果の出力
op.save_result(out_dir, prefix='total', with_image=args['withimage'])