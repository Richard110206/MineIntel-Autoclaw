# 计算机视觉在矿井安全监测中的大创选题科研调研报告

## 1. 研究主题概述

本报告面向软件工程专业学生，围绕“计算机视觉在矿井安全监测中的大创选题”进行端到端科研调研。建议选题聚焦为：**面向矿井复杂低照环境的轻量化视觉安全隐患识别与预警系统**。研究对象可从“人员 PPE 合规识别、危险区域入侵、人员跌倒/异常姿态、皮带异物、井下移动目标监测”中选择 1-2 个切入点，避免一开始覆盖全部安全监测任务。

该方向的价值在于：煤矿智能化建设正在推进“少人化、无人化、智能化”，国家能源局《煤矿智能化标准体系建设指南》明确提出构建适应煤矿智能化发展的标准体系，并覆盖智能视频、算法平台、平台软件等方向；矿井场景则存在低照度、粉尘、水雾、遮挡、空间狭窄、摄像头部署受限、误报成本高等工程难点。因此，大创项目应强调“可复现算法 + 小规模数据集 + 工程化部署原型 + 风险核验机制”，而不是只做普通目标检测套壳。

## 2. 研判结论摘要

1. 选题可行，但必须收窄目标。推荐优先做“井下人员安全帽/反光服/PPE 合规检测 + 危险区域闯入识别”，因为数据标注、演示视频、YOLO baseline、评价指标和答辩展示都更容易闭环。
2. 技术路线建议采用“YOLOv8/YOLOv10/RT-DETR 等检测模型 + 低照图像增强 + 视频多目标跟踪 + 边缘端轻量化部署”的组合。
3. 创新点不要写成“首次提出计算机视觉用于矿井安全”。更稳妥的创新点是：矿井低照增强与检测联合优化、小目标/PPE 遮挡场景的数据增强、误报分级预警、边缘端实时部署、矿井场景规则引擎。
4. 文献调研显示，中文方向已有机器视觉在煤炭工业、安全监测、井下图像增强、矿井视频目标检测与隐患识别等综述和应用线索；国际方向已有地下煤矿移动目标安全监测、地下矿山行人检测防碰撞综述、地下钻进监测数据集等可参考工作。
5. GitHub baseline 建议只保留一个最贴近场景的仓库：`AyushRajput-cmds/End_to_End_Vision_Based_PPE_Compliance_And_Personal-Monitoring_System_for_Coal_Minning_Environments`。该仓库面向煤矿环境 PPE 合规和人员监测，采用 YOLOv8，适合做大创原型迁移。

## 3. 应用场景概述

### 3.1 人员安全行为监测

识别矿工是否佩戴安全帽、反光服、自救器等 PPE，是否进入危险区域，是否出现跌倒、长时间静止、异常聚集等风险行为。该场景与现有视频监控系统结合紧密，适合软件工程学生做端到端系统原型。

### 3.2 运输与皮带安全监测

识别皮带异物、煤流异常、人员靠近皮带危险区域、运输巷道障碍物等。中文检索中“矿井输送带异物检测”是较常见方向，适合做目标检测、小目标识别和实时预警。

### 3.3 井下移动目标监测

对人员、车辆、装备等移动目标进行检测、跟踪和风险区域判断。Scientific Reports 论文《Safety monitoring method of moving target in underground coal mine based on computer vision processing》就是该方向的重要线索。

### 3.4 多模态隐患识别

融合视频、气体传感器、定位、设备状态等信息，形成更可靠的预警。大创阶段不建议一开始做复杂融合，但可以在系统设计中预留传感器接口，把“视觉检测结果 + 规则引擎”作为第一阶段闭环。

## 4. 矿井特殊技术难点

1. 低照度与强点光源并存：井下照明不均匀，摄像头画面常出现过暗、局部过曝、噪声高。
2. 粉尘、水雾、遮挡：目标边缘模糊，安全帽、人员、车辆可能被遮挡，容易漏检。
3. 小目标与远距离目标：危险区域中的人员或装备在画面中占比小，普通模型容易忽略。
4. 类别边界不清：安全帽、矿灯、头部、反光服在低清图像中容易混淆。
5. 数据难获取：真实井下视频涉及安全、隐私和企业数据权限，大创项目需要公开数据、模拟视频、实验室采集和合成增强结合。
6. 实时性要求：矿井安全监测不能只追求离线 mAP，需要给出 FPS、延迟、误报率、漏报率和边缘端部署方案。

