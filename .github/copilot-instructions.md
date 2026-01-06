# GitHub Copilot Instructions for MAAAE Project

## 项目概述

MAAAE 是基于 **MaaFramework** 的白荆回廊自动化小助手。该项目使用**任务流水线（Pipeline）协议**来定义游戏自动化流程，结合图像识别和控制模拟实现自动化操作。

- **主要技术栈**: Python, JSON (Pipeline), MaaFramework
- **核心概念**: Pipeline 节点、识别算法、执行动作
- **GUI框架**: MFAAvalonia (Windows) 或 MaaPiCli (命令行)

---

## Pipeline 协议指南

### 基础结构

Pipeline 配置采用 JSON 格式，由若干节点（Node）构成。每个节点包含：

```jsonc
{
    "节点名": {
        "recognition": "识别算法类型",    // 可选，默认为 DirectHit
        "action": "执行动作类型",         // 可选，默认为 DoNothing
        "next": ["下一个节点", ...],     // 可选，后继节点列表
        "on_error": ["错误处理节点", ...] // 可选，错误时的处理
        // 其他配置字段...
    }
}
```

### 执行流程

1. **任务触发**: 通过入口节点启动任务
2. **顺序识别**: 按 `next` 列表顺序尝试识别每个子节点
3. **首匹配**: 检测到第一个匹配的节点时，立即执行其 `action` 并终止后续检测
4. **迭代处理**: 执行完成后，继续识别当前节点的 `next` 列表
5. **终止条件**: 当 `next` 为空或识别超时，任务完成

### 流程控制特性

#### 1. 节点属性（Node Attributes） - v5.1+

在 `next` 或 `on_error` 中为节点指定额外行为：

**前缀形式**（推荐）:
```jsonc
{
    "A": {
        "next": [
            "B",
            "[JumpBack]C",  // C 执行完后跳回 A，重新识别
            "[Anchor]MyAnchor"  // 引用最后设置的 MyAnchor 锚点
        ]
    }
}
```

**对象形式**:
```jsonc
{
    "A": {
        "next": [
            "B",
            { "name": "C", "jump_back": true },
            { "name": "MyAnchor", "anchor": true }
        ]
    }
}
```

#### 2. 时序控制字段

- `pre_delay`: 识别到动作前的延迟（默认 200ms）
- `post_delay`: 动作后到下一个识别的延迟（默认 200ms）
- `pre_wait_freezes`: 动作前等待画面静止（默认 0，可设置 uint 或 object）
- `post_wait_freezes`: 动作后等待画面静止
- `repeat`: 动作重复次数（默认 1）
- `repeat_delay`: 重复之间的延迟
- `rate_limit`: 每轮识别最低消耗时间（默认 1000ms）
- `timeout`: 识别超时时间（默认 20000ms）

#### 3. 识别和处理限制

- `enabled`: 节点是否启用（默认 true）
- `max_hit`: 节点最多被识别成功的次数（默认无限）
- `inverse`: 反转识别结果（默认 false）

---

## 识别算法（Recognition Types）

### 常用算法

| 算法 | 说明 | 适用场景 |
|------|------|--------|
| **DirectHit** | 直接执行，不识别 | 固定流程 |
| **TemplateMatch** | 模板匹配（找图） | 界面元素精确定位 |
| **FeatureMatch** | 特征匹配 | 抗透视、抗尺寸变化 |
| **ColorMatch** | 颜色匹配（找色） | 单色或纯色区域 |
| **OCR** | 文字识别 | 动态文本识别 |
| **NeuralNetworkClassify** | 深度学习分类 | 固定位置分类 |
| **NeuralNetworkDetect** | 深度学习目标检测 | 任意位置检测 |
| **And** | 逻辑与 | 多条件同时满足 |
| **Or** | 逻辑或 | 多条件任一满足 |

### TemplateMatch 参数示例

