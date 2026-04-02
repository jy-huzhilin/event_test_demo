import argparse
import json

import redis


def parse_args():
    parser = argparse.ArgumentParser(description="Publish one ETL ready event for event_future_1min_demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6379)
    parser.add_argument("--db", type=int, default=0)
    parser.add_argument("--channel", default="ETL")
    parser.add_argument("--table", default="cbond.future_hf_1min")
    parser.add_argument("--business-time", required=True)
    parser.add_argument("--count", type=int, default=131)
    return parser.parse_args()


def main():
    args = parse_args()
    client = redis.Redis(host=args.host, port=args.port, db=args.db, decode_responses=True)
    payload = {
        "table": args.table,
        "value": args.business_time,
        "count": args.count,
    }
    receivers = client.publish(args.channel, json.dumps(payload, ensure_ascii=False))
    print(f"published to {args.channel}: receivers={receivers}")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
