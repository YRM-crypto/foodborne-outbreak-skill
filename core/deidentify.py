"""输出边界的简单脱敏。默认关闭，由 config.DEIDENTIFY 控制。"""
import re

_PATTERNS = [
    (re.compile(r"\d{17}[\dXx]"), "[脱敏:身份证]"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[脱敏:电话]"),
    (re.compile(r"[一-龥]{2,4}(?=\s*(先生|女士|同志))"), "[脱敏:姓名]"),
    (re.compile(r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]?[A-Z]\w{5,6}"), "[脱敏:车牌]"),
]


def scrub(text):
    if not text:
        return text
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
