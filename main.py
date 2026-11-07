"""统一应用入口：python main.py [web|agent]。"""
import argparse
import config  # 统一加载根目录配置


def main():
    parser = argparse.ArgumentParser(description='Fermata — 通用 Agent')
    parser.add_argument('mode', nargs='?', choices=['web', 'agent'], default='web')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8018)
    args = parser.parse_args()
    if args.mode == 'web':
        import uvicorn
        uvicorn.run('web.app:app', host=args.host, port=args.port)
    else:
        from agent.runtime import run
        try:
            run()
        except NotImplementedError as exc:
            parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
