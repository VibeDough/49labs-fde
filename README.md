# 49Labs · FDE 交付实战
公开阅读三册手册、术语词典、逐节笔记与门店实训。正式自测题存放在私有 Cloudflare KV，使用网站体验码解锁。

## 本地阅读
运行 `python3 build.py` 和 `python3 -m http.server 8000 -d dist`，访问 http://localhost:8000/tools/fde/ 。生成器只依赖 Python 标准库。

## 托管
Pages Functions 从 QUIZ 绑定的 KV 读取 quiz-html，通过服务端 secret UNLOCK_CODE 校验体验码。自行部署时配置自己的 KV 和 secret。更换 secret 后旧设备会重新领码。完成解锁后，浏览器可以读取本次获准使用的完整题库。

## 来源与许可
原创源码采用 MIT 许可。原创学习材料采用 CC BY 4.0，署名 49Labs。第三方资料、商标和引文的权利归原作者。腾讯云课程见各节笔记出处，范冰原书见 https://fde4.ai/book/ 。私有题库未包含在公开许可内。
