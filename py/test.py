a= dodo.Grind("./data/weapon_13.csv")
a.set_skip("None")
a.set_reducers(['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None'])
a.set_boosters(['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None'])


in_names_item = {
    "reducer": ["None", "+1", "+2"], 
    "booster": ["None", "+5%", "+10%", "+20%"]
}

best_bee = {
    "sol": {
        "booster": ['None', 'None', 'None', '+10%', 'None', 'None', 'None', '+10%', 'None', '+10%'], 
        "reducer": ['None', 'None', 'None', 'None', 'None', '+1', '+2', '+2', '+1', 'None']
    }
}