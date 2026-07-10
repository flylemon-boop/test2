#!/usr/bin/env python3
import argparse

from capx.serving.launch_pyroki_server import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8116)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--robot", default="panda_description")
    parser.add_argument("--target-link", default="panda_hand")
    args = parser.parse_args()
    main(port=args.port, host=args.host, robot=args.robot, target_link=args.target_link)
