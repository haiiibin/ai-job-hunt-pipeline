# AI Job Hunt Pipeline

用 Claude Code 把求职流程做成流水线:从发现岗位到"网申表填好、停在提交前",全程人在回路。

```
/hunt 岗位雷达 → JD 评分(scoring-rubric) → 定制简历(CV/CL/中文简历) → compile_cv.py 编译 → /apply 填表待提交
   发现            打分                     裁剪                        产出 PDF              用户亲手提交
```

三条铁律(任何阶段不得违反):**绝不自动提交任何表单;绝不点"解析并覆盖";登录一律用户手动**。

---

## 仓库结构

```
CLAUDE.md                  本文件: 工作流主文档
compile_cv.py              CV/CL 编译器(LaTeX + HTML 两种输入)
.claude/commands/hunt.md   /hunt 岗位雷达命令
.claude/commands/apply.md  /apply 网申全链路命令
docs/cn-workflow.md        中文简历工作流(格式锁定 + 满页验证)
docs/webapp-autofill.md    浏览器填表工作流(平台坑速查)
docs/scoring-rubric.md     JD 评分标准(A-F 维度 + 反猜测纪律)
templates/cv_template.tex  英文 CV 模板(pdflatex)
templates/cl_template.tex  英文 CL 模板(xelatex)
templates/cn_skeleton.html 中文简历骨架(CSS 锁定)
pipeline/filter_rules.yaml 硬规则粗筛词库(/hunt 用)
```

以下由**用户自建**,已 gitignore,绝不提交:

```
resume-data/               简历素材库(结构见下节)
pipeline/jobs.yaml         岗位去重库 + 名额账本(schema 见 hunt.md Phase 0)
pipeline/profile.yaml      网申固定字段档案(证件号/微信/邮箱/手机/渠道等)
pipeline/watchlist.md      监控清单 + 候选池 + 已投递记录
output/                    每个岗位的定制简历产出
photo.jpg                  中文简历证件照
.playwright-profile/       浏览器登录态
.playwright-mcp/           简历上传中转目录
.mcp.json                  Playwright MCP 配置
```

---

## Source Documents: resume-data/ 约定

所有简历内容**只能**来自这里,按 JD 动态选取,不维护多份固定简历:

```
resume-data/
  _index.yaml          索引入口,每次必读(轻量)
  skills.md            技能列表(双语可选)
  education.md         教育背景(双语可选)
  experience/*.md      每段经历一个文件
  projects/*.md        每个项目一个文件
```

`_index.yaml` 每条记录的字段:

```yaml
experiences:
  - file: experience/company-a.md
    tags: [data, analytics, sql]     # 与 JD 匹配用
    priority: required               # required=每份简历必选 / optional=按条件选
    condition: ""                    # optional 时的选取条件(如"仅金融岗")
    date_range: "2025-12 ~ present"
projects:
  - file: projects/project-x.md
    tags: [ml, visualization]
    date_range: "2025-03"
```

每个 experience/project 文件内含:core bullets(核心表述,必用)+ 若干 `*_focus` bullets(按 JD 方向替换的侧重版),中英文各一节。

**Source Reading Logic:**

1. 读 `resume-data/_index.yaml`
2. 判断 JD 主要类型(data / finance / consulting / marketing / ops / product)
3. experiences:priority=required 全选;optional 按 condition 判断
4. projects:按 tags 与 JD 重合度排序,选前 3-5 个
5. 读对应文件:英文简历读 EN section;中文简历读 ZH section
6. 每个文件选 core bullets + 对应 focus bullets,目标 2-3 条/经历

**AUTHENTICITY:** Never fabricate content. Only use real experiences from provided files. Estimate realistic metrics based on documented scope only; never invent achievements.

---

## CV 生成规则(英文 LaTeX)

- 先读 `templates/cv_template.tex`,填占位符,不改版式
- **无 Summary 段**:Header 后直接 EDUCATION
- Section 顺序:EDUCATION → PROFESSIONAL EXPERIENCE → EXTRACURRICULAR → SKILLS
- 经历按 reverse chronological(最近在前)
- 每条 bullet 必须含量化指标(数字/百分比/时间/规模),单条 ≤ 30-40 词
- 默认每段经历 2 条 bullet,空间明显富余才加第 3 条
- **严格单页**:超页先砍 extracurricular,再减 bullet;不足页则补充条目填满

## CL 生成规则(英文 Cover Letter)

- 先读 `templates/cl_template.tex`
- **日期实时查询**:写 CL 前 web search 当天目标城市日期,不用训练数据
- **公司调研先行**:主营业务/近期动态/文化/该岗位要解决的问题,开头段必须体现具体调研发现
- 字数硬限:开头 ≤70 词;每 bullet ≤55 词;收尾 ≤50 词;全文 ≤280 词;单页
- **CV/CL 互补**:CL 用 CV 未重点展示的经历,不重复
- 开头明确表达加入"这家公司这个岗位"的意向,结尾再次确认

## 中文简历

完整流程见 `docs/cn-workflow.md`(骨架 CSS 锁定、PyMuPDF 满页验证 fill% ≥ 93%、单页硬性要求)。

## JD 评分

标准见 `docs/scoring-rubric.md`:A-E 五维加权得 F 分,含反猜测评分纪律与岗位真实性三问。F ≤ 2.0 停下告知不建议申请;F > 2.0 直接进简历生成。

---

## 输出与编译

**输出目录**:每个岗位一个文件夹 `output/[Company]_[Role]/`,先建文件夹再写文件。

**编译**(仓库根执行;compile_cv.py 自动选引擎:文件名含 `CL_` 或 `CV_CN` 用 xelatex,其余 .tex 用 pdflatex,.html 用 Chrome headless):

```bash
python compile_cv.py output/[Company]_[Role]/[Your_Name]_CV_[Role].tex
python compile_cv.py output/[Company]_[Role]/[Your_Name]_CL_[Role].tex
python compile_cv.py output/[Company]_[Role]/[Your_Name]_CV_[Role].html
```

依赖:MiKTeX 或 TeX Live 在 PATH(或仓库根放 `miktex_install/` 便携版);HTML 编译需本机 Chrome/Edge。

**验证**:PDF 非零字节,且 LaTeX log 以 `Output written on ... (1 page).` 结尾。

**清理**(验证 PDF 后立即执行,只留 .pdf 与中文简历的 .html):

```bash
rm -f output/[Company]_[Role]/*.{tex,aux,log,out,synctex.gz,fls,fdb_latexmk,xdv}
```

---

## 命令

| 命令 | 作用 | 终点 |
|---|---|---|
| `/hunt` | 四渠道扫描 → 资格核验 → F 初评 → 两档报告 | 报告为止,用户挑岗 |
| `/apply <JD>` | JD 评分 → 定制中文简历 → 浏览器填表 → 截图 | 停在提交前,用户亲手提交 |

## 全局格式规则

- 全部输出禁用 em dash;分隔用冒号/逗号/双连字符 ` -- `
- 信息不确定就问用户或标"待核",不猜
