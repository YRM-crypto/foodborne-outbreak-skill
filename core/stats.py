"""小规模、无依赖的流行病学计算，约定明确。"""
import math
import statistics


def _count(value, name="count"):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} 必须为非负整数")
    return value


def proportion(numerator, denominator):
    _count(numerator, "numerator")
    if denominator is None:
        return {"numerator": numerator, "denominator": None, "value": None, "ci95": None, "reason": "分母未知"}
    _count(denominator, "denominator")
    if numerator > denominator:
        raise ValueError("分子超过分母")
    if denominator == 0:
        return {"numerator": numerator, "denominator": 0, "value": None, "ci95": None, "reason": "分母为零"}
    p = numerator / denominator
    z = 1.959963984540054
    center = (p + z * z / (2 * denominator)) / (1 + z * z / denominator)
    half = z * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator ** 2)) / (1 + z * z / denominator)
    return {"numerator": numerator, "denominator": denominator, "value": p,
            "ci95": [max(0.0, center - half), min(1.0, center + half)], "method": "Wilson score 95% CI"}


def duration_summary(hours):
    if not hours:
        return {"n": 0, "minimum": None, "maximum": None, "median": None, "mean": None, "unit": "hours"}
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x < 0 for x in hours):
        raise ValueError("时长必须为非负有限小时数")
    return {"n": len(hours), "minimum": min(hours), "maximum": max(hours),
            "median": statistics.median(hours), "mean": statistics.mean(hours), "unit": "hours"}


def _fisher_two_sided(a, b, c, d):
    n = a + b + c + d
    row, col = a + b, a + c
    lo, hi = max(0, row - (n - col)), min(row, col)
    if hi - lo > 100000:
        return None
    def logcomb(nn, k):
        return math.lgamma(nn + 1) - math.lgamma(k + 1) - math.lgamma(nn - k + 1)
    def logp(k):
        return logcomb(col, k) + logcomb(n - col, row - k) - logcomb(n, row)
    observed = logp(a)
    return min(1.0, math.fsum(math.exp(lp) for k in range(lo, hi + 1)
                              if (lp := logp(k)) <= observed + 1e-10))


def two_by_two(a, b, c, d, design="cohort", correction=False):
    for name, val in zip("abcd", (a, b, c, d)):
        _count(val, name)
    if design not in ("cohort", "case-control"):
        raise ValueError("仅支持非匹配队列/病例对照")
    out = {"table": [[a, b], [c, d]], "design": design, "n": a + b + c + d, "correction": "none", "warnings": []}
    if min(a + b, c + d, a + c, b + d) == 0:
        out.update(effect=None, ci95=None, p_fisher_two_sided=None, reason="至少一个边际为零")
        return out
    out["p_fisher_two_sided"] = _fisher_two_sided(a, b, c, d)
    vals = [a, b, c, d]
    if 0 in vals:
        out["warnings"].append("存在零单元格")
        if not correction:
            num = a * (c + d) if design == "cohort" else a * d
            den = c * (a + b) if design == "cohort" else b * c
            out.update(measure="RR" if design == "cohort" else "OR",
                       effect=num / den if den else None,
                       effect_status="finite" if den else "infinite" if num else "undefined",
                       ci95=None, ci_method="not estimated: zero cell")
            return out
        vals = [x + 0.5 for x in vals]
        out["correction"] = "Haldane-Anscombe: 所有格 +0.5（仅用于效应与区间）"
    aa, bb, cc, dd = vals
    if design == "cohort":
        effect = (aa / (aa + bb)) / (cc / (cc + dd))
        se = math.sqrt(1 / aa - 1 / (aa + bb) + 1 / cc - 1 / (cc + dd))
        measure = "RR"
        ci_method = "Katz log-Wald 95% CI"
    else:
        effect = aa * dd / (bb * cc)
        se = math.sqrt(sum(1 / x for x in vals))
        measure = "OR"
        ci_method = "Woolf log-Wald 95% CI"
    z = 1.959963984540054
    out.update(measure=measure, effect=effect, effect_status="finite",
               ci95=[math.exp(math.log(effect) - z * se), math.exp(math.log(effect) + z * se)],
               ci_method=ci_method)
    if min(vals) < 5:
        out["warnings"].append("样本稀疏，对数近似区间可能不稳")
    return out
