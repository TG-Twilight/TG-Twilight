# 项目记忆

最后整理：2026-10-17。日常维护规则见 [AGENTS.md](AGENTS.md)。以下仓库事实在此次交接时根据本地文件核实，后续以实际代码和用户最新指示为准。

## 用户偏好与交接

- 使用新加坡华文、简体字交流，表达自然，技术内容讲清楚，不硬塞 Singlish。
- 2026-10-17：用户决定后续由 Codex 持续维护本项目，要求在项目根目录使用规范化的 `AGENTS.md` 和 `MEMORY.md`。
- 已将 Claude 的语言偏好记忆整合进这两个文件；原始文件保留，未移动或删除。
- 原始来源：`~/.claude/projects/D--Project-Claude-TG-Twilight/memory/MEMORY.md` 和同目录的 `reply-in-singapore-chinese.md`，记录于 2026-09-23。该目录当时只有这条偏好，没有技术交接记忆。
- 同一 Claude 项目目录下另有历史会话 JSONL；此次未阅读或迁入，不能据此推断过去的维护决策。

## 项目与视觉

- 本仓库为 `TG-Twilight/TG-Twilight` 的 GitHub Profile README，展示名为 Simon Twilight。
- 页面主题为落日与赛博牛仔；主要资源在仓库内自托管。
- `assets/banner.svg` 与 `tools/make_cards.py` 共用落日配色：背景 `#1B1123`、正文 `#F3D9C4`、金色 `#FFD166`、橙色 `#FF8C42`、珊瑚红 `#FF5F6D`。
- 招牌项目为 `AWAvenue-Ads-Rule`；其他项目由卡片生成脚本中的 `PINS` 列表配置，页面分组与说明维护在 README。
- 2026-10-17：项目区加入 `c001apk`、`AC130.Zombie.Gunship`，普通卡片按「应用与实用工具」「Web 工具与服务」「游戏与折腾」分为 4 / 4 / 2 张，保留招牌全宽卡和落日风格。
- `c001apk` 为接续维护的 Flutter 非官方酷安客户端，目前重点维护 Android / Windows；Kotlin / Compose 迁移尚属计划，写简介时勿当作已完成。`AC130.Zombie.Gunship` 是 AC130Beta 本地游戏的 Cheat Engine 修改表。
- README 还使用 shields.io 徽章、count.getloli.com 访问计数器和用户自有的 r6.awads.cc 图标服务。

## 资源生成

以下命令为已有脚本的完整生成入口，运行前注意联网请求及覆盖范围。

| 脚本 | 运行方式与依赖 | 输入与输出 |
| --- | --- | --- |
| [make_cards.py](tools/make_cards.py) | `python tools/make_cards.py`；仅 Python 标准库，需要联网 | GitHub 数据 → `assets/stats-strip.svg`、`assets/feature-*.svg`、`assets/pin-*.svg` |
| [make_banner_name.py](tools/make_banner_name.py) | `python tools/make_banner_name.py`；依赖 `fonttools`、`uharfbuzz`，需要联网取字体 | Yellowtail 字体与脚本中的名字配置 → 改写 `assets/banner.svg` 的名字路径、裁剪框及光标 |
| [make_cos_assets.py](tools/make_cos_assets.py) | `python tools/make_cos_assets.py`；依赖 `Pillow`，头像需要联网 | 本地主图 JPG、在线角色立绘 → `Alastor.Cos/` 中三个 WebP |

- 卡片脚本默认用户为 `TG-Twilight`，支持 `GH_USER`；认证取 `GITHUB_TOKEN` 或 `GH_TOKEN`。API 调用失败或项目数据不完整时会拒绝覆盖卡片。
- 仅新增卡片时，可用公开仓库 API 的真实数据调用现有 `pin_card()`，只写对应 SVG，避免顺带刷新全部统计；同时更新 `PINS`，供后续自动任务继续维护。
- Cos 主图当前输入为本地 `Alastor.Cos/photo_1_2026-08-24_22-25-24.jpg`；该 JPG 受 `.gitignore` 忽略，不能假设新克隆中存在。
- 横幅以字形路径显示手写名字，避免依赖访问者字体或 SVG 中的外部字体加载。

## 自动更新

- [stats.yml](.github/workflows/stats.yml)：每天 UTC 20:23（UTC+8 次日 04:23）生成统计及项目卡片并提交；支持手动触发，修改该工作流或 `tools/make_cards.py` 的 push 也会触发。CI 使用 Python 3.12。
- [snake.yml](.github/workflows/snake.yml)：每周日 UTC 19:17（UTC+8 周一 03:17）使用 `Platane/snk` 更新贡献蛇并提交，也支持手动触发。
- 这些流程会自动提交生成产物；维护时留意远端可能出现的自动更新。

## 当前交接状态

- 已更新 README 项目分组与「在做」简介，新增两张项目 SVG，并同步 `tools/make_cards.py` 的 `PINS`；没有修改工作流。
- 接手时发现未跟踪的 `.claude/`，其中为 `settings.local.json`；它是既有本机设置，此次未改动或迁入文档。
- 本次页面调整沿用现有生成器，仅生成新增卡片，没有运行完整统计刷新。
