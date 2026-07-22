# AIMS API 專案代理與架構規範

## 適用範圍

- 本檔案適用於此儲存庫根目錄及所有子目錄。
- 本專案是 AIMS／MES 相關 Python Web API，會存取多個 Microsoft SQL Server（MSSQL）資料庫，並整合 Redis、LDAP、SocketIO 與背景任務。
- `C:\Project\@Web\Api2` 是待遷移的既有 Flask 系統，只作為公開 API 契約、商業邏輯與資料存取行為的來源；本儲存庫的 FastAPI 應用程式是唯一目標系統。
- Api2 整合完成並通過驗收後，正式流量應由本專案完整接管，不長期維持兩套可獨立演進的 API。

## 文件語言、編碼與刪除限制

- 所有 Markdown 文件一律使用繁體中文 `zh-TW` 與 `UTF-8` 編碼。
- 技術名詞、套件名稱、程式識別字、命令、路徑與 API 名稱可保留英文。
- 禁止批量刪除檔案或目錄。
- 不得使用 `del /s`、`rd /s`、`rmdir /s`、`Remove-Item -Recurse` 或 `rm -rf`。
- 需要刪除時，一次只能刪除一個已確認的明確檔案路徑。
- 若工作需要批量刪除，必須停止並請使用者手動處理。
- 不得覆寫、回復或刪除無法確認來源的既有修改。

## 架構定位

本專案採用模組化單體與 Ports-and-Adapters 四層架構。Application Service 即 Use Case 層；它可以協調流程與交易，但不得承擔 HTTP、SQL、驅動或部署設定細節。

| 層級 | 目錄 | 責任 |
|---|---|---|
| API | `app/api/` | FastAPI Router、SocketIO 事件邊界、輸入驗證、HTTP 狀態碼、權限入口與 OpenAPI |
| Application | `app/application/` | Use Case、交易流程、跨 Repository 協調與 Port 定義 |
| Domain | `app/domain/` | Entity、Value Object、Enum、領域規則與領域例外 |
| Infrastructure | `app/infrastructure/` | 多 MSSQL／Redis／LDAP／外部系統、Repository、Unit of Work、資料映射、連線與設定實作 |

其他目錄責任：

- `app/contracts/`：Pydantic request／response model、舊 API 相容契約與共用 API schema。
- `app/composition.py`：Application Port 與 Infrastructure 實作的唯一組裝點。
- `app/main.py`：建立 FastAPI／ASGI app、lifespan、middleware 與 Router 註冊，不放商業邏輯。
- `tests/`：架構、契約、Use Case、Domain、Infrastructure 與 Api2 差異測試。
- `docs/` 或 `specs/`：架構決策、Api2 遷移清冊、設定契約與維運文件。

允許的主要依賴方向：

```text
API → Application → Domain
Infrastructure → Application Port、Domain
Contracts → Domain
Composition → Application、Infrastructure
```

分層限制：

- `app/api/` 不得直接匯入 Infrastructure、Repository、SQLAlchemy engine、`pyodbc`、Redis client 或處理資料庫交易。
- `app/application/` 不得依賴 API 或 Infrastructure，只能透過 Port 使用資料庫、Redis、LDAP、排程及外部系統。
- `app/domain/` 必須是純 Python，不得依賴 FastAPI、Pydantic、SQLAlchemy、`pyodbc`、Redis 或 Infrastructure。
- SQL、資料列映射、ORM model、Cache key 與外部系統整合只能存在 Infrastructure。
- Infrastructure 必須實作 Application 定義的 Port，不得要求 Application 依賴具體 Repository、連線名稱或驅動。
- 不新增只有轉呼叫、沒有 Use Case、交易、驗證或協調責任的 Service、BLL、Manager、Provider 或 Wrapper。
- 不得為了共用程式而建立可無限制依賴的 `common.py` 或 `utils.py`；共用能力必須有明確所屬層與責任。

## 業務模組邊界

新程式應依業務能力分組，而不是依資料庫主機或資料表分組。目標模組至少包含：

