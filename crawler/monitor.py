import logging
from dataclasses import dataclass


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@dataclass
class Counters:
    success: int = 0
    failed: int = 0
    empty_content: int = 0

    def report(self) -> str:
        total = self.success + self.failed
        empty_rate = (
            f"{(self.empty_content / total * 100):.2f}%" if total > 0 else "0.00%"
        )
        return (
            f"成功: {self.success}, 失败: {self.failed}, 空正文: {self.empty_content} "
            f"(空正文率: {empty_rate})"
        )