## 5. 中文矿业论文线索

以下为检索线索，正式申报前建议到期刊官网、CNKI、万方或学校图书馆二次核验题名、作者、卷期和 DOI。

| 方向 | 线索 | 来源/链接 | 可用价值 |
| --- | --- | --- | --- |
| 机器视觉综述 | 机器视觉感知理论与技术在煤炭工业领域应用进展综述 | [工矿自动化 PDF](http://www.gkzdh.cn/cn/article/pdf/preview/10.13272/j.issn.1671-251x.2022100087.pdf) | 可作为中文综述主线，说明机器视觉对煤矿安全监测和装备自动化的意义。 |
| 矿井视觉体系 | 矿井视觉计算体系架构与关键技术 | [煤炭科学技术 PDF](https://www.mtkxjs.com.cn/cn/article/pdf/preview/10.12438/cst.2023-0152.pdf) | 可用于阐述矿井视觉计算的体系化框架。 |
| 井下图像增强 | 煤矿井下工业视频图像增强技术研究与分析 | [中国矿业 PDF](http://www.chinaminingmagazine.com/cn/article/pdf/preview/10.12075/j.issn.1004-4051.20240273.pdf) | 支撑低照、粉尘和图像增强问题设置。 |
| 安全帽/PPE | 基于超像素特征与 SVM 分类的人员安全帽分割方法 | [煤炭学报 PDF](https://www.mtxb.com.cn/cn/article/pdf/preview/370c9d8d-84be-4ee4-9139-968df6b15ca0.pdf) | 可作为传统方法与深度学习方法对比的早期线索。 |
| 隐患识别综述 | 矿井视频图像目标检测与隐患识别方法研究综述 | [煤炭科学技术 PDF](https://mtkxjs.com.cn/cn/article/pdf/preview/10.12438/cst.2025-1116.pdf) | 与本选题高度相关，建议重点核验和精读。 |
| 掘进场景 | 机器视觉在煤矿掘进工作面中的应用 | [山西煤炭](http://www.sxmtzz.com/article/doi/10.20120/j.cnki.issn.1671-749x.2026.0527) | 可扩展到掘进工作面视觉安全监测。 |
| 政策与案例 | 全国煤矿智能化建设典型案例汇编（2023 年） | [国家能源局 PDF](http://www.nea.gov.cn/download/%E5%85%A8%E5%9B%BD%E7%85%A4%E7%9F%BF%E6%99%BA%E8%83%BD%E5%8C%96%E5%BB%BA%E8%AE%BE%E5%85%B8%E5%9E%8B%E6%A1%88%E4%BE%8B%E6%B1%87%E7%BC%96%EF%BC%882023%E5%B9%B4%EF%BC%89.pdf) | 用于说明产业背景和工程落地趋势。 |

## 6. 国际前沿线索

| 方向 | 文献/资料 | 链接 | 价值 |
| --- | --- | --- | --- |
| 地下煤矿移动目标 | Safety monitoring method of moving target in underground coal mine based on computer vision processing | [Scientific Reports, 2022](https://www.nature.com/articles/s41598-022-22564-8) | 直接面向地下煤矿移动目标安全监测，可作为核心国际论文线索。 |
| 地下矿山防碰撞 | The Future of Mine Safety: A Comprehensive Review of Anti-Collision Systems Based on Computer Vision in Underground Mines | [Sensors/MDPI, 2023](https://www.mdpi.com/1424-8220/23/9/4294) | 综述地下矿山基于视觉的行人检测/防碰撞系统，适合写研究现状。 |
| 地下钻进数据集 | An open paradigm dataset for intelligent monitoring of underground drilling operations in coal mines | [Scientific Data, 2025](https://www.nature.com/articles/s41597-025-05118-1) | 数据集方向很适合说明“公开数据不足”和“场景数据集建设”的研究价值。 |
| 地下 SLAM/监测 | SubSurfaceGeoRobo: a Comprehensive Underground Dataset for SLAM-Based Geomonitoring with Sensor Calibration | [Springer, 2025](https://link.springer.com/article/10.1007/s41064-025-00361-y) | 可作为地下环境多传感器数据采集和机器人监测参考。 |
| 矿山灾害 AI 风险预测 | Application of Artificial Intelligence in Predicting Coal Mine Disaster Risks: A Review | [Sensors/MDPI, 2025](https://www.mdpi.com/1424-8220/25/21/6586) | 说明 AI 在煤矿灾害风险预测中的综述脉络。 |
| 开采场景视觉综述 | A Review of the Application of Computer Vision Techniques in Sustainable Engineering of Open Pit Mines | [Sustainability/MDPI, 2025](https://www.mdpi.com/2071-1050/17/7/3051) | 虽偏露天矿，但可借鉴视觉监测、设备识别和安全预警思路。 |

## 7. GitHub baseline 推荐

推荐仓库：[`AyushRajput-cmds/End_to_End_Vision_Based_PPE_Compliance_And_Personal-Monitoring_System_for_Coal_Minning_Environments`](https://github.com/AyushRajput-cmds/End_to_End_Vision_Based_PPE_Compliance_And_Personal-Monitoring_System_for_Coal_Minning_Environments)

推荐理由：

1. 场景贴近：仓库描述直接面向 coal mining environments 的 PPE compliance 和 personal monitoring。
2. 技术可迁移：以 YOLOv8 检测人员、安全帽、反光服为核心，适合大创快速复现。
3. 工程闭环清晰：可扩展为视频流输入、检测框输出、风险规则判断、告警日志、Web 可视化面板。
4. 软件工程匹配度高：可以把算法能力封装为服务，并实现数据管理、模型配置、告警记录、前端可视化和测试报告。

迁移建议：

1. 先复现仓库 Demo，记录环境、模型权重、推理速度和示例输出。
2. 建立小规模矿井/PPE 图像数据集，至少标注 person、helmet、vest、danger_zone 四类。
3. 做 3 组对比：原始 YOLOv8、加入低照增强、加入数据增强/小目标策略。
4. 输出工程指标：mAP、Precision、Recall、FPS、单帧延迟、误报样例、漏报样例。

## 8. 导师方向推荐

以下导师为官网检索和校内方向匹配线索，正式联系前需以学院官网最新个人主页为准。

| 姓名 | 学院 | 链接 | 匹配理由 |
| --- | --- | --- | --- |
| 焦文华 | 计算机科学与技术学院/人工智能学院 | [官网主页](https://cs.cumt.edu.cn/info/1148/6469.htm) | 研究方向包含机器视觉、智能矿山、矿山通信等，与本选题高度相关。 |
| 张奎元 | 计算机科学与技术学院/人工智能学院 | [官网主页](https://cs.cumt.edu.cn/info/1147/7192.htm) | 方向包含矿山智能感知、多模融合定位与自主导航，适合视觉感知与井下场景结合。 |
| 柳奉奇 | 计算机科学与技术学院/人工智能学院 | [官网主页](https://cs.cumt.edu.cn/info/1106/7308.htm) | 方向包含视觉大模型、多模态生成、三维重建与补全，可对接视觉模型与数据增强。 |
| 邵志文 | 计算机科学与技术学院/人工智能学院 | [官网主页](https://cs.cumt.edu.cn/info/1097/4482.htm) | 具备机器视觉、图像图形相关背景，适合视觉检测与识别方向咨询。 |
| 周伟 | 矿业工程学院 | [官网主页](https://cese.cumt.edu.cn/info/1109/6248.htm) | 矿业工程与智能矿山应用场景匹配，可补足矿井安全业务问题。 |
| 张超林 | 安全工程学院 | [官网主页](https://safe.cumt.edu.cn/info/1029/12357.htm) | 安全监测与应急管理方向相关，适合把视觉识别落到安全预警需求。 |

## 9. 技术路线

### 9.1 最小可行路线

1. 场景定义：选择“井下人员 PPE 合规 + 危险区域入侵”作为核心任务。
2. 数据准备：公开视频/公开 PPE 数据集 + 自制模拟矿井场景图像 + 少量现场公开视频截图；统一标注为 YOLO 格式。
3. baseline 复现：使用 YOLOv8 训练 PPE/人员检测模型。
4. 低照增强：加入 Gamma、CLAHE、Retinex 或轻量低照增强模块，比较增强前后检测效果。
5. 视频推理：加入 ByteTrack/DeepSORT 或简单 IOU 跟踪，实现人员轨迹和危险区域判断。
6. 告警规则：若人员未佩戴 PPE、进入危险区、连续 N 帧异常，则生成告警记录。
7. 系统原型：后端 FastAPI/Flask，前端展示视频帧、检测框、告警表和统计图。
8. 评估报告：输出模型指标、系统延迟、失败案例和改进计划。

### 9.2 可写入申报书的创新点

1. 面向矿井低照和粉尘环境的数据增强策略。
2. PPE 合规检测与危险区域规则联动的安全预警机制。
3. 轻量化模型部署，面向边缘端视频流实时推理。
4. 面向软件工程的大创交付：数据集、训练脚本、推理服务、可视化界面、测试报告。

### 9.3 风险与替代方案

1. 若真实矿井数据不足，可用公开 PPE/工地安全数据集和模拟矿井视频替代，但要在报告中说明“场景迁移验证不足”。
2. 若模型效果一般，优先改进数据标注质量和场景增强，不急于堆复杂模型。
3. 若边缘部署困难，可先在笔记本 GPU/CPU 完成实时性测试，再设计边缘端部署方案。

## 10. 科研经验参考

知乎/小红书等经验内容只作为项目推进参考，不作为论文或技术事实依据。结合检索结果，建议：

1. 申报书要把问题讲具体：不要写“智慧矿山安全监测系统”，而写“井下低照环境下人员 PPE 合规与危险区域入侵识别”。
2. 任务拆解要可验收：数据集、baseline、模型改进、系统原型、实验报告分别对应中期和结题材料。
3. 答辩重点不是模型名字，而是“为什么矿井难、你怎么处理低照/粉尘/遮挡、误报漏报怎么评估、系统如何落地”。
4. 项目周期建议按 12 周规划：第 1-2 周调研和数据；第 3-5 周复现 baseline；第 6-8 周改进和对比；第 9-10 周系统原型；第 11-12 周报告和答辩材料。

## 11. 搜索路径溯源

本次端到端测试使用了以下路径：

1. 本地矿井应用知识图谱：检索“计算机视觉 矿井安全监测 痛点 解决方案 技术设备”，得到瓦斯监测监控、顶板与矿压监测、大型固定设备运维、AI 大模型赋能等场景线索。
2. 中文论文检索：检索“计算机视觉 矿井安全监测 煤矿 矿井 论文 2024 2025 2026”“计算机视觉 矿井安全监测 煤炭学报 工矿自动化 煤炭科学技术”。
3. 国际论文检索：检索“computer vision underground mining safety monitoring underground mining safety monitoring paper”“computer vision underground mining safety monitoring intelligent mining review survey”。
4. GitHub baseline：检索“YOLOv8 coal mine safety helmet detection”，保留最贴近煤矿 PPE 合规监测的 1 个仓库。
5. 导师匹配：优先限定中国矿业大学徐州官网域名，包括 `cs.cumt.edu.cn`、`cese.cumt.edu.cn`、`safe.cumt.edu.cn` 等。
6. 科研经验：检索知乎和小红书公开入口，仅用于大创推进、申报和答辩经验参考。

## 12. 最终建议选题

建议申报题目：

**面向矿井低照环境的人员安全装备合规识别与危险区域入侵预警系统**

备选题目：

1. 基于轻量化 YOLO 的矿井人员 PPE 合规检测与边缘端部署研究。
2. 面向矿井安全监测的低照视频目标检测与告警系统设计。
3. 融合低照增强与目标跟踪的井下人员异常行为识别方法研究。

最推荐第一个备选题，因为它和软件工程专业最匹配，既有算法复现，也有系统开发，还能形成可演示原型。