```jsonc
{
    "recognition": "TemplateMatch",
    "template": "path/to/image.png",  // 必选
    "threshold": 0.7,                  // 匹配阈值，默认 0.7
    "roi": [100, 100, 200, 200],      // 识别区域 [x, y, w, h]，默认全屏
    "method": 5,                        // TM_CCOEFF_NORMED（推荐）
    "order_by": "Horizontal",          // 排序方式：Horizontal, Vertical, Score
    "index": 0                         // 取第几个匹配结果
}
```

### OCR 参数示例

```jsonc
{
    "recognition": "OCR",
    "expected": "目标文字",            // 支持正则表达式
    "threshold": 0.3,                  // 置信度阈值
    "roi": [0, 0, 0, 0],              // 全屏识别
    "order_by": "Horizontal",
    "only_rec": false                  // 是否仅识别不检测
}
```

### And 组合识别

```jsonc
{
    "recognition": "And",
    "all_of": [
        {
            "sub_name": "icon",
            "recognition": "TemplateMatch",
            "template": "icon.png"
        },
        {
            "recognition": "OCR",
            "roi": "icon",                // 引用上一个识别结果
            "expected": "确认"
        }
    ]
}
```

---

## 执行动作（Action Types）

### 常用动作

| 动作 | 说明 | 关键参数 |
|------|------|--------|
| **DoNothing** | 无操作 | — |
| **Click** | 点击 | `target`, `target_offset`, `contact` |
| **LongPress** | 长按 | `target`, `duration` (ms) |
| **Swipe** | 滑动 | `begin`, `end`, `duration`, `end_hold` |
| **MultiSwipe** | 多点滑动 | `swipes` (array) |
| **Scroll** | 滚轮滚动 | `dx`, `dy` |
| **ClickKey** | 按键 | `key` (虚拟键码) |
| **InputText** | 输入文本 | `input_text` |
| **StartApp** | 启动应用 | `package` (包名) |
| **StopApp** | 关闭应用 | `package` |
| **StopTask** | 停止任务 | — |
| **Command** | 执行命令 | `exec`, `args`, `detach` |
| **Shell** | ADB Shell命令 | `cmd` |

### Click 参数详解

```jsonc
{
    "action": "Click",
    "target": true,                    // 点击本节点识别位置（自身）
    // OR
    "target": "NodeB",                 // 点击某个前驱节点的识别位置
    // OR
    "target": [100, 200],              // 固定坐标点 [x, y]
    // OR
    "target": [100, 100, 200, 200],   // 矩形区域 [x, y, w, h]（随机点）
    "target_offset": [10, 20, 0, 0],  // 在 target 基础上移动 [dx, dy, dw, dh]
    "contact": 0                       // 触点编号（多点触控）
}
```

### Swipe 参数详解

```jsonc
{
    "action": "Swipe",
    "begin": [100, 200],               // 滑动起点
    "end": [100, 500],                 // 滑动终点
    "duration": 300,                   // 滑动耗时（ms）
    "end_hold": 100,                   // 到达终点后保持时间（ms）
    // 支持折线滑动（v4.5.x+）
    "end": [[100, 300], [100, 500]],  // 多个途径点
    "duration": [150, 150]             // 对应段落耗时
}
```

---

## Pipeline v2 格式（推荐）

v2 格式将识别和动作参数统一为二级结构，增强可读性：

```jsonc
{
    "NodeA": {
        "recognition": {
            "type": "TemplateMatch",
            "param": {
                "template": "icon.png",
                "threshold": 0.7,
                "roi": [100, 100, 200, 200]
            }
        },
        "action": {
            "type": "Click",
            "param": {
                "target": true,
                "target_offset": [10, 10, 0, 0]
            }
        },
        "next": ["NodeB"],
        "pre_delay": 500
    }
}
```

---

## 默认配置（default_pipeline.json）

用于为所有节点设置默认参数，减少重复配置：

```jsonc
{
    "Default": {
        "rate_limit": 1000,
        "timeout": 20000,
        "pre_delay": 200
    },
    "TemplateMatch": {
        "recognition": "TemplateMatch",
        "threshold": 0.7,
        "method": 5
    },
    "Click": {
        "action": "Click",
        "target": true
    }
}
```

**优先级**（从高到低）:
1. 节点中直接定义的参数
2. 对应算法/动作类型的默认参数
3. `Default` 中的通用默认参数
4. 框架内置的默认值

