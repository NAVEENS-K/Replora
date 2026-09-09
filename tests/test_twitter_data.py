from pathlib import Path

from replora.twitter_data import reconstruct_pairs, frequent_brand_authors


def test_reconstruct_direct_customer_reply(tmp_path: Path):
    csv = tmp_path / "twcs.csv"
    csv.write_text(
        "tweet_id,author_id,inbound,created_at,text,response_tweet_id,in_response_to_tweet_id\n"
        "1,customer,true,2020-01-01T00:00:00Z,Need help,,\n"
        "2,brand,false,2020-01-01T00:01:00Z,Happy to help,,1\n"
        "3,other,false,2020-01-01T00:02:00Z,Noise,,1\n",
        encoding="utf-8",
    )
    pairs = reconstruct_pairs(csv, "brand")
    assert len(pairs) == 1
    assert pairs[0].customer_tweet.tweet_id == "1"
    assert pairs[0].brand_reply.tweet_id == "2"


def test_frequent_brand_authors(tmp_path: Path):
    csv = tmp_path / "twcs.csv"
    csv.write_text(
        "tweet_id,author_id,inbound,created_at,text,response_tweet_id,in_response_to_tweet_id\n"
        "1,brand,false,1,a,,\n"
        "2,brand,false,2,b,,\n"
        "3,cust,true,3,c,,\n",
        encoding="utf-8",
    )
    assert frequent_brand_authors(csv)[0] == ("brand", 2)
