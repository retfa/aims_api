def Exclude_Fields(data_list, fields_to_exclude):
    """
    从字典列表中移除指定的字段。

    :param data_list: List[Dict] - 要处理的字典列表
    :param fields_to_exclude: List[str] - 要排除的字段列表
    :return: List[Dict] - 处理后的字典列表
    """
    return [
        {k: v for k, v in item.items() if k not in fields_to_exclude}
        for item in data_list
    ]