---

## 项目文件结构

```
assets/
├── resource/
│   ├── pipeline/          # Pipeline JSON 文件（核心任务定义）
│   │   ├── wakeup.json    # 启动与登录流程
│   │   ├── main.json      # 主流程
│   │   └── ...
│   ├── image/             # 识别用的图片资源（需为 720p 缩放图）
│   ├── model/             # 深度学习模型文件夹
│   │   ├── ocr/           # OCR 模型
│   │   ├── classify/      # 分类模型
│   │   └── detect/        # 检测模型
│   └── default_pipeline.json  # 默认参数配置
├── config/
│   ├── maa_option.json    # MAA 框架选项
│   └── maa_pi_config.json # MaaPi 配置
└── options/               # 各功能的选项配置
    ├── 作战关卡.json
    ├── 培养同调者.json
    └── ...

agent/
├── main.py                # Python 代理主程序
├── custom/
│   ├── mylevelcheck.py    # 自定义识别示例
│   └── __init__.py
└── utils/
    ├── logger.py
    ├── time.py
    └── __init__.py
```

---

## Python 扩展指南 (Agent 开发)

本项目采用 Agent 架构，Python 端通过 `MaaAgent` 协议运行扩展逻辑。主要负责实现**自定义识别器（CustomRecognition）**和**自定义动作（CustomAction）**。

### 1. 核心模块导入

```python
import json
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context
from utils import logger
```

### 2. 开发自定义识别 (Custom Recognition)

在 `agent/custom/` 目录下新建 Python 文件，并使用 `@AgentServer.custom_recognition` 装饰器注册。

```python
@AgentServer.custom_recognition("MyCustomReco")
class MyCustomReco(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        
        # 1. 获取输入图像和 ROI
        # image 为 numpy.ndarray (H, W, C) BGR 格式
        image = argv.image
        roi = argv.roi  # (x, y, w, h)
        
        # 2. 解析 Pipeline 中传入的参数
        # 对应 JSON 中的 "custom_recognition_param": { "target": 123 }
        try:
            params = json.loads(argv.custom_recognition_param)
            target = params.get("target")
        except:
            target = None

        # 3. 执行识别逻辑 (OpenCV / OCR / etc.)
        # ... 你的代码 ...
        
        # 也可以调用 Context 运行其他 Task/Recognition
        # context.run_recognition("OtherNode", image)

        # 4. 返回结果
        # 成功: 返回 AnalyzeResult 对象，包含 box (x, y, w, h) 和 detail 信息
        # 失败: 返回 box=None
        if success:
            return CustomRecognition.AnalyzeResult(
                box=(x, y, w, h),
                detail="found target"
            )
        else:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail="target not found"
            )
```

### 3. 开发自定义动作 (Custom Action)

同样在 `agent/custom/` 下，使用 `@AgentServer.custom_action` 装饰器。

```python
@AgentServer.custom_action("MyCustomAction")
class MyCustomAction(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        
        # 1. 获取参数
        # box: 上一步识别成功返回的区域
        box = argv.box
        # param: Pipeline 中的 "custom_action_param"
        param = argv.custom_action_param
        
        # 2. 执行操作
        # 可以通过 context 执行其他原子动作，或者使用 Python 库进行操作
        # 注意: 在 Agent 模式下，直接控制设备可能受限，建议通过 context 回调 MaaFramework
        
        # 示例: 在当前位置点击
        # context.run_action("Click", box, "Click from custom action")
        
        logger.info(f"Executing custom action with param: {param}")
        
        # 3. 返回执行结果
        return True
```

### 4. 注册模块

新建的文件需要在 `agent/custom/__init__.py` 中导入才能生效：

```python
from . import my_custom_reco
from . import my_custom_action
```

### 5. 在 Pipeline 中调用

```jsonc
{
    "使用自定义组件的节点": {
        "recognition": "Custom",
        "custom_recognition": "MyCustomReco",
        "custom_recognition_param": { "target": 123 },  // 可选，传递给 analyze 的参数
        
        "action": "Custom",
        "custom_action": "MyCustomAction",
        "custom_action_param": "some_param",           // 可选，传递给 run 的参数
        
        "next": ["下一个节点"]
    }
}
```