- `identity_access`：登入、JWT、使用者、選單與權限。
- `mes`：MES 查詢、能源、地磅、派車與生產紀錄。
- `green_zone`：GreenZone 查詢、品質、預測與收藏。
- `costing`：CostSheet、塗佈重量與成本分析。
- `workplace`：員工訂餐、客飯與 WSP。
- `operations`：健康檢查、Redis 管理、系統狀態與背景任務入口。
- `quality`：Skyeye、Wintriss、AUG、紙張品質與 BI／ESG 報表。

每個模組仍須遵守 API、Application、Domain、Infrastructure 的依賴方向。模組之間透過明確 Application Port、Domain 型別或事件協作，不得直接匯入另一模組的 Repository 或資料庫連線。

## 既有目錄的過渡規則

目前的 `app/routers/`、`app/services/`、`app/resources/`、`app/BLL/`、`app/DAL/`、`app/Model/`、`app/Kernel/` 與 Notebook 是過渡區，不是新架構範本。

- 既有程式可進行必要的錯誤修正、安全修正與相容性修正。
- 新業務能力不得繼續擴充舊式 BLL／DAL／resources 分層，應放入新四層架構。
- 遷移一個 Use Case 時，應搬移完整垂直切片：契約、Application Port／Service、Domain 規則、Infrastructure 實作與 API。
- 不允許只搬 Router 而繼續把新商業邏輯塞進大型 `resources` 檔案。
- `.py` 是正式執行原始碼；Notebook 只可作為分析或探索用途，不得作為同一模組的第二份正式來源。
- 遷移期間不進行與該 Use Case 無關的全域重新命名、格式化或清理。

## API 層規則

- Router 只處理 HTTP／SocketIO 邊界，商業流程交由 Application Service。
- 所有 request／response 必須使用明確的 Pydantic model；不得直接公開 ORM、資料庫 row、Pandas DataFrame 或任意 `dict[str, Any]`。
- 新增或修改路由時，必須同步維護 OpenAPI 的 `summary`、`description`、參數、response model 與錯誤回應。
- HTTP 狀態碼與錯誤格式必須一致；Domain 或 Application 例外在 API 邊界轉換。
- 新設計的 API 使用版本化路徑，例如 `/api/v1`；Api2 舊路徑則透過相容 Router 或 Response Adapter 保留。
- 不得以回應 body 內的 `status_code` 取代真實 HTTP status；舊 API 若有此契約，可以同時保留欄位與正確 HTTP status。
- API 不得讀取 `connections.json`、環境變數或祕密檔案。
- 稽核 Header 不等同身分驗證；不得只憑 `X-User-Id`、`X-Site-Code` 等用戶輸入授權。

## Application 與 Domain 規則

- 每個 Application Service 方法必須代表明確 Use Case。
- 寫入 Use Case 必須透過 Unit of Work Port 明確決定 commit／rollback；查詢不得產生隱性寫入。
- 跨 MSSQL 資料庫或 MSSQL＋Redis 的流程必須明確定義一致性策略，不得假設不同資料來源共用單一原子交易。
- Application 不得使用實體資料庫名稱、Connection Profile、SQL、Redis key、FastAPI Request 或 HTTP Response。
- Port 優先使用 Domain 型別、專用 DTO 或明確 Contract；現有任意 dict 只視為過渡設計，不得擴散。
- 可重複使用的商業判斷放在 Domain Rule，不得散落於 Router、Application Service 或 Repository。
- 多狀態欄位使用 Enum 或 Value Object，避免持續增加互斥的布林旗標。

## Infrastructure、資料庫與交易規則

