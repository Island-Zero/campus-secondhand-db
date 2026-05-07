# 校园二手交易平台

基于 Flask + SQLite 的数据库课程项目，面向校园闲置物品交易场景，实现用户、商品、订单、查询统计、视图、事务和权限控制等功能。

在线访问地址：

```text
https://campus-secondhand-db-684z.vercel.app/
```

项目说明文档：

```text
项目说明.md
```

## 功能概览

- 首页概览：展示用户数、商品数、未售商品数和订单数。
- 登录与权限控制：区分管理员和普通用户，普通用户只能浏览和查询，管理员可以执行写操作。
- 用户管理：展示用户编号、用户名和联系电话。
- 商品管理：展示商品名称、分类、价格、卖家和状态，支持新增商品、修改价格、删除未售商品。
- 订单管理：展示订单编号、商品名称、买家 ID、买家姓名和订单日期。
- 购买商品：购买成功后写入 `orders` 表，并将 `item.status` 修改为已售出。
- 查询统计：支持基本查询、连接查询、聚合分组查询和视图查询。
- 业务规则：禁止重复购买已售商品，禁止购买自己发布的商品。
- 事务控制：购买流程使用事务保证订单记录和商品状态一致。

## 测试账号

```text
管理员账号：admin
管理员密码：admin123

普通用户账号：user
普通用户密码：user123
```

## 技术栈

- 后端：Flask
- 数据库：SQLite
- 前端：HTML、CSS、Jinja2、JavaScript
- 部署：GitHub + Vercel

## 本地运行

进入项目目录：

```powershell
cd E:\Code\DB_project
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

启动服务：

```powershell
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

## 项目结构

```text
.
|-- app.py                  # Flask 应用入口、路由、业务逻辑和数据库操作
|-- requirements.txt        # Python 依赖
|-- vercel.json             # Vercel 部署配置
|-- 项目说明.md             # 课程项目说明文档
|-- data/
|   |-- campus_trade.db     # SQLite 数据库文件
|   |-- database.sql        # 建表、约束、触发器和视图定义
|   `-- test/               # 本地测试数据库文件
|-- templates/              # Jinja2 页面模板
|-- static/                 # 本地静态资源
|-- public/                 # Vercel 静态资源兼容目录
|-- alt_md_images/          # 项目说明文档截图
`-- docs/
    `-- assignment/         # 课程要求和原始截图资料
```

## 数据库说明

数据库包含三张核心表：

- `user`：保存用户信息。
- `item`：保存商品信息。
- `orders`：保存订单信息。

主要约束包括：

- 商品状态 `status` 只能为 0 或 1。
- `orders.item_id` 设置唯一约束，保证同一商品最多成交一次。
- 商品、卖家、买家之间通过外键保持关联。
- 触发器用于保证订单商品必须处于已售状态，并防止已有订单的商品被改回未售状态。

系统创建两个视图：

- `sold_item_view`：已售商品视图，包含商品名和买家 ID。
- `unsold_item_view`：未售商品视图，包含未售商品编号、名称、分类、价格和卖家 ID。

## 查询任务

基本查询：

- 查询所有未售出的商品。
- 查询价格大于指定值的商品。
- 查询指定分类的商品。
- 查询指定卖家发布的商品。

连接查询：

- 查询所有已售商品及其买家姓名。
- 查询每个订单的商品名、买家 ID、买家名和日期。
- 查询卖家 `u001` 的商品是否被购买。

聚合与分组：

- 统计商品总数。
- 统计每类商品数量。
- 计算商品平均价格。
- 查询发布商品数量最多的用户。

视图查询：

- 查询已售商品视图。
- 查询未售商品视图。

## 部署说明

项目使用 GitHub 托管代码，并通过 Vercel 自动部署。推送到 `main` 分支后，Vercel 会自动构建并更新线上版本。

Vercel 配置要点：

```text
Framework Preset: Flask
Root Directory: ./
Build Command: None
Install Command: pip install -r requirements.txt
```

环境变量：

```text
SECRET_KEY=campus-trade-secret-1006
```

说明：SQLite 适合课程项目和在线演示。Vercel 的运行环境不适合作为长期持久化数据库环境，重新部署或运行环境重置后，线上数据可能恢复到初始状态。真实生产环境建议迁移到 MySQL、PostgreSQL 等持久化数据库。