---

## 编码最佳实践

### Pipeline 编写规范

1. **节点命名**: 使用清晰的中文名称，格式为 `功能_具体操作`
   ```jsonc
   "启动_进入游戏"
   "通用_确认进入主界面"
   "外勤_任务完成"
   ```

2. **参数复用**: 使用 `default_pipeline.json` 定义通用参数，减少重复

3. **错误处理**: 充分利用 `on_error` 和 `[JumpBack]` 处理异常情况
   ```jsonc
   {
       "main": {
           "next": ["step1", "step2"],
           "on_error": ["handle_error"]
       }
   }
   ```

4. **ROI 优化**: 限制识别区域以提升性能
   ```jsonc
   "roi": [100, 100, 800, 600]  // 明确指定识别范围
   ```

5. **避免深层嵌套**: 保持节点链条相对扁平，使用 `JumpBack` 处理复杂流程

6. **图片资源**: 必须为无损原图缩放到 720p 后的裁剪

### Python 代码规范

1. **日志记录**: 使用 `agent/utils/logger.py` 进行日志记录
2. **自定义识别**: 在 `agent/custom/` 目录实现自定义识别器
3. **模块化**: 将复杂逻辑分离到 `agent/utils/` 目录

### JSON 格式规范

- 使用 4 空格缩进
- 数组元素逐行排列（可参考 prettier-plugin-multiline-arrays）
- 注释使用 `//` (jsonc 格式)
- 避免末尾逗号问题

---

## 常见开发场景

### 场景 1: 添加新功能节点

```jsonc
{
    "新功能_开始": {
        "recognition": "OCR",
        "expected": "新功能按钮",
        "action": "Click",
        "next": ["新功能_处理结果"]
    },
    "新功能_处理结果": {
        "recognition": "TemplateMatch",
        "template": "result.png",
        "action": "Click",
        "next": []
    }
}
```

### 场景 2: 处理多个可能的结果（Or 逻辑）

```jsonc
{
    "检查状态": {
        "recognition": "Or",
        "any_of": [
            {
                "recognition": "OCR",
                "expected": "成功"
            },
            {
                "recognition": "OCR",
                "expected": "失败"
            }
        ],
        "action": "Click",
        "next": ["处理完成"]
    }
}
```

### 场景 3: 条件判断（And 逻辑）

```jsonc
{
    "验证条件": {
        "recognition": "And",
        "all_of": [
            {
                "sub_name": "icon",
                "recognition": "TemplateMatch",
                "template": "icon.png"
            },
            {
                "recognition": "OCR",
                "roi": "icon",
                "expected": "确认"
            }
        ],
        "action": "Click"
    }
}
```

### 场景 4: 错误恢复

```jsonc
{
    "主流程": {
        "next": ["步骤1", "步骤2"],
        "on_error": ["异常恢复", "重试主流程"]
    },
    "异常恢复": {
        "action": "Click",
        "target": [100, 100],  // 点击返回按钮
        "next": []
    }
}
```

---

## 调试建议

1. **启用调试截图**: 配置 `rate_limit` 较小的值，观察每一步的识别结果
2. **查看日志**: 检查 `logs/` 目录下的日志文件
3. **逐步验证**: 单独测试每个关键节点的识别准确性
4. **时序调整**: 根据实际运行速度调整 `pre_delay`、`post_delay`、`timeout` 等参数
5. **图片资源**: 确保模板图片清晰，无损缩放到 720p

---

## 相关资源

- **MaaFramework 文档**: https://github.com/MaaXYZ/MaaFramework
- **项目仓库**: https://github.com/NewWYoming/MAAAE
- **MFAAvalonia GUI**: https://github.com/SweetSmellFox/MFAAvalonia
- **问题反馈**: https://github.com/NewWYoming/MAAAE/issues

---

## 协议版本

本指南适用于 MaaFramework v4.4.0+ (Pipeline v1/v2)，包含 v5.1 新增特性。
