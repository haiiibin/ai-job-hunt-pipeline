# 网申自动填表工作流（浏览器驱动，可复用）

用 Playwright MCP 驱动真实 Chrome，把**已定制好的简历内容**填进各公司官网/校招网申表单，**停在提交前**交用户确认。适用于任何官网（字节、腾讯、阿里等），不限于某一岗位。

## 角色分工（铁律）

```
生成定制简历(见 docs/cn-workflow.md) → 打开 JD → 用户登录(手机/短信或邮箱) → 我填表 → 截图给用户 → 用户亲手点提交
```

- **登录必须用户手动**（手机号 + 短信验证码，或邮箱密码）；账号密码我不经手。
- **绝不自动提交**。填完截图，由用户核对后亲手点"提交"。
- 登录态持久化在仓库根 `.playwright-profile/`（系统 Chrome + `--user-data-dir`，已 gitignore），**同一公司只需登录一次**，后续岗位直接进表单。

## 前置（一次性，用户自建）

- 安装 Node.js，把 `@playwright/mcp@latest` 写入仓库根 `.mcp.json`（用户自建；参数 `--browser chrome --user-data-dir .playwright-profile`）。
- 重启 Claude Code 后 `browser_*` 工具可用。

## 步骤

1. **先生成定制简历**（按 `docs/cn-workflow.md`：动态选经历/项目 + 锁定的教育/格式），再填表。表单内容来自简历。
2. `browser_navigate` 打开 JD；点"投递/申请" → 一般跳转登录页。
3. 用户登录（仅此一次，session 持久）。
4. `browser_snapshot` 抓表单。**很多中国校招门户会自动带出用户的旧档案**（几年前的旧简历也会带出）。逐项核对、更新，**不可信任旧值**。
5. 填字段：基本信息、教育（锁定内容）、工作/实习/项目（来自简历）、自我评价、语言、社交、了解渠道。长表单用 `browser_fill_form` 批量填稳定文本框。
6. **上传简历 PDF**：见下方"文件上传"。
7. `browser_take_screenshot` 给用户核对；**不提交**。

## 关键坑（每次都要注意）

- **⚠️ 上传后绝不点"解析并覆盖"**：它会用 PDF 自动解析内容覆盖掉刚填好的所有字段。出现该提示就忽略或关掉 ×。
- **文件上传受 allowed-root 限制**：`browser_file_upload` 只能传 MCP 配置允许目录内的文件。先把简历 PDF `cp` 到仓库根 `.playwright-mcp/`（已 gitignore），再上传；上传的**显示文件名 = 该副本的文件名**（命名见下）。
- **自定义下拉不是原生 `<select>`**：`browser_select_option` 会报错。改为点击展开 → 选项常渲染在页面底部的 portal 里 → 用 `text=选项文字` 选择器点击，或整页快照找 ref。
- **日期选择器的"至今"**：当前在职的结束日期，点开日期面板，底部有"至今"选项（否则报"请填写完整时间"）。
- **ref 会在 DOM 变动后失效**：每次 `添加/删除/上传` 后要重新快照；优先用 `browser_snapshot` 带 `target` 选择器只抓某个容器（如 `#formily-item-career_list`）省 token。
- **表单文本框不必和 PDF 逐字一致**：PDF 附件是主材料，文本框是结构化解析数据，措辞略有差异无妨。

## 字节特定 quirks（同类门户可类推）

- **了解渠道两级**：主问选"字节跳动招聘官方渠道/账号"；追问"在哪个官方渠道"选"校园招聘官网"（都对应"官网"渠道）。
- **校招 vs 社招资格**：校招岗要求应届身份；若已毕业且在职，可能不符合，考虑投社招同类岗。资格判断权在用户。

## 可复用档案 & 命名

- 网申字段固定值（证件号/微信/邮箱/手机/信息来源渠道默认官网等）维护在 `pipeline/profile.yaml`（用户自建，已 gitignore，字段清单见 README）。
- **简历命名**：`[你的姓名]_CV_[岗位简称].pdf`（不带 `CN_`）；上传副本与显示名都用此。

