import json
import pandas as pd

class JsonConverter:
    # 靜態方法 1: 將字典陣列轉換為 JSON
    @staticmethod
    def dict_array_to_json(dict_array):
        return json.dumps(dict_array)

    # 靜態方法 2: 將 JSON 轉換為表格型 JSON
    @staticmethod
    def json_to_table_json(json_data):
        df = pd.read_json(json_data)
        return df.to_json(orient='table', index=False)

    # 靜態方法 3: 將表格型 JSON 轉換回 JSON
    @staticmethod
    def table_json_to_json(table_json):
        df = pd.read_json(table_json, orient='table')
        return df.to_json(orient='records')

    @staticmethod
    def dict_array_to_table_json_dict(dict_array, custom_field_types=None):
        # 將字典陣列轉換成 DataFrame
        df = pd.DataFrame(dict_array)

        # 將 DataFrame 轉換成 JSON 格式的字典
        table_json_dict = df.to_dict(orient='records')

        # custom_field_types = {
        #     "fta_dtm": "DATE",
        #     "relno": "string",
        #     "ptype": "string"
        # }
        # 如果未傳入自定義 field types，則使用預設處理方式
        if custom_field_types is None:
            custom_field_types = {}

        pandas_to_js_datatypes = {
            'object': 'string',
            'int64': 'number',
            'float64': 'number',
            'datetime64': 'Date',
            'timedelta': 'string',
            'bool': 'boolean',
            'category': 'string',
            'datetime': 'Date',
            'float': 'number',
            'int': 'number'
        }
        # 建立 schema
        fields = []
        for col in df.columns:
            # 檢查是否有自定義 field type
            field_type = custom_field_types.get(col, None)
            if field_type:
                fields.append({"name": col, "type": field_type})
            else:
                # 使用映射來轉換欄位類型
                dtype = str(df[col].dtype)
                if dtype in pandas_to_js_datatypes:
                    field_type = pandas_to_js_datatypes[dtype]
                else:
                    field_type = dtype
                fields.append({"name": col, "type": field_type})

        csv_data = df.to_csv(index=False, header=False)
        new_table_json_dict = {
            "schema": {
                "fields": fields
            },
            "data": csv_data.split('\r\n')[:-1]
        }

        return new_table_json_dict

# 範例使用：
# dict_array = [{"name": "John", "age": 30}, {"name": "Alice", "age": 25}]
# json_data = JsonConverter.dict_array_to_json(dict_array)
# print("靜態方法 1 結果:", json_data)

# table_json = JsonConverter.json_to_table_json(json_data)
# print("靜態方法 2 結果:", table_json)

# json_data_again = JsonConverter.table_json_to_json(table_json)
# print("靜態方法 3 結果:", json_data_again)
