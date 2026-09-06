"""生成演示事件（命令行入口）。

首次打开工作台时运行一次，即可在「案例总览 → 调查工作区」看到完整的
流行曲线、三间分布、四格表、证据与审计日志，便于演示与上手。

用法：  uv run python scripts/seed_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.store import Store
from server.config import STORE_PATH
from server.seed import EVENT_ID, seed_demo_event


def main():
    store = Store(STORE_PATH)
    ev = seed_demo_event(store)
    if ev is None:
        print(f"事件 {EVENT_ID} 已存在，跳过。如需重建请先删除 {STORE_PATH}")
    else:
        print("已生成演示事件：")
        print(f"  {ev['id']} · {ev['title']} · 修订 {ev['revision']}")
        print("打开前端「案例总览」即可进入工作区查看可视化。")
    store.close()


if __name__ == "__main__":
    main()