---

## 智联校园网申（xiaoyuan.zhaopin.com）完整套路（2026-06 实测）

### 两套在线简历，互不同步（重要）
- **社招**在线简历 = `i.zhaopin.com/resume`；**校招**在线简历 = 校园站独立一套。
- 校招网申**自动带出校园那套**，和你在 i.zhaopin 改的不是同一份。每次校招投递前必须在网申表里**逐项核对**（旧档常偏旧、缺最新经历、自我评价含"学生"措辞）。

### 投递流程（志愿制）
1. JD 页点"**立即投递**" → 新开标签"**志愿选择**"（`/scrd/postprocess2`）。
2. 校招是**志愿制**：1 个公司**最多 3 个志愿**，同一包内多岗位共享名额；已选过会显示"已申请"。底部"**下一步**"。
3. → "**网申表填写**"（`/scrd/resume2`，左侧 9 分区：个人信息/教育/求职意向/实习工作/语言/技能/奖励/附件/其他信息）。
4. 底部"**预览**"(`/scrd/resume/preview`) 看整份；"**立即投递**" = 最终提交，**绝不点**。预览页"修改简历"回表单。

### Element UI **只读日期控件**自动化（关键技巧）
这些日期 input 是 `readonly`，只能驱动弹层。**逐个处理、保证同时只开一个 picker**（双 picker 重叠会让 cell 报 "not visible"）：
1. `browser_click` 该 date input 打开弹层（多为 date/day 型，DOM 里 month-table 与 date-table 并存、隐藏的那个 cell 尺寸为 0）。
2. 点表头**月标签**切到月表：`.el-picker-panel:visible .el-date-picker__header-label:has-text("月")`。
3. 换年用箭头按钮：上一年 `button.el-icon-d-arrow-left`、下一年 `.el-icon-d-arrow-right`（**每次 evaluate 读 `.el-date-picker__header-label` 校准年份**）。
4. 点月：`.el-month-table td:has-text("五月")`（**中文数字**：一月…十二月；注意 `一月` 会与 `十一月` 撞，必要时用 `td.today` 或精确判断）。
5. 落日：`.el-date-table td.available span:text-is("1")` → 提交并关闭；`evaluate` 读 input.value 形如 `2026-05-01` 确认。
- **约束坑**：①「入职 ≤ 离职」：若离职是旧值会把目标年月**禁用**，所以**先设离职、再设入职**；②**离职禁未来**（在职岗只能选到当前月，用"当前月"表示"至今"，PDF 里仍写"至今"）；③重新打开同一 picker 会**记忆上次浏览的年份**→ 容易 overshoot，先读年份再增减。
- **真实 `browser_click` 才触发 Vue**；`evaluate` 里 `el.click()`/dispatch MouseEvent **不生效**。

### 工作经历上限 5 条
- 满 5 条后"添加"按钮消失。要加新经历就**编辑某条 in-place 覆盖**（= 删旧+加新，且不超限）：点该条"编辑"→ 表单出现"保存/取消"→ 覆盖工作单位/职务/日期/描述 → 保存。
  - 定位某条的"编辑"：`evaluate` 找到含该公司名+"入职时间"的最小块，给其"编辑"打 `data-` 标记，再 `browser_click [data-…]`。

### 自定义下拉 & 附件
- 工作类型下拉：点 input → `.el-select-dropdown__item:has-text("实习")`（全职/兼职/实习）。
- **简历附件上传**：隐藏 `input[name=multipartFile]`（el-upload）。点可见"重新上传"**不弹** filechooser → 解法：`evaluate` 把该 input 强制可见（`position:fixed;width/height;z-index`）→ `browser_click input[name=multipartFile]` → 出现 File chooser → `browser_file_upload` 传 `.playwright-mcp/` 里的副本（显示名=副本名）。传完把 style 复位。
  - ⚠️**附件不持久**：MCP 重连/页面 reset 会丢掉未随表单保存的附件，回到旧默认档 → **投递前在同一会话重传一次**，且让用户**别刷新**直接投。
