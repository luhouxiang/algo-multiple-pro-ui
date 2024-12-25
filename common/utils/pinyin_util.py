from pypinyin import pinyin, Style


def get_pinyin_first_letters(text: str) -> str:
    """
    将一段中文文本转换为拼音首字母。例如:
    "菜籽指数" -> "CZZS"
    """
    # pinyin函数会返回嵌套列表，如 [["cài"], ["zǐ"], ["zhǐ"], ["shù"]]
    # 我们只取 style=Style.FIRST_LETTER 来获取首字母
    result = pinyin(text, style=Style.FIRST_LETTER)
    # result 形如 [["c"], ["z"], ["z"], ["s"]]
    # 将其拼接成字符串并大写
    return "".join(item[0] for item in result).upper()



print(get_pinyin_first_letters("菜籽指数"))