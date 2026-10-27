# 设计系统生成工作流

## 目标

根据产品、用户、任务和平台限制，生成可追踪、可持久化、可覆盖的设计系统。它不是固定模板。

## 前置

- 已完成 [需求分析](analyze-requirements.md)。
- 已识别技术栈：`wechat-native`、`uni-app` 或 `taro`。
- 已确认用户是否指定风格；没有指定时不要默认套用某个流行风格。

## 步骤

### 1. 检索产品与推理

```bash
python scripts/search.py "音乐播放器 持续播放 内容发现" --domain product
python scripts/search.py "内容消费 播放状态" --domain reasoning
```

查看返回的 ID、命中字段与匹配原因。不要把 0 结果伪装成命中。

### 2. 选择风格

- 用户指定了风格：直接使用 `--style`，并在结果中检查冲突。
- 用户没有指定：读取产品记录的首选风格，再结合目标用户和场景判断。
- 需要更多风格候选时：
  ```bash
  python scripts/search.py "现代东方 克制 内容" --domain style -n 4
  ```

### 3. 生成 Master

```bash
python scripts/generate_design_system.py \
  --product "音乐播放器小程序" \
  --style "现代极简" \
  --stack wechat-native \
  --output ./design-system \
  --format both
```

产物：

- `MASTER.md`：人读的设计事实源。
- `MASTER.json`：结构化 token、规则与来源 ID。
- `tokens.wxss` / `tokens.scss`：按技术栈生成 token 文件。
- `pages/*.md`：默认页面覆盖。

### 4. 检查冲突与缺口

必须阅读 MASTER 第 5 节“设计选择理由与冲突”，确认：

- 指定风格是否与产品推荐冲突。
- 配色和风格是否有兼容标记。
- 信息密度与风格是否矛盾。
- 对比度是否通过。
- 平台规则中哪些需要真机验证。

冲突不能被静默删除。若决定接受例外，在页面覆盖或项目设计决策中写明理由。

### 5. 页面覆盖

```bash
python scripts/generate_design_system.py \
  --product "文创商城小程序" \
  --stack wechat-native \
  --pages home,product-detail,profile \
  --output ./design-system
```

默认继承 Master。页面只允许覆盖顺序、局部间距和页面特有状态，不允许另起配色/字体/圆角系统。

### 6. 复核生成结果

- 每个选择都有来源 ID。
- 不同产品类型的风格、配色、布局和 token 有合理差异。
- 缺失数据有明确回退说明，没有伪造记录。
- 未执行的真机、截图和视觉检查列在限制中。
- Token 与组件实际实现能一一对应。

### 7. 保护已有设计

如果 `MASTER.md` 已存在，生成器会跳过而不是覆盖。先读现有 Master，确认是否需要更新；只有得到明确授权才使用 `--force`。

## 输出

- `design-system/MASTER.md`
- `design-system/MASTER.json`
- token 文件
- 页面覆盖
- 冲突与限制清单
- 数据来源 ID

## 完成标准

- [ ] 1 个产品任务对应 1 套可解释设计语言。
- [ ] 配色、排版、布局、组件、UX、平台规则均有来源。
- [ ] P0/P1 冲突为零或在实现前解决。
- [ ] 页面覆盖不形成第二套设计系统。
- [ ] 未验证项明确记录。

## 相关文件

- [Master 模板](../templates/design-system-master.md)
- [页面覆盖模板](../templates/page-override.md)
- [设计原则](../references/design-principles.md)
- [图标、组件与状态检查](../references/component-design.md)