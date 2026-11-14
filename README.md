<!--
  ─────────────────────────────────────────────────────────────
   落日终端风格。图片几乎全是自托管的，不看第三方服务脸色：
     assets/hero.svg         页首 neofetch 终端卡   → tools/make_hero.py
     assets/pacman.svg       吃豆人 + Claude 小精灵 → tools/make_pacman.py
     assets/feature-*.svg    主项目横幅 / 仓库卡    → tools/make_cards.py
     assets/pin-*.svg
       ↑ 以上由 .github/workflows/stats.yml 每天自动刷新
         （入口统一是 python tools/make_cards.py）
     assets/link-*.svg       像素链接按钮（静态）   → tools/make_links.py
     assets/art-*.svg        涂鸦作品卡（静态）     → tools/make_graffiti.py
     assets/cos-*.svg        cos 对话卡（静态）     → tools/make_dialogue.py
     assets/divider.svg      分隔线（手写）
     Alastor.Cos/*.webp      cos 主图（本地原图裁出，原图走 .gitignore）
                             与两个角色头像（现拉官方立绘裁圆）
                             → tools/make_cos_assets.py
   配色与等宽排版的公共零件在 tools/sunset.py。
   仅剩的外部依赖：count.getloli.com 计数器、
   r6.awads.cc 图标（你自己的服务）。
  ─────────────────────────────────────────────────────────────
-->

<a href="https://me.awads.cc/"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/hero.svg" width="100%" alt="Simon Twilight — The SuperCowboy who lives forever in the sunset"/></a>

<p align="center">
<a href="https://steamcommunity.com/id/SuperCowboy/"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-steam.svg" width="32%" alt="Steam"/></a>
<a href="https://x.com/Simon_Twilight"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-x.svg" width="32%" alt="X"/></a>
<a href="https://www.pixiv.net/users/106832575"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-pixiv.svg" width="32%" alt="Pixiv"/></a><br/>
<a href="https://me.awads.cc/"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-homepage.svg" width="32%" alt="个人主页"/></a>
<a href="https://awads.cc"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-blog.svg" width="32%" alt="博客"/></a>
<a href="https://afdian.com/a/AdsRule"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/link-sponsor.svg" width="32%" alt="赞助我"/></a>
</p>

<p align="center">平时写广告过滤规则和一些小工具，偶尔画画、出 cos。</p>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pacman.svg" width="100%" alt="吃豆人正在吃掉我过去一年的贡献格子，三只 Claude 小精灵在后面追"/>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/divider.svg" width="100%" alt=""/>

## `~/projects`

### `ads-rule/` 秋风广告规则

<a href="https://github.com/TG-Twilight/AWAvenue-Ads-Rule"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/feature-AWAvenue-Ads-Rule.svg" width="100%" alt="AWAvenue-Ads-Rule"/></a>

<p align="center"><sub>众多优秀广告规则的上游，开源社区中最棒的广告过滤器列表之一。<br/>🌐 <a href="https://awavenue.top">awavenue.top</a> · 📦 <a href="https://github.com/TG-Twilight/AWAvenue-Ads-Rule">GitHub</a></sub></p>

### `apps/` 应用与实用工具

<table>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/c001apk"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-c001apk.svg" width="100%" alt="c001apk"/></a></td>
<td><sub>第三方酷安客户端，从 c001apk-flutter 接手过来继续维护。修了失效的 API，补了简体中文，能看动态、文章和评论，收藏和屏蔽都存在本地。Flutter 写的，目前主要顾 Android 和 Windows。</sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/Any.ADB"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-Any.ADB.svg" width="100%" alt="Any.ADB"/></a></td>
<td><sub>给 Android 设备开一个固定端口的无线 ADB，走 Sui / Shizuku 或者直接 <code>su</code>。会检查端口冲突，失败了自动回滚，也可以开机恢复。配上 Tailscale 可以跨网络调试。</sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/Call.Editor"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-Call.Editor.svg" width="100%" alt="Call.Editor"/></a></td>
<td><sub>通话记录编辑器：增删改，外加 JSON 备份和恢复，恢复时会去重。Kotlin + Compose 写的原生应用，没有申请联网权限。</sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/DeskPins"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-DeskPins.svg" width="100%" alt="DeskPins"/></a></td>
<td><sub>把窗口钉在最上层的小工具。原作者 2015 年停在 1.32，我接着做了 64 位、简体中文、深色模式、Per-Monitor DPI 和便携模式，还补上了缺失的私有框架，现在源码拿下来就能编译。</sub></td>
</tr>
</table>

### `web/` Web 工具与服务

<table>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/JKS.Recover"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-JKS.Recover.svg" width="100%" alt="JKS.Recover"/></a></td>
<td><sub>忘了 Android 签名文件（keystore）密码时用的找回工具。全在浏览器本地算，不上传任何东西。<br/>🌐 <a href="https://jks.awads.cc">jks.awads.cc</a></sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/Fastboot.js-Next"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-Fastboot.js-Next.svg" width="100%" alt="Fastboot.js-Next"/></a></td>
<td><sub>基于 WebUSB 的网页刷机工具。在 fastboot.js 上换了 Material 3 界面，加了中英双语和危险操作的二次确认。vibecoding 练手作，刷机前自己想清楚。</sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/Starstruck"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-Starstruck.svg" width="100%" alt="Starstruck"/></a></td>
<td><sub>查一个仓库被哪些「大佬」Star 过。<br/>🌐 <a href="https://star.awads.cc">star.awads.cc</a></sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/Gamer-Skill-Icons"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-Gamer-Skill-Icons.svg" width="100%" alt="Gamer-Skill-Icons"/></a></td>
<td><sub>游戏图标的 SVG API，可以贴在 README 或任何网页里，也能自己部署。下面 cosplay 里的 R6 干员图标就是它出的。<br/>🌐 <a href="https://r6.awads.cc">r6.awads.cc</a></sub></td>
</tr>
</table>

### `games/` 游戏与折腾

<table>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/CaveStory-rs"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-CaveStory-rs.svg" width="100%" alt="CaveStory-rs"/></a></td>
<td><sub>洞窟物语引擎 doukutsu-rs 的分支。加了简中 / 英 / 日三语、手柄布局和更强的震动，Android 上支持离线资源和存档迁移，蓝牙手柄的震动是借 Shizuku 做的。</sub></td>
</tr>
<tr>
<td width="46%"><a href="https://github.com/TG-Twilight/AC130.Zombie.Gunship"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/pin-AC130.Zombie.Gunship.svg" width="100%" alt="AC130.Zombie.Gunship"/></a></td>
<td><sub>AC130Beta 的 Cheat Engine 修改表：金钱、移动、弹药、伤害这些，重生和换枪之后依然生效。仓库里有 Lua 源码、CT 生成工具和模拟内存测试。只用于单人或自己开的房间。</sub></td>
</tr>
</table>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/divider.svg" width="100%" alt=""/>

## `~/graffiti`

偶尔画点东西，都发在 Pixiv：**[Twilight](https://www.pixiv.net/users/106832575)**

<p align="center">
<a href="https://www.pixiv.net/artworks/150784396"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/art-150784396.svg" width="49%" alt="Dear？"/></a>
<a href="https://www.pixiv.net/artworks/146949017"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/art-146949017.svg" width="49%" alt="Keep Smile！My Dear！"/></a><br/>
<a href="https://www.pixiv.net/artworks/146948848"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/art-146948848.svg" width="49%" alt="Hey! My Dear?"/></a>
<a href="https://www.pixiv.net/artworks/119393336"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/art-119393336.svg" width="49%" alt="Judgement - HellTaker"/></a>
</p>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/divider.svg" width="100%" alt=""/>

## `~/cosplay`

### `rainbow-six-siege-x/` Tom Clancy's Rainbow Six Siege X — Jäger & Solis in Hotel

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/R6.Cos/jager-solis.webp" alt="Jäger and Solis" width="100%"/>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/cos-r6.svg" alt="Jäger: Hey, Ash is up ahead, let's go take her out！ Solis: Hurh？" width="100%"/>

### `hazbin-hotel/` Hazbin Hotel — Alastor, the Radio Demon

<table>
<tr>
<td width="46%"><img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/Alastor.Cos/alastor.webp" alt="Alastor" width="100%"/></td>
<td>
<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/cos-alastor.svg" alt="Alastor: You're never fully dressed without a smile！ Vox: ...Put me down, Alastor." width="100%"/>
<p align="center">📍 2026 成都世界动漫展 · 5.1 – 5.4</p>
</td>
</tr>
</table>

<img src="https://raw.githubusercontent.com/TG-Twilight/TG-Twilight/main/assets/divider.svg" width="100%" alt=""/>

<div align="center">

<img src="https://count.getloli.com/get/@TG-Twiligh?theme=booru-helltaker" alt="Profile Views" width="640"/>

<br/><br/>

<sub>🌅 <i>See you on the other side of the sunset.</i></sub>

</div>