- Repository 只負責資料存取與映射，不放 HTTP 邏輯或跨 Use Case 商業流程。
- 所有 SQL 值必須參數化；資料表、欄位與排序方向等無法參數化的識別字必須使用白名單。
- 同一 Use Case 的多筆異動必須透過 Unit of Work 共用交易。
- Connection、Session、Cursor 與 Unit of Work 必須在成功及例外路徑正確關閉，不可跨 Request 共用可變連線或交易狀態。
- 同步 SQLAlchemy／`pyodbc` 呼叫維持同步邊界，不得包裝成阻塞事件迴圈的假非同步程式。
- SQLAlchemy 統一採 2.x 交易語意；禁止隱式 autocommit、`execute()` 關鍵字參數與已移除的 1.x API。
- Engine／pool 可以由應用程式生命週期共用；Session／Connection 不可作為 module-level singleton。
- 每個 MSSQL canonical profile 擁有獨立 Engine／pool；Repository 必須明確綁定一個 profile，不得在方法內依 Request 資料任意切換實體資料庫。
- 一個 Unit of Work 原則上只管理一個 MSSQL profile 的本機交易；跨 profile 流程不得把數個獨立 commit 包裝成「單一交易」的假象。
- 預設不導入 MSDTC／兩階段提交。跨 MSSQL 的重要寫入使用冪等操作、明確執行順序、狀態紀錄、補償動作，或由 Transactional Outbox＋worker 完成最終一致性。
- 長時間工作不得佔用 HTTP request；應使用具備冪等、狀態與失敗處理的 queue／worker。

## connections.json 與連線設定

- 資料庫密碼、完整連線字串與可直接連線正式環境的預設值不得進入原始碼、Git、log、回應、測試資料或打包產物。
- 正式祕密由環境變數、部署平台 Secret 或受 ACL 保護的外部掛載提供。
- 儲存庫只可追蹤 `connections.schema.json`、`connections.example.json` 與 `.env.example` 等不含真實值的契約文件。
- 若部署使用 `connections.json`，它只作為外部掛載的非機密連線拓撲與 profile 設定，不得內含密碼。
- 建立 Infrastructure 內部的 `MssqlConnectionRegistry` 管理多個 MSSQL profile；另以 `RedisClientProvider` 管理 Redis client／pool。Application 與 API 不得直接使用這兩者。
- MSSQL 與 Redis profile 使用穩定的邏輯名稱，例如 `identity_read`、`mes_write`、`green_zone_read`、`cache_default`、`socketio_bus`；不得以實體主機名稱作為新程式介面。
- `connections.json` 必須以 `mssql` 與 `redis` 分區，不將 Redis 偽裝成關聯式資料庫 connection，也不讓 SQL Repository 取得 Redis client。
- 每個 profile 至少定義 `purpose`、`required` 與所引用的環境變數名稱；MSSQL 可另定義 driver、pool、timeout、唯讀／讀寫用途，Redis 可另定義 DB index、TTL 預設值與 cache／queue／lock／SocketIO bus 用途。
- Api2 `ConnectionStrings` 與目前平面 alias 可由 Infrastructure 相容 Adapter 解析；舊 alias 只作為遷移映射，不得擴散到新程式。
- 多個 alias 指向同一 canonical profile 時，只建立一組 engine／pool。
- Engine 採 lazy creation，並在 lifespan shutdown 統一 dispose。
- MSSQL 與 Redis pool 都必須有全系統連線預算；不得無條件沿用每個資料庫 `pool_size=20`、`max_overflow=30`，也不得以 worker 數量無限制放大總連線數。
- `required=true` 的 MSSQL／Redis profile 參與 readiness；選用 profile 按需連線，單一選用依賴失敗不得讓所有 API 無法啟動。
- 應依用途區分唯讀與讀寫帳號，API 不使用資料庫管理員權限。

連線 Registry／Provider 是 Infrastructure 實作細節，正確依賴方式為：

```text
API → Application Service → UnitOfWork／Repository Port
                                      ↑
Infrastructure UnitOfWork／Repository → MssqlConnectionRegistry → MSSQL Driver

API → Application Service → Cache／Queue／Lock Port
                                      ↑
             Infrastructure Adapter → RedisClientProvider → Redis Driver
```

## 設定與 Composition

