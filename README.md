# XutheringWavesUID

<p align="center">
  <a href="https://github.com/Loping151/XutheringWavesUID"><img src="https://s2.loli.net/2024/10/08/ku3pLJBPoGjfQWq.png" width="256" height="256" alt="XutheringWavesUID"></a>
<h1 align = "center">XutheringWavesUID</h1>

## 说明

本插件为 [WutheringWavesUID](https://github.com/tyql688) 的构建版本，加强了评分和伤害计算的保护，确保本地计算的权重和伤害与服务器一致。本插件将继续更新，对于不计划自己编写权重计算和伤害计算的用户，与之前没有任何区别。

另外：目前提供可在网页直接使用的web版，无需在社交软件上使用：[WEBUID 传送门](https://ngabbs.com/read.php?tid=45645691)

国际服用户支持识别直出，同时支持小程序、官方面板截图：[用例](https://github.com/Loping151/ScoreEcho)，支持伤害计算功能。
<details>
  <summary>用例</summary>
  <p align="center">
    <img src="https://img.nga.178.com/attachments/mon_202511/30/nqQ1aq-2wfzKwT1kSc6-80.jpg" alt="示例图" width="480" />
    <img src="https://img.nga.178.com/attachments/mon_202511/30/nqQ1aq-cqzxZjT1kShs-1ey.jpg" alt="示例图" width="480" />
    <img src="https://img.nga.178.com/attachments/mon_202511/30/nqQ1aq-leszKqToS5j-cn.jpg" alt="示例图" width="480" />
    <img src="https://img.nga.178.com/attachments/mon_202511/30/nqQ1aq-l5caZiT1kShs-1ey.jpg" alt="示例图" width="480" />
  </p>
</details>

在线使用：[识别计算 传送门](https://scoreecho.loping151.site/)

```bash
mv gsuid_core/gsuid_core/plugins/WutheringWavesUID ./WutheringWavesUID_bak
cd gsuid_core/gsuid_core/plugins/
git clone https://github.com/Loping151/XutheringWavesUID.git
```
将继承原有数据和配置。

如果为首次安装：
```
git clone https://github.com/Loping151/XutheringWavesUID.git
``` 

总排行数据库重建：群号 653696746。如果仅需要本地伤害计算而不希望打扰，可发邮件 wkl@loping151.com 申请计算服务token，支持较少的请求量和用户量，但完全足以小范围使用，一般都欢迎入群。

## 丨安装提醒

> **注意：该插件为[早柚核心(gsuid_core)](https://github.com/Genshin-bots/gsuid_core)
的扩展，具体安装方式可参考[GenshinUID](https://github.com/KimigaiiWuyi/GenshinUID)**
>
> **如果已经是最新版本的`gsuid_core`, 可以直接对bot发送`core安装插件XutheringWavesUID`，然后重启core以应用安装**
>
> **权重和伤害计算更新时，仅需发送 ww下载全部资源 将自动重载，无需重启**

## 丨其他

+ 本项目仅供学习使用，请勿用于商业用途，禁止将**仅具有本插件功能**的服务进行收费
+ [GPL-3.0 License](https://github.com/Loping151/XutheringWavesUID/blob/main/LICENSE)

## 支持设备列表：
win_amd64: python3.10-3.13<br>
win_arm64: not yet<br>
linux_x86_64: python3.10-3.13<br>
linux_aarch64: python3.11-3.13<br>
macos_intel: python3.10-3.13<br>
macos_apple: python3.10-3.13<br>
android: python3.10-3.12<br>

**！本插件所含构建没有任何风险后门！本插件所含构建只读取gsuid_core目录下的文件，只请求非构建部分显示的域名！请随意进行流量检查和读写检查！**

## 致谢
- ⭐[Echo](https://github.com/tyql688)
- 特别鸣谢 [Wuyi无疑](https://github.com/KimigaiiWuyi) 为 WutheringWavesUID 作出的巨大贡献！本插件的设计图均出自 Wuyi无疑
  之手！！！
- [鸣潮声骸评分工具](http://asfaz.cn/mingchao/rule.html) 鸣潮声骸评分工具
- [waves-plugin](https://github.com/erzaozi/waves-plugin) Yunzai 鸣潮游戏数据查询插件
- [Yunzai-Kuro-Plugin](https://github.com/TomyJan/Yunzai-Kuro-Plugin) Yunzai 库洛插件
- [Kuro-API-Collection](https://github.com/TomyJan/Kuro-API-Collection) 库街区 API 文档
- 特别鸣谢以下攻略作者
  - [Moealkyne](https://www.taptap.cn/user/533395803)
  - [小沐XMu](https://www.kurobbs.com/person-center?id=10450567)
  - [金铃子攻略组](https://space.bilibili.com/487275027)
  - [結星](https://www.kurobbs.com/person-center?id=10015697)
  - [小羊早睡不遭罪](https://space.bilibili.com/37331716)
  - [吃我无痕](https://space.bilibili.com/347744)
  - [巡游天国FM](https://space.bilibili.com/444694026)