- 个人作品里的"添加附件" = **个人作品（portfolio），投递时不发出**；要的是"**简历附件**"。

### 直接回到网申表
- 会话还在登录态时，可直接 `browser_navigate` 到 `/scrd/resume2?...`（完整 query）跳过 JD→志愿→下一步。

---

## 腾讯校招（join.qq.com）完整套路（2026-07 实测）

### 找岗 & 投递流程
- 岗位库 `join.qq.com/post.html`：勾选目标批次（如"2026校园招聘"= 全职应届，毕业窗口以页面原文为准，留学生批次常放宽，远程面试无需回国）；搜索框可按"运营/数据/分析"等关键词筛。
- 岗位详情 `post_detail.html?postid=…` → 点 **"投递简历"**。
- **一人只能投 1 个岗**：若已投过别的岗，会弹"是否更换成 XXX"。**确认键=切换/提交动作 → 铁律:让用户亲手点**。未进面试前可随时改投。
- 确认后跳 **`resumeedit.html`（在线简历表）** → 底部 **"提交简历"** = 最终提交（**绝不替用户点**）。

### ⚠️ "解析并填写"（腾讯版"解析并覆盖"）
- 更新简历附件后会提示 **"解析简历内容填写到下方表单？解析并填写"**。默认铁律**不点**。
- **例外（需用户明确同意）**：当在线简历是旧/错版、而上传的 PDF 是当前岗好版本时，点"解析并填写"可自动把经历/项目/描述灌进去，省几十项手填。
- **解析副作用（务必解析后逐项复核）**：解析虽能补全实习+项目+描述，但可能**清空教育明细**（院系/成绩排名/GPA/满绩/导师）、**清空期望工作城市**、部分**日期只填了结束缺开始**。解析≠万事大吉，必须全表复核补齐。

### Element-UI 控件坑（腾讯表单大量使用）
- **日期控件（el-date-picker）认死理**：用 `evaluate` 原生 setter+dispatch(input/change/blur) 赋值**不生效**：输入框显示有字，blur 后被清空/前端不记录，校验标 **"未填写"**。**必须真实交互**：`browser_click` 该日期框 → `browser_type` 输入 `YYYY-MM-DD` → `browser_press_key Enter`（editable 日期框回车即提交）。实测这样才 commit。
- **el-input 文本框**（院系/GPA/语言成绩/描述/奖项名）：原生 setter+dispatch('input') **能生效**（Vue @input 收得到），可批量 evaluate 填。
- **el-select / el-cascader（只读）**：原生赋值无效，必须真实点击。多选(期望城市)内层 input 被 `.el-select__tags` 挡，空标签容器 0 高度不可点 → 直接 `browser_click input`（tags 空时不挡）打开下拉，再点 `.el-select-dropdown__item`。级联(就读地)逐级点选（注意同名地名会撞，如"河北区"与"河北"，用 `text===` 精确匹配）。
- **验证收尾**：`evaluate` 数页面 `未填写` 文本数量应=0；`选择日期` 空值只应剩"至今"的结束日期。在职岗结束日期勾 **"至今"** checkbox（点 `.el-checkbox__inner`）。
- **必填项终检**：该表不用标准 `.el-form-item.is-required`，直接逐个已知必填字段读 `input.value` 最稳；隐私政策同意 checkbox 默认未勾、属法律同意 → 留给用户亲手勾。

---

## 字节校招（jobs.bytedance.com/campus）完整套路（2026-07 实测）

