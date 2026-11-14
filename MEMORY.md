# 项目记忆

最后整理：2026-11-15。日常维护规则见 [AGENTS.md](AGENTS.md)。以下仓库事实在此次交接时根据本地文件核实，后续以实际代码和用户最新指示为准。

## 用户偏好与交接

- 使用新加坡华文、简体字交流，表达自然，技术内容讲清楚，不硬塞 Singlish。
- 2026-11-15：用户指出此前的项目说明「AI 味」太重。页面文案要像本人随手写的：平实、具体，不用排比句式、口号和夸张说法。用户点名「招牌项目」这种叫法就很 AI 味，页面和卡片上不要再用「招牌」「flagship」。
- 2026-11-15：Pixiv 上的名字写 `Twilight`，不要写成 `Simon Twilight`（用户原话针对 `~/graffiti`，终端卡里的 Pixiv 一项也已同步）。
- 2026-10-17：用户决定后续由 Codex 持续维护本项目，要求在项目根目录使用规范化的 `AGENTS.md` 和 `MEMORY.md`。
- 已将 Claude 的语言偏好记忆整合进这两个文件；原始文件保留，未移动或删除。
- 原始来源：`~/.claude/projects/D--Project-Claude-TG-Twilight/memory/MEMORY.md` 和同目录的 `reply-in-singapore-chinese.md`，记录于 2026-09-23。该目录当时只有这条偏好，没有技术交接记忆。
- 同一 Claude 项目目录下另有历史会话 JSONL；此次未阅读或迁入，不能据此推断过去的维护决策。

## 项目与视觉

- 本仓库为 `TG-Twilight/TG-Twilight` 的 GitHub Profile README，展示名为 Simon Twilight。
- 页面主题为落日与赛博牛仔；主要资源在仓库内自托管。
- 2026-11-15：用户对旧版页面不满意，喜欢 `hu553in/ascii-profile-card` 与 `ignaciochiappero` 主页的终端 / ASCII 风格，并指定把贡献蛇换成后者那种「吃豆人 + Claude 小精灵」。页面据此改为「落日终端」风格：页首 neofetch 终端卡（程序生成的 ASCII 落日 + 个人信息 + GitHub 数字 + 语言比例）、六个像素链接按钮、吃豆人贡献图，其后是项目、Graffiti、Cosplay。
- 参考仓库 `ignaciochiappero/ignaciochiappero` 没有开源许可，这里只借鉴思路，脚本和像素图均为重新编写；继续维护时不要直接复制其代码。
- 落日配色集中在 `tools/sunset.py`：背景 `#1B1123`、正文 `#F3D9C4`、金色 `#FFD166`、橙色 `#FF8C42`、珊瑚红 `#FF5F6D`、紫色 `#7B4B94`。Claude 小精灵使用角色自身的 `#D97757`。
- 页面只保留一套深色卡片，没有按浅色 / 深色模式分别出图。
- 此次移除：手写名字横幅（`assets/banner.svg`、`tools/make_banner_name.py`）、统计长条（数字和语言比例并入终端卡，逐年贡献柱不再展示）、`Platane/snk` 贡献蛇及其工作流、README 中的 shields.io 徽章。需要时可从 Git 历史（`40eccce` 及之前）取回。
- R6 cos 图由 `profile-contrib-snake/jager,solis.webp` 移到 `R6.Cos/jager-solis.webp`。
- 主项目为 `AWAvenue-Ads-Rule`（全宽横幅卡，README 小节标题直接写「秋风广告规则」）；其他项目由 `tools/make_cards.py` 的 `GROUPS` 配置（`apps` / `web` / `games`，各有强调色，目录名印在卡片上），说明文字维护在 README。
- 2026-11-15 第二轮调整：`~/projects` 改为「左卡片、右说明」的逐行列表，仓库卡加上分组路径和最近推送月份；`~/graffiti` 改为作品卡；`~/cosplay` 的对话改为内嵌头像的聊天卡，Hazbin 一组为照片与对话左右并排。
- 2026-10-17：项目区加入 `c001apk`、`AC130.Zombie.Gunship`，普通卡片按「应用与实用工具」「Web 工具与服务」「游戏与折腾」分为 4 / 4 / 2 张，保留主项目全宽卡和落日风格。
- `c001apk` 为接续维护的 Flutter 非官方酷安客户端，目前重点维护 Android / Windows；Kotlin / Compose 迁移尚属计划，写简介时勿当作已完成。`AC130.Zombie.Gunship` 是 AC130Beta 本地游戏的 Cheat Engine 修改表。
- README 仍使用的外部服务只有 count.getloli.com 访问计数器；r6.awads.cc 的图标已在生成时内嵌进 `assets/cos-r6.svg`，页面展示时不再请求它。
- Pixiv 不允许未登录的程序读取作品页（网页 403；带伪装请求头的抓取已被本机权限策略拒绝，不要再试）。2026-11-15 用户提供了浏览器里 Playwright MCP 扩展的令牌，授权用其登录态查看作品信息；令牌不写入仓库，下次需要时再向用户要。当时核实的作品共四件：`150784396`「Dear？」(2026-10-12)、`146949017`「Keep Smile！My Dear！」(2026-07-07)、`146948848`「Hey! My Dear?」(2026-07-07)、`119393336`「Judgement - HellTaker」(2024-06-06，未登录时不在公开列表里)。
- `raw.githubusercontent.com` 在用户所在线路（香港节点）偶发 `503 Backend.max_conn reached`，表现为个别图片随机裂图，刷新即可；2026-11-15 确认与仓库内容无关。若长期频繁出现，可考虑改走 jsDelivr 镜像。