- 設定解析放在 Infrastructure config；Domain 與 Application 不直接讀檔案或環境變數。
- `app/composition.py` 是連接 Application Port 與 Infrastructure 實作的唯一位置。
- `app/main.py` 只建立 app、lifespan、middleware、Router 與 Composition，不建立散落各 Router module 的全域 service。
- 共享物件必須有明確生命週期與併發策略；不得用可變 Singleton 保存 Request、使用者、站別、權限或交易狀態。
- 啟動時驗證必要設定；缺少必要祕密不得使用弱預設值繼續運行。
- CORS 必須來自統一設定來源，不得在 `main.py` 硬編碼局部清單。

## 認證、授權與安全

- 建立單一 Current Principal／認證依賴，支援遷移期所需的既有 JWT Cookie 與 Bearer header。
- 除登入、liveness 與明確列入公開清單的端點外，所有 Router 預設要求認證。
- 認證只證明身分；使用者、權限、Redis、排程及其他敏感操作仍須通過明確授權政策。
- 密碼必須使用適當的密碼雜湊；禁止新增明文密碼儲存、比較或固定重設密碼。
- JWT、密碼、API Key、私鑰、Cookie、連線字串及資料庫憑證不得寫入 log、測試快照或版本控制。
- Cookie 必須依環境設定 `HttpOnly`、`Secure`、`SameSite`、有效期限與登出清除行為。
- Redis 管理與模糊／全部刪除能力不得作為一般公開 API；正式環境應預設停用高破壞性操作。
- 登入、權限變更、排程觸發、Redis 管理及敏感資料異動必須記錄不含祕密的結構化稽核資料。
- 對外錯誤不得暴露 SQL、連線資訊、內部路徑或 stack trace。

## Api2 整合規則

- 禁止將 `C:\Project\@Web\Api2` 整個複製或直接 Git merge 到本儲存庫。
- 每次開始遷移前記錄 Api2 來源 commit、工作樹差異與端點清冊，保護兩邊未提交修改。
- 只遷移 Api2 已註冊且可到達的 HTTP／SocketIO 行為，以及這些行為實際依賴的 BLL、DAL、Model 與 Kernel 程式。
- 不搬入 `.git`、`.venv`、`build`、`dist`、`__pycache__`、`.pyc`、log、IDE 設定、真實設定檔或祕密。
- Api2 Controller 的 URL、method、參數名稱與大小寫、status、body、cookie、header、CORS 與 SocketIO event 是相容性基準。
- Api2 商業邏輯與 SQL 是遷移參考，不代表可直接覆蓋本專案已修正的同名 BLL／DAL。
- 同名檔案必須逐 Use Case／方法比較，不得以整檔複製決定勝出版本。
- Flask、flask-restx、Flask-SocketIO 與 `current_app` 不得進入目標架構；Web 邊界改為 FastAPI 與 `python-socketio` ASGI。
- 必須保留 `/message`、`/json_message`、`/broadcast_message` 的既有 SocketIO namespace 與事件契約；背景 task 在 disconnect 時必須可取消。
- 先以差異契約測試確認 Api2 與 FastAPI 行為，再將 Router 註冊至正式 app。
- 寫入端點不得對正式資料庫做雙寫比對；使用隔離測試資料庫或明確 rollback。
- 安全修正優先於錯誤的遷移現況；不得為了維持未認證的 FastAPI 回歸而取消 Api2 原有 JWT 驗證。

## 回應相容與版本策略

- Api2 舊路徑在接管期間保持可用；既有前端不應被迫一次全面改版。
- 舊 response envelope 可由明確的 Legacy Response Adapter 保留，不得散落複製在每個 Router。
- 新 `/api/v1` 契約使用一致的 HTTP status、錯誤模型、分頁與欄位命名。
- `/swagger`、`/swagger.json`、登入 alias、健康檢查與下載文件等既有入口若仍有呼叫方，必須提供相容路由或明確淘汰程序。
- 相容性例外、淘汰期限與呼叫方必須記錄在遷移清冊，不可只留程式註解。

## SocketIO、Redis 與背景任務

