# RelayWatch 检测脚本 v0 / RelayWatch detection scripts v0

> v0.1.0

## 中文

用于检测 Claude API 中转站是否「掺水」的开源脚本。**在你自己的电脑上、用你自己的 key 运行**；脚本不收集、不上传、不保存 key，没有任何遥测。只依赖 Python 3 标准库。

**花费提示**：每次运行会在你的账户上消耗少量 token。必须显式设置 `RELAY_CONFIRM_SPEND=yes` 才会发出请求。

```bash
export RELAY_BASE_URL=https://<中转站地址>   # 你自己填写
export RELAY_API_KEY=<你的 key>               # 只从环境变量读取
export RELAY_CONFIRM_SPEND=yes
python3 run_all.py            # 生成 result.json 并自动校验
python3 validate_result.py result.json
```

| 脚本 | 检测内容 |
|---|---|
| check_signature.py | extended thinking 的 signature 是否存在且格式合理；可选用你自己的官方 key（`OFFICIAL_ANTHROPIC_KEY`）回放到 api.anthropic.com 验证 |
| check_format.py | msg_/toolu_ 前缀、model 字段、usage 字段、SSE 事件顺序 |
| check_billing.py | input token 偏差（需 `EXPECTED_INPUT_TOKENS`）、Prompt Cache 是否命中 |
| daily_prompts.py | 本地随机生成的算术链和 needle-in-haystack 题 |
| check_speed_repeat.py | tokens/s、首 token 时间、temperature=1 下两次输出是否相同 |

可选环境变量：`RELAY_MODEL`、`EXPECTED_INPUT_TOKENS`、`RELAY_MIN_TPS`/`RELAY_MAX_TPS`（默认区间未校准，请先在官方 API 实测）。

**结果解读**：单次结果只是「某日某样本的观察」，不是对任何服务方的定性。签名格式检查是启发式的；速度区间与签名长度阈值是未校准的假设。

**测试**（不调用任何真实 API，使用本地 mock 服务器）：`python3 -m unittest discover -s tests -v`

## English

Open-source scripts to check whether a Claude API relay is serving what it claims. **Run them locally with your own key.** The scripts never collect, upload or store keys and contain no telemetry. Python 3 standard library only.

**Cost**: each run spends a few tokens on your own account. Requests are only sent when `RELAY_CONFIRM_SPEND=yes` is set.

Usage is shown above. Checks: thinking-signature presence/format (optional replay to the official API with your own `OFFICIAL_ANTHROPIC_KEY`), protocol fingerprint (id prefixes, model echo, usage fields, SSE order), token/cache billing, locally randomized capability prompts, and speed/repeat checks.

**Interpretation**: a single result is a dated observation of one sample, not a verdict on any provider. The signature-format check is heuristic; the speed range and signature-length threshold are uncalibrated assumptions.

**Tests** (no real API calls; local mock server): `python3 -m unittest discover -s tests -v`

## Why / What / How to use / Neutrality & disclosure / Right of reply

### Why

Third-party Claude API relays (中转站) sit between you and Anthropic. Users often can’t tell whether a relay is serving the claimed model, billing usage/cache honestly, or swapping in a cheaper path. Public vendor lists are large; independent, dated evidence is scarce. RelayWatch exists to make checks **reproducible and open**, not to sell tokens or rank affiliates.

### What