## 资源生成

以下命令为已有脚本的完整生成入口，运行前注意联网请求及覆盖范围。

| 脚本 | 运行方式与依赖 | 输入与输出 |
| --- | --- | --- |
| [make_cards.py](tools/make_cards.py) | `python tools/make_cards.py`；仅 Python 标准库，需要联网。统一入口，一次取数后调用下面两个模块 | GitHub 数据 → `assets/hero.svg`、`assets/pacman.svg`、`assets/feature-*.svg`、`assets/pin-*.svg` |
| [make_hero.py](tools/make_hero.py) | 由 `make_cards.py` 调用，不单独运行 | `PROFILE` 文案 + 统计数据 → 页首终端卡；ASCII 落日由 `scene()` 程序绘制 |
| [make_pacman.py](tools/make_pacman.py) | 由 `make_cards.py` 调用；也可 `python tools/make_pacman.py` 单独重画，只读公开贡献日历页面，不占 API 额度 | 最近 53 周贡献 → `assets/pacman.svg` |
| [make_links.py](tools/make_links.py) | `python tools/make_links.py`；不联网 | `LINKS` 配置 → `assets/link-*.svg`（静态，不在定时任务内） |
| [make_graffiti.py](tools/make_graffiti.py) | `python tools/make_graffiti.py`；不联网 | `WORKS`（Pixiv id、标题、是否标 NEW）→ `assets/art-<id>.svg`（静态） |
| [make_dialogue.py](tools/make_dialogue.py) | `python tools/make_dialogue.py`；R6 头像需联网访问 r6.awads.cc | `SCENES` 台词 + 头像（base64 内嵌）→ `assets/cos-r6.svg`、`assets/cos-alastor.svg`（静态） |
| [make_cos_assets.py](tools/make_cos_assets.py) | `python tools/make_cos_assets.py`；依赖 `Pillow`，头像需要联网 | 本地主图 JPG、在线角色立绘 → `Alastor.Cos/` 中三个 WebP |

- 卡片脚本默认用户为 `TG-Twilight`，支持 `GH_USER`；认证取 `GITHUB_TOKEN` 或 `GH_TOKEN`。API 调用失败或项目数据不完整时会拒绝覆盖卡片。
- 仅新增卡片时，可用公开仓库 API 的真实数据调用现有 `pin_card()`，只写对应 SVG，避免顺带刷新全部统计；同时更新 `PINS`，供后续自动任务继续维护。
- Cos 主图当前输入为本地 `Alastor.Cos/photo_1_2026-08-24_22-25-24.jpg`；该 JPG 受 `.gitignore` 忽略，不能假设新克隆中存在。
- SVG 文字一律使用系统等宽字体，并以 `textLength` 按 0.6em 字宽固定每段宽度，避免不同系统的等宽字体造成错位；因此 SVG 里不放中文等全宽字符。
- 吃豆人贡献图的动画全部是 SMIL，共用同一总时长并从 0 开始以保持同步；`make_pacman.check()` 会校验 XML 与 `keyTimes`，不合法时生成会报错。追兵数量、间距和特长在 `CAST` 配置。
- 本机 Git 为 `core.autocrlf=true`；生成脚本写文件时固定用 LF，与 CI 产物一致。

## 自动更新

- [stats.yml](.github/workflows/stats.yml)：每天 UTC 20:23（UTC+8 次日 04:23）运行 `tools/make_cards.py`，生成终端卡、吃豆人贡献图及项目卡片并提交；支持手动触发，修改该工作流或 `make_cards.py` / `make_hero.py` / `make_pacman.py` / `sunset.py` 的 push 也会触发。CI 使用 Python 3.12。这是目前唯一的工作流。
- 这些流程会自动提交生成产物；维护时留意远端可能出现的自动更新。

## 当前交接状态

- 2026-11-15 第一轮重新设计已推送（`29180ad`）。第二轮（projects / graffiti / cosplay 与文案）在本地完成，等待用户确认后推送。
- 本地匿名调用 GitHub API 一小时只有 60 次，`make_cards.py` 跑两次就会用完；用完时脚本会拒绝覆盖。第二轮的 `assets/hero.svg` 是用稍早取到的数据重画的，推送后 CI 会用最新数据刷新。
- 本地验证方式：Python 语法检查、全部 SVG 的 XML 解析、`git diff --check`、实际运行 `make_cards.py` / `make_pacman.py` / `make_links.py`，并用无头 Chrome 截图检查终端卡、按钮、项目卡，以及吃豆人动画在多个时间点的画面。未在 Firefox / Safari 或 GitHub 移动端验证。
- 接手时发现未跟踪的 `.claude/`，其中为 `settings.local.json`；它是既有本机设置，未改动。
- 2026-11-15：按用户指示把页脚计数器 ID 由 `@TG-Twiligh` 更正为 `@TG-Twilight`；新 ID 是独立的计数，从头累计。
