# 政策库抓取系统 - 改造总结与使用指南（v1）

## 概览
- 将脚本式抓取重构为模块化工程，分层为：Scheduler / Fetcher / Parser / Pipeline / Storage / Monitor。
- 列表与详情任务解耦，支持独立调度；实现幂等写入与增量抓取。
- 落盘原始数据（Raw HTML、附件），便于回溯与二次解析。
- 增加重试/退避、403/429 降速、正文长度阈值等稳定性与质量控制。

## 目录结构
```
crawler/
  config.py                  # 常量、限速、重试、阈值、路径、DB
  fetcher.py                 # 请求层：Session、重试/退避、状态码处理
  parser/
    list_parser.py           # 列表 JSON 解析
    detail_parser.py         # 详情 HTML 解析（候选容器+最长文本；附件识别）
  pipeline.py                # 预留数据清洗/合并（当前直通）
  storage/
    sqlite_store.py          # SQLite 建表、UPSERT、状态更新、任务提取
    file_store.py            # Raw HTML 落盘、SHA256、附件下载
  tasks/
    list_task.py             # 抓列表→解析→写 policy_list（置 PENDING_DETAIL）
    detail_task.py           # 消费 PENDING_DETAIL→抓详情→落盘→解析→附件→写 policy_detail→状态流转
  monitor.py                 # 日志/简易计数器（可扩展报表）
  main.py                    # 统一命令入口（list/detail）

gov_policies/
  raw_html/YYYY/MM/*.html    # 原始详情 HTML（按年月分层）
  attachments/*              # 附件（基于标题提示+url hash 命名）
  details/*                  # 可选：结构化详情（历史脚本产物，保留兼容）

data/
  crawler.db                 # SQLite 数据库
```

## 数据模型（SQLite）
- `policy_list(id TEXT PRIMARY KEY, url, pubtime, title, status, retry, puborg, pcode, summary, created_at, updated_at)`
  - 幂等 UPSERT；`DONE/FAILED` 状态不回退；新增时默认 `PENDING_DETAIL`。
- `policy_detail(id TEXT PRIMARY KEY, content, attachments_json, parser_version, raw_html_path, raw_html_sha256, source_url, fetched_at, parsed_at)`
  - 每条详情具备可追溯元数据与解析版本。

## 运行方式
- 列表任务（写入 `policy_list`，状态为 `PENDING_DETAIL`）

```bash
python -m crawler.tasks.list_task --keyword 管理条例 --max-pages 2 --page-size 50
# 或统一入口
python -m crawler.main list --keyword 管理条例 --max-pages 2 --page-size 50
```

- 详情任务（消费 `PENDING_DETAIL`，保存 Raw HTML、正文与附件至库与文件系统）

```bash
python -m crawler.tasks.detail_task --limit 50 --max-retry 5
# 或统一入口
python -m crawler.main detail --limit 50 --max-retry 5
```

## 配置与环境变量
- 关键配置位于 `crawler/config.py`：
  - 重试：`RETRY_MAX=3`，退避：指数退避+抖动
  - 限速：列表 `0.8s/次`；详情 `random.uniform(1.0, 2.5)`；每 20 次额外 `sleep 5s`
  - 质量阈值：`MIN_CONTENT_LENGTH=200`
  - 路径：`data/crawler.db`、`gov_policies/raw_html`、`gov_policies/attachments`
- 若站点需要有效 Cookie（如 `tfstk`）：

```bash
export CRAWLER_TFSTK="你的_tfstk"
```

## 幂等与增量
- 唯一键优先使用接口返回的 `id`，退化为 `index` 或 `url`。
- 列表入库采用 UPSERT；已处于 `DONE/FAILED` 的记录不会被回退覆盖。
- 详情任务按 `PENDING_DETAIL` 消费，失败 `retry+1`；超限留待人工或后续策略处理。

## 稳定性与质量控制
- 网络重试：超时/5xx/连接失败自动重试与退避。
- 状态码处理：403/429 增加等待，降低访问节奏。
- 质量阈值：正文长度 < 200 视为解析失败，回退到重试。
- 原始数据落盘：每条详情保存 Raw HTML 与 SHA256，支持回放与二次解析。

## 后续演进建议
- 调度：接入 `apscheduler` 或 `cron` 定时跑“列表/详情”两条任务。
- 监控：收集成功率、失败率、空正文比例、耗时，阈值报警（飞书/钉钉）。
- 规模化：迁移至 Scrapy/Redis（内置队列、去重、重试、限速更完善）。

---
如需示例定时任务、质量报表模板或迁移到 Scrapy 的脚手架，可在此基础上继续补充。 