- **Site:** [https://relay-watch.com](https://relay-watch.com) — methodology, real-cost calculator, scam/outage-style archive (dated + sourced; **0 named relay entries** live as of launch), submit flow, right of reply.  
- **Scripts (this repo):** MIT, Python 3 stdlib only. Checks: thinking-signature, protocol/SSE format, usage & Prompt Cache billing, randomized daily prompts, speed/repeat. Launched publicly **2026-10-19**; site **2026-10-21**.  
- Named relay pages appear only after our own reproducible tests with raw output and human review (“On &lt;date&gt; we measured…”), or ≥3 independent submissions.

### How to use

```bash
export RELAY_BASE_URL=https://<your-relay>
export RELAY_API_KEY=<your key>          # env only — never paste into Issues
export RELAY_CONFIRM_SPEND=yes           # required; default is no network spend
python3 run_all.py
python3 validate_result.py result.json
```

Optional: `OFFICIAL_ANTHROPIC_KEY` (signature replay), `EXPECTED_INPUT_TOKENS`, `RELAY_MIN_TPS` / `RELAY_MAX_TPS`. Local mock tests: `python3 -m unittest discover -s tests -v` (no real API calls).

A single `result.json` is a **dated observation of one sample**, not a verdict on any provider.

### Neutrality & disclosure

- No affiliate, referral, or paid placement links — ever.  
- We do not sell tokens, resell API access, or recommend relays.  
- We do not collect or store API keys; submissions are results only.

**Disclosure (English):**  
The same owner is preparing a Claude Code relay resale pilot (not live, not charging); this site does not review or recommend it.

**披露（中文，与 /about/ 原句一致）：**  
同一所有者在筹备一个 Claude Code 中转转售试点（尚未上线、未收费），本站不为它做评测或推荐。

### Right of reply

Operators (or anyone) can request correction, clarification, or takedown via the GitHub issue template:  
https://github.com/relaywatch-cn/relaywatch-scripts/issues/new?template=right-of-reply.yml  
Also linked from https://relay-watch.com/reply/ . We aim to review within 72 hours; responses are shown alongside the record when published.

---

## 中文

### 为什么

第三方 Claude API 中转站介于用户与 Anthropic 之间。用户往往难以判断中转是否按声称的模型服务、usage/缓存是否如实计费、是否换了更便宜的线路。公开榜单很多，带日期、可复现的独立证据很少。RelayWatch（中转鉴）要做的是**可复现、开源的检测**，不是卖 token，也不靠返佣排名。

### 做什么

- **站点：** https://relay-watch.com — 检测方法、真实成本计算器、跑路/停服类档案（带日期与来源；**上线时 0 条点名中转站条目**）、提交入口、站方回应。  
- **本仓库脚本：** MIT，仅 Python 3 标准库。检测：thinking 签名、协议/SSE 格式、usage 与 Prompt Cache 计费、每日随机能力题、速度/重复。仓库公开 **2026-10-19**；站点 **2026-10-21**。  
- 点名某家中转站须有我们自己的可复现测试（含原始输出）并经人工审核（措辞：「某日我们测得…」），或 ≥3 份独立提交。

### 怎么用

见上方 bash 示例。默认零花费；只有设置 `RELAY_CONFIRM_SPEND=yes` 才会发真实请求。**绝不把 API key 贴进 Issue 或站点。** 单次结果只是「某日某样本的观察」，不是对站方的定性。

### 中立与披露

- 永不接受返佣、推广或付费排名。  
- 不卖 token、不转售、不推荐任何中转站。  
- 不收集、不存储 API key；提交只收结果。

**披露原句：** 同一所有者在筹备一个 Claude Code 中转转售试点（尚未上线、未收费），本站不为它做评测或推荐。

### 站方回应

https://github.com/relaywatch-cn/relaywatch-scripts/issues/new?template=right-of-reply.yml  
或站点 https://relay-watch.com/reply/ 。目标 72 小时内复核。

---

## 致谢 / Credits
方法思路参考了社区工具 [veridrop](https://github.com/canarybyte/veridrop)（AGPL-3.0）和 RelayScope（GitHub 公开仓库，未声明开源许可）；未复制任何代码。

Method ideas were informed by the community tools [veridrop](https://github.com/canarybyte/veridrop) (AGPL-3.0) and RelayScope (public GitHub repository with no declared open-source license, so not linked). No code was copied.

## 提交结果 / Submitting results
可通过本仓库的 Issue 模板自愿提交 `result.json`（只含结果，绝不含 key 或 prompt）。Results may be voluntarily submitted via this repository's issue template (results only, never keys or prompts).

License: MIT (see LICENSE).
