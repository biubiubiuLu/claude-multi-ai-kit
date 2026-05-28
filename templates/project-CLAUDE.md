# 项目元信息（供 multi-ai-kit 使用）

# 测试命令（cship 在执行完编码后会跑）
test_command: mvn test

# 构建命令（可选）
build_command: mvn package -DskipTests

# 前端代码所在路径（cship 据此判断"是否涉及前端"）
frontend_paths:
  - src/main/resources/static
  - src/main/webapp

# 排除路径（不让 AI 读 / 改）
exclude_paths:
  - target
  - generated-sources
  - node_modules
  - dist

# 可选：覆盖项目级前端开关
# frontend_enabled: false
