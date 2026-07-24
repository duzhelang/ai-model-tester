# AI 模型连通性测试工具

一站式测试各种 AI 模型 API 连通性的轻量工具。支持网页界面和命令行两种模式，内置粘贴自动识别、批量测试、提供商管理等功能。

## 功能特性

- **粘贴自动识别**：粘贴任意配置文本，自动提取 API 地址、Key、模型名
- **手动测试**：输入任意 OpenAI 兼容 API 地址进行单模型连通性测试
- **批量测试**：一键测试多个提供商的所有模型，结果分组汇总
- **提供商管理**：支持添加、编辑、删除提供商配置，配置自动保存到浏览器
- **预设配置**：内置 OpenRouter、智谱AI、DeepSeek、Kimi、NVIDIA NIM 等预设
- **智能错误分析**：区分认证失败、权限不足、模型下线、网络超时、DNS 解析失败等错误类型
- **端口自动切换**：默认端口被占用时自动寻找可用端口，检测已有实例避免重复启动
- **零外部依赖前端**：纯 HTML/CSS/JS，无框架依赖

## 快速开始

### 安装依赖

```bash
pip install requests pyyaml
```

### 启动工具

**Windows 双击启动：**
```
启动测试工具.bat
```

**命令行启动：**
```bash
python ai_tester_web.py
```

启动后浏览器会自动打开 `http://localhost:8765`。

### 命令行版本

```bash
# 测试所有提供商
.\scripts\test-ai-models.ps1

# 快速测试（每个提供商只测默认模型）
.\scripts\test-ai-models.ps1 -Quick

# 测试指定提供商
.\scripts\test-ai-models.ps1 -Provider zhipu
.\scripts\test-ai-models.ps1 -Provider deepseek
.\scripts\test-ai-models.ps1 -Provider openrouter
```

## 项目结构

```
ai-model-tester/
├── ai_tester_web.py          # 网页版服务端（推荐）
├── index.html                # 网页界面（HTML/CSS/JS 一体化）
├── ai_tester.py              # 命令行版本
├── config_parser.py          # YAML 配置解析器
├── model_tester.py           # API 测试核心逻辑
├── report_generator.py       # 测试报告生成器
├── quick_test.txt            # 快速测试用例（可直接复制粘贴）
├── config_example.yaml       # 配置文件示例
├── 启动测试工具.bat           # Windows 双击启动脚本
└── requirements.txt          # Python 依赖
```

## 网页界面功能

### 手动测试（默认标签页）

1. **粘贴自动识别区**：在顶部文本框粘贴任意配置内容，自动识别并填入表单
2. **快速模型选择**：点击预设按钮一键填充对应提供商的配置
3. **手动输入**：API 地址、模型名称、API Key、超时时间
4. **测试结果**：显示连通状态、响应时间、HTTP 状态码、错误类型、解决建议

### 批量测试

1. 选择要测试的提供商（支持全选/反选）
2. 点击"测试全部"一键运行
3. 结果按提供商分组展示，含成功率统计
4. 配置管理支持导入导出 JSON

### 粘贴识别支持的格式

| 格式 | 示例 |
|------|------|
| 裸 Key | `sk-or-v1-xxxx`、`nvapi-xxxx` |
| YAML 配置 | `ZHIPU_API_KEY: 1a0d...` |
| 模型名 | `glm-4-flash`、`deepseek/deepseek-v4-flash:free` |
| URL | `https://open.bigmodel.cn/api/paas/v4` |
| 反引号包裹 | `` `https://...` `` |
| 带注释 | `sk-xxx # 这是注释` |
| ${} 变量 | `${ZHIPU_API_KEY:1a0d...}` |

## 内置提供商配置

| 提供商 | 免费模型 | API 地址 |
|--------|----------|----------|
| **OpenRouter** | gemma-4, qwen3-next, deepseek-v4-flash, kimi-k2.6, llama-4-scout, minimax-m2.5, qwen3-coder | `https://openrouter.ai/api/v1` |
| **智谱AI** | glm-4-flash, glm-4.7-flash, glm-4.6v-flash | `https://open.bigmodel.cn/api/paas/v4` |
| **DeepSeek** | deepseek-v4-flash, deepseek-v4-pro | `https://api.deepseek.com` |
| **Kimi** | kimi-k2.5, kimi-k2.6 | `https://api.moonshot.cn/v1` |
| **NVIDIA NIM** | glm-5, deepseek-v4-flash, kimi-k2.6, qwen3-coder-next, llama-4-scout 等 | `https://integrate.api.nvidia.com/v1` |
| **小米 MiMo** | mimo-v2.5, mimo-v2.5-pro | `https://api.xiaomimimo.com/v1` |
| **千问** | qwen3.6-plus, qwen-turbo（通过 OpenRouter） | `https://openrouter.ai/api/v1` |

## 错误类型说明

| 错误 | 含义 | 排查建议 |
|------|------|----------|
| **认证失败 (401)** | API Key 不正确 | 检查 Key 是否正确或已过期 |
| **权限不足 (403)** | Key 无权访问该模型 | 检查 Key 对应的权限范围 |
| **模型不存在 (404)** | 模型名称错误或已下线 | 核实模型 ID 是否正确 |
| **频率限制 (429)** | 调用频率超限 | 稍后再试或降低请求频率 |
| **网络超时** | 响应过慢 | 检查网络，境外服务可能需要代理 |
| **DNS 解析失败** | 域名无法解析 | 检查 API 地址是否正确 |
| **SSL 证书错误** | 安全连接失败 | 可能需要代理或证书问题 |
| **服务不可用 (503)** | 服务器端故障 | 等待服务恢复 |

## 配置文件

### 创建配置

```bash
# 复制示例配置
cp config_example.yaml config.yaml

# 编辑配置，填入你的 API Key
```

### 快速测试文本

`quick_test.txt` 包含所有提供商的测试用例，格式为每 3 行一组：
```
API地址
APIKey
模型名
```

直接复制粘贴到工具的粘贴区即可自动识别。

## 技术实现

- **后端**：Python `http.server.ThreadingHTTPServer`，多线程处理请求
- **前端**：纯 HTML/CSS/JavaScript，单文件无依赖
- **端口管理**：自动检测 8765-8799 范围内的可用端口，避免重复启动
- **配置持久化**：浏览器 `localStorage` 保存用户自定义配置

## 许可证

MIT License