- SocketIO 事件處理器屬於 API 邊界；事件內的商業流程仍呼叫 Application Service。
- 多 worker 的 SocketIO broadcast 使用具備生命週期管理的外部 manager，不使用 process-local 全域 dict 作為跨 worker 狀態。
- 每個 client 的背景 task 必須可追蹤、可取消，disconnect 後不可繼續無限迴圈。
- Redis key、序列化與快取失效策略屬於 Infrastructure；Application 只透過 Cache／Queue Port 使用。
- Redis 不是 MSSQL 交易的一部分。資料庫寫入成功後才進行快取失效／更新；Redis 失敗不得回滾或偽裝回滾已提交的 MSSQL 交易。
- 需要保證事件最終送達時，先在同一 MSSQL 交易寫入 Outbox，再由 worker 重試發送至 Redis queue／pub-sub；不得直接依賴「先寫 MSSQL、再寫 Redis」的無紀錄雙寫。
- Redis key 必須包含應用程式、環境、用途及版本命名空間，設定明確 TTL；禁止不同環境或不同資料型別共用無命名空間的 key。
- 任務觸發必須具備授權、冪等 key、執行狀態、逾時、失敗資訊及重試策略。

## Logging、健康檢查與可觀測性

- 使用結構化 logging，至少包含 request／correlation ID、路由、HTTP method、status、耗時與不含祕密的身分識別。
- 不使用 `print()` 作為正式 logging，不把可變執行 log 寫入儲存庫。
- 提供 `GET /health` 相容端點、`GET /health/live` 與 `GET /health/ready`。
- liveness 不連外部系統；readiness 只檢查必要依賴，且不得回傳 hostname、帳號、連線字串或底層例外全文。
- 資料庫 pool、查詢耗時、錯誤率、Redis 與背景任務狀態應可被監控。
- 不得在 module import 階段啟動 server、建立所有資料庫連線或執行商業工作。

## 測試與驗證

- 優先建立 `tests/test_architecture.py`，檢查四層 import 方向及禁止依賴。
- Route 行為、OpenAPI 契約、認證授權、Use Case、Domain Rule、Repository 映射、Unit of Work 與設定解析必須有自動化測試。
- Api2 遷移必須有差異契約測試，涵蓋 URL、method、query／body、status、body、cookie、header、CORS 與 SocketIO payload。
- 寫入測試至少驗證成功 commit、例外 rollback、稽核資料與重複／衝突處理。
- 測試不得連正式資料庫、Redis 或 LDAP；使用 dependency override、fake、測試容器或隔離環境。
- 不可宣稱測試成功，除非已實際執行並確認結果。
- 依異動範圍至少執行：

```powershell
python -m pytest -p no:cacheprovider
python -m compileall -q app tests
```

- 若專案尚未建立測試或缺少必要依賴，必須明確回報，不能以 scratch 腳本或正式資料庫查詢替代自動化測試。

## 部署與打包

- 正式部署以 Docker Compose 管理的 stateless ASGI service 為目標；禁止用 PyInstaller 取代正式 container 部署。
- PyInstaller 只作為遷移期或特定離線環境相容方案，不能內嵌真實設定或祕密。
- 設定以環境變數、Secret 或 bind mount 提供；image 不內嵌正式 `connections.json`、`security.json` 或 `.env`。
- Log 使用 stdout 與受管理的 volume／collector，不依賴 container 本地狀態。
- Docker／Compose 必須設定健康檢查、明確 image 版本、必要 network 與 restart policy。
- API 必須保持可水平擴充；SocketIO、Cache、Lock 與背景任務不得依賴單一 process 記憶體。
- 架構、公開 API、設定契約、資料庫行為或部署方式變動時，必須同步更新 `docs/`、`specs/` 或資料庫文件。

## 修改與工作原則

- 優先正確性、安全性、可讀性、可維護性與可測試性；效能最佳化必須有量測依據。
- 優先小步、可回退的修改，一次遷移一個可驗收的 Use Case 或模組。
- 先搜尋相關 Router、Contract、Service、Port、Repository、SQL、設定與測試，再開始修改。
- 避免掃描 `.git/`、虛擬環境、cache、`__pycache__/`、build、dist 與產物目錄。
- 優先修改或擴充責任正確的既有元件，不建立用途重複的抽象或文件。
- 完成回報只陳述實際修改、實際執行的驗證與仍存在的風險。
