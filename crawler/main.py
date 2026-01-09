import argparse
import sys

from .monitor import setup_logging
from .tasks.list_task import run as run_list
from .tasks.detail_task import run as run_detail


def main(argv=None):
    setup_logging()
    parser = argparse.ArgumentParser(description="政策库抓取系统")
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_p = sub.add_parser("list", help="抓取列表并入库")
    list_p.add_argument("--keyword", required=True, help="搜索关键字")
    list_p.add_argument("--max-pages", type=int, default=2, help="最大页数")
    list_p.add_argument("--page-size", type=int, default=50, help="每页数量")

    detail_p = sub.add_parser("detail", help="处理详情任务")
    detail_p.add_argument("--limit", type=int, default=50, help="每批次处理条数")
    detail_p.add_argument("--max-retry", type=int, default=5, help="最大重试次数")

    args = parser.parse_args(argv)
    if args.cmd == "list":
        run_list(keyword=args.keyword, max_pages=args.max_pages, page_size=args.page_size)
    elif args.cmd == "detail":
        run_detail(limit=args.limit, max_retry=args.max_retry)


if __name__ == "__main__":
    main(sys.argv[1:])


