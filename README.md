# FongMi 固定配置入口

这个仓库通过 GitHub Actions 定时读取上游配置，并发布到 GitHub Pages。电视只需保存同一个地址：

**电视配置 URL：** https://hessukwon.github.io/fongmi-config/tv.json

## 更换上游

编辑仓库根目录的 `upstream.txt`，只写一个完整的上游配置 URL，然后提交。当前上游为 Larry 自维护的 FongMi 单仓 JSON：`https://raw.githubusercontent.com/larry-biu/tvbox-config/main/fongmi.json`。同步脚本会检查它是否为配置 JSON，再发布到 Pages。此配置中的 spider JAR、扩展 JSON 和直播列表仍由电视直接从该仓库获取；请先在一台电视验证导入和播放。

同步任务每 6 小时运行一次，也可以在仓库的 **Actions → Sync and publish FongMi config → Run workflow** 手动运行。成功后 Actions 会部署最新配置；上游请求失败或返回不符合预期的导航页时，任务会失败并保留 Pages 上上一次成功发布的配置。

## 更新生效

上游变化一般在下一次同步后生效。需要立即更新时，手动运行 workflow，等部署成功后，在电视的影视应用里刷新这条配置。电视端继续使用上面的固定 URL。

若 GitHub Pages/CDN 仍返回旧内容，可在 Actions 确认最新运行已完成，再稍等片刻并在应用中重新刷新配置。

## 目录说明

- `upstream.txt`：可编辑的上游地址。
- `scripts/sync_config.py`：获取、校验并生成 `site/tv.json`。
- `.github/workflows/publish-config.yml`：定时/手动同步并发布 GitHub Pages。
- `site/tv.json`：Actions 运行时生成，不需要手动编辑。

仓库和 Pages 内容是公开的。此方案中，首次加载由 Pages 提供同步后的配置文件；配置文件里若有影视站点或视频播放的绝对 URL，FongMi 后续是否直接请求那些站点取决于配置格式和应用逻辑。本仓库目前没有反向代理那些后续媒体/站点请求。

## 故障排查

1. 在 **Actions** 打开最近一次运行，查看上游获取/校验是否成功。
2. 若失败，确认 `upstream.txt` 中的地址仍可用，并返回 FongMi 可识别的原始配置，而不是 HTML 导航页。
3. 若 Actions 成功但电视没更新，确认部署步骤成功，然后在应用内刷新；必要时等待 CDN 缓存更新。
4. 若上游改了地址，只改 `upstream.txt` 并提交，无须改电视中的配置 URL。

同步请求未设置长期缓存；Pages/CDN 有自己的边缘缓存。免费额度和 GitHub Pages/Actions 的使用限制以 GitHub 当前账户方案为准。
