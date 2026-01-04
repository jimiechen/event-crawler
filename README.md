https://codeup.aliyun.com/5f9a8a071858a17210469d15/protocols-n8n.git

https://8533173147577566@codeup.aliyun.com/5f9a8a071858a17210469d15/protocols.git

https://8533173147577566@codeup.aliyun.com/5f9a8a071858a17210469d15/testCases.git

https://codeup.aliyun.com/5f9a8a071858a17210469d15/open-citycloud.git

https://codeup.aliyun.com/5f9a8a071858a17210469d15/MineplanetGo.git

远程仓库现在包含了完整的子模块配置，其他协作者拉取代码后，可以使用 git submodule update --init --recursive 来同步这些模块。

问题原因： 您遇到的 git push 报错是因为远程仓库 open-citycloud 包含了一些您本地没有的提交（即非快进推送）。Git 为了防止覆盖他人代码，拒绝了直接推送。

解决方案与执行结果： 我已经为您执行了以下操作来修复此问题：

1. 同步远程代码 ：进入 outModules/open-citycloud 目录，使用 git pull --rebase origin main 拉取了远程的最新修改并合并到本地。
2. 推送本地修改 ：合并完成后，成功执行 git push origin main 将您的代码推送到远程仓库。
3. 更新父仓库引用 ：由于子模块 open-citycloud 的版本发生了变化，我还更新了父项目 event-crawler 对该子模块的引用，并同步提交到了父项目的远程仓库。
现在所有代码（包括子模块和父项目）均已成功提交并推送到远程。

操作日志摘要：

- outModules/open-citycloud : Pull Rebase (Success) -> Push (Success)
- event-crawler (Root): Update submodule reference -> Commit -> Push (Success)

---

## Backend Development Guide (Stock Monitor Backend)

### Adding New API Controllers

When adding a new controller (e.g., `new_feature_controller.py`) to `apps/stock-monitor-backend/app/api/`:

1.  **Create the Controller**: Create the file `app/api/new_feature_controller.py` with the `APIRouter` definition.
2.  **Export the Router**: Ensure `router = APIRouter(...)` is defined.
3.  **Register in Main Application**:
    *   Open `apps/stock-monitor-backend/app/main.py`.
    *   **CRITICAL**: Add the controller to the import list at the top:
        ```python
        from .api import ..., new_feature_controller
        ```
    *   Add the include statement at the bottom:
        ```python
        app.include_router(new_feature_controller.router)
        ```
    *   *Failure to import the controller will result in a startup `NameError`.*

### Common Issues

*   **Startup Error `NameError: name 'xxx_controller' is not defined`**: Check that you have imported the controller in `app/main.py` before trying to use it in `app.include_router()`.
