def fit_count(results, price_grind, price_grinder=0):
    num_grinds = [x["count_grind"] for x in results]
    num_grind = sum(num_grinds) * 1.0 / len(num_grinds)
    
    score = (price_grind + price_grinder) * num_grind
    return score
    