from clauseledger.evaluation import benchmark

def test_benchmark():
    result=benchmark()
    assert result['queries']==3
    assert result['mean_reciprocal_rank_at_5']>0
