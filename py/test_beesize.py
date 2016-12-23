import optimizer
import itertools
import pandas as pd


nbees = [20, 40, 80]

data = []
for nbee in itertools.product(nbees, nbees):
    size_archive = []
    for i in range(4):
        ex = optimizer.MOABC('./data/weapon_13.csv', 192000)
        ex.proc = 6
        ex.N = 1
        ex.M_employed = nbee[0]
        ex.M_onlooker = nbee[1]
        ex.learn()
        print(len(ex.archives[0]))
        size_archive.append(len(ex.arc._archive))
    
    data.append([nbee[0], nbee[1], sum(size_archive) * 1.0 / len(size_archive)])
    print(data)

data_df = pd.DataFrame(data, columns=['employed', 'onlooker', 'archive size'])
data_df.to_csv('test_bee.csv')
