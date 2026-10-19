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

## 致谢 / Credits
方法思路参考了社区工具 [veridrop](https://github.com/canarybyte/veridrop)（AGPL-3.0）和 RelayScope（GitHub 公开仓库，未声明开源许可）；未复制任何代码。

Method ideas were informed by the community tools [veridrop](https://github.com/canarybyte/veridrop) (AGPL-3.0) and RelayScope (public GitHub repository with no declared open-source license, so not linked). No code was copied.

## 提交结果 / Submitting results
可通过本仓库的 Issue 模板自愿提交 `result.json`（只含结果，绝不含 key 或 prompt）。Results may be voluntarily submitted via this repository's issue template (results only, never keys or prompts).

License: MIT (see LICENSE).
