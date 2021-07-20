# settingkit
从配置文件、环境变量加载配置文件

## 注意事项

- 加载顺序（先后顺序）：`默认配置 > 用户配置 | 环境变量`
  - 根据load_settings()、load_enviroment()函数执行先后顺序而定
- 不同的数据类型，其值处理方式不同，如下。
  - `list,tuple`：会自动追加并去重
  - `dict`：更新（参考dict.update()函数）
  - `string`：替换,覆盖

## 示例

示例 1：

```python
import os
from settingkit import settings

os.environ['STK_ITEM_st_test_0'] = "(INT)1"
os.environ['STK_ITEM_st_test_1'] = "(BOOL)0"
os.environ['STK_ITEM_st_test_2'] = "key1=value1&K3=(B)1&K4=(I)1&k2=v21,v22"

st = settings()

st.load_enviroment()

print(st.st_test_0)
print(st.st_test_1)
print(st.st_test_2)
```

示例 2：

```python
from settingkit import settings

global_settings = "config.settings"
user_settings = "config.user_settings"

settings = Settings()
settings.global_settings(global_settings)
settings.load_settings(user_settings)
settings.load_enviroment(prefix="STK_ITEM_")
```

示例 3：

```python
import os
from settingkit import initialize

global_settings = "config.settings"
user_settings = "config.user_settings"
os.environ['STK_ITEM_st_test_0'] = "key1=value1&K3=(B)1&K4=(I)1&k2=v21,v22"

st = initialize(global_settings, user_settings, list_or_tuple_cover=True, dict_cover=True)
print(st.st_test_0)
```
