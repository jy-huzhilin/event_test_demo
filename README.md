# event_future_1min_demo
这是一个用于测试环境验证“基础数据事件驱动唤醒等待任务”链路的最小 demo 项目。
它依赖分钟线基础表 `cbond.future_hf_1min`，运行时读取最近 10 分钟数据，计算每个标的最新一分钟的 `close - open`，输出一个简单因子。
demo 会额外校验输入数据里必须存在 `time == current_time` 的记录；如果该分钟数据尚未到达，会直接报“基础数据尚未更新到当前时间”。
## 目录结构
- `config.json`：项目配置
- `event_future_1min_demo.py`：因子计算逻辑
- `publish_etl_event.py`：向 Redis 发布基础数据 ready 事件的辅助脚本
## 项目行为
- 输入表：`cbond.future_hf_1min`
- 触发方式：当前分支的事件服务监听 Redis Pub/Sub 消息
- 事件消息格式：
```json
{"table":"cbond.future_hf_1min","value":"2026-04-02 10:30:00","count":131}
```
- 当前分支的监听器默认订阅频道 `ETL`
- 任务执行成功后会输出：
  - `demo__future_minute_spread__1m`
- 该 demo 仅实现 `single` 模式，`batch` 保持为空
## 测试环境验证步骤
### 1. 为基础表补充/确认事件规则
当前 demo 依赖 `basic_data_registry` 中存在 `cbond.future_hf_1min` 的检测规则。可执行：
```sql
INSERT INTO basic_data_registry (
    source_db,
    table_name,
    time_column,
    time_granularity,
    schedule_rules,
    detect_schedule_rules,
    min_rows,
    need_detect,
    provider
) VALUES (
    'basic_data_db',
    'cbond.future_hf_1min',
    'time',
    'timestamp',
    '[{"schedule_time":"****-**-** **:**:00","is_openday":true}]',
    '[{"schedule_time":"****-**-** **:**:00","is_openday":true}]',
    1,
    TRUE,
    'redis'
)
ON CONFLICT (table_name) DO UPDATE SET
    source_db = EXCLUDED.source_db,
    time_column = EXCLUDED.time_column,
    time_granularity = EXCLUDED.time_granularity,
    schedule_rules = EXCLUDED.schedule_rules,
    detect_schedule_rules = EXCLUDED.detect_schedule_rules,
    min_rows = EXCLUDED.min_rows,
    need_detect = EXCLUDED.need_detect,
    provider = EXCLUDED.provider;
```
### 2. 将项目仓库加载到 JadeServe
将本项目推到可访问的 GitHub 仓库后，调用加载接口：
```bash
curl -X POST http://127.0.0.1:19465/api/v2/project/load \
  -H 'Content-Type: application/json' \
  -d '{
    "team": "it",
    "repository_url": "https://github.com/jy-huzhilin/event_test_demo.git",
    "version": "main"
  }'
```
### 3. 先跑一次测试，确保项目状态变为 passed
```bash
curl -X POST http://127.0.0.1:19465/api/v2/test/run \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: hzl' \
  -d '{
    "team": "it",
    "project_name": "event_future_1min_demo",
    "version": "main",
    "start_time": "2026-04-02 10:30:00",
    "end_time": "2026-04-02 10:30:00"
  }'
```
### 4. 创建一条调度任务
这一步会创建一条 `schedule` 任务。若对应分钟线水位尚未 ready，Worker 会把任务移入 `waiting_queue`。
```bash
curl -X POST http://127.0.0.1:19465/api/rerun_schedule \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: hzl' \
  -d '{
    "team": "it",
    "project_name": "event_future_1min_demo",
    "version": "main",
    "current_time": "2026-04-02 10:30:00"
  }'
```
### 5. 发布基础数据 ready 事件
当前分支实际监听的是 Redis Pub/Sub，可直接执行：
```bash
python publish_etl_event.py --business-time "2026-04-02 10:30:00"
```
也可以直接用 `redis-cli`：
```bash
redis-cli -n <redis_db> PUBLISH ETL '{"table":"cbond.future_hf_1min","value":"2026-04-02 10:30:00","count":131}'
```
### 6. 观察预期结果
- 事件服务日志应出现 `cbond.future_hf_1min` 对应水位推进
- 等待队列中的该任务会被 `mark_task_ready()` 移回可执行队列
- Worker 开始执行项目 `event_future_1min_demo`
- 任务完成后可在任务表/日志中看到成功状态
## 推荐观察点
- 事件服务日志：`log/event.log`
- Worker 日志：`log/workers/<worker_id>.log`
- Redis 队列：
  - `jadeserve_waiting_queue`
  - `jadeserve_normal_queue`
  - `jadeserve_processing_queue`