### 找岗（大厂有名额上限，先通览挑最优 1-2）
- 岗位搜索页 URL 直达：`/campus/position?keywords=数据分析&location=CT_11&project=<id>`（CT_11=北京）。**关键词只是初筛**，同城同关键词的正式岗常混有大量算法/销售/研发。
- **必须按招聘项目过滤**：左侧"招聘项目→正式→XX届校园招聘"（点后 URL 出现 `project=…` 才生效，project id 每届不同；核对该项目的毕业窗口含你的毕业年月）；否则默认混入大量"日常实习/下一届 Intern"。React 筛选器 `el.click()` 单击叶子节点即可（点多层会 toggle 反复开关）。
- **非技术背景（商科/数据/非CS）的对口正式岗**常在职能序列（如 Corporate Services 的策略/综合运营类，要求"专业不限+咨询/数据分析/项目管理实习优先"）。产品经理/算法/后端一般不匹配。
- 岗位详情 `/campus/position/<postid>/detail` 读 JD → 点"投递"→ 跳 `/campus/resume/<postid>/apply` 在线表单。
- **每人 2 次投递名额**（比腾讯宽松）；未登录也能打开 apply 表单，登录态持久时**直接带出旧档案**。

### 登录 & 旧档案
- 持久 profile 若登录过，apply 表单**自动带出上次投递的完整旧简历**（旧经历/旧项目/缺最新学历）。`fetch('/api/v1/user/profile')` 可能返回 loggedIn:false 但表单仍有数据 → 以表单实际带出的账号数据为准。

### ⚠️ "解析并覆盖"（默认铁律不点）
- 更新简历附件后弹"将简历内容解析到下方表单？**解析并覆盖**"。默认**不点**。
- **例外（需用户明确授权）**：旧档案是整份过时简历时，上传本岗定制 PDF→点"解析并覆盖"可一次性用新简历替换全部经历/项目/教育/描述，远比手动逐项改稳。实测效果好（多段实习+项目+描述全部正确替换，旧条目自动消失）。
- **解析副作用（务必逐项复核补齐）**：解析会**清空** 证件号、期望工作地点(基本信息内)、教育明细（学历类型/起止时间，且常只保留最高学历一条→需手动加本科）、部分只填结束缺开始；**项目描述有 OCR 乱码**（如 Canvas API→"Canvas Amf"、5G→"Rd"、AI→"Af"、Demo→"aemo"）→用简历原文覆盖；**自我评价可能保留旧内容**→替换。邮箱/姓名/手机/实习经历一般解析正确。

### 控件坑（字节用 ud/formily 组件，非 Element-UI）
- **普通文本框**（邮箱/证件号/学校/学院/专业/自我评价/项目描述）：native setter+dispatch(input/change/blur) **能生效**（React onChange 收得到），可批量 evaluate 填。
- **日期控件（起止时间）**：是可编辑文本框+日历。**坑：点日历里的"08月"格会用面板当前默认年覆盖你输入的年份**。可靠解法：`browser_click` 日期框 → `browser_type` 输入 `YYYY-MM` → **按 Escape 关闭日历，不要点月份格**（纯键入值会 commit）。
- **ud__select 下拉（学历类型/学历/期望城市）**：`browser_select_option` 无效；必须真实点 `.ud__select__selector` **容器**（点内层 search input 会被 `.ud__select__selector__placeholder` 挡）。选项在 portal 里 `.ud__select__list__item`，取 `offsetParent!==null` 的可见项点击。**被底部"隐私区"粘性栏遮挡时**报 "intercepts pointer events"→先 `el.scrollIntoView({block:'center'})` 把字段移到视口中间再点。点选择器有时会 toggle（点一次开、再点关）→ 点后立即读 `.ud__select__list__item` 确认开着再选。
- **加教育条**：教育区底部"添加"→新条结构同首条（e2_0/1=起止日期文本框、e2_2=学历类型 readonly select、e2_3=学校、e2_4=学历 readonly select、e2_5=学院、e2_6=专业）。
- **终检**：`evaluate` 数 `未填写`=0；`请填写X`（class=applyFormModuleWrapper-des）是章节副标题非报错；`[class*="error"]` 可见且有文字才是真错。
- **隐私同意 checkbox（底部第 ~10 个 checkbox，y≈固定栏）默认可能已勾**（默认勾或解析带出）→ 按铁律 `browser_click` 取消，交用户亲手勾。提交按钮="提交简历"，**绝不替点**。
- **提交成功**：跳 `/campus/resume/applied`，标题"投递成功"。查进度同一路径。
