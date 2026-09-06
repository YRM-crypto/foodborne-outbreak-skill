"""助手编排：缺项/相似案例。自然语言锚定结构化来源，模型只解释不计算不抽取。"""
from assistant.client import LLMUnavailable


def render_gaps(gaps):
    lines = ["当前调查缺项与建议："]
    for g in gaps:
        stage = f"（{g['stage']}）" if g.get("stage") else ""
        lines.append(f"- {g['title']}{stage}：{g['why']}。用表：{g['table']}。依据：{g['basis']}")
    return "\n".join(lines)


def render_similar(hits):
    lines = ["检索到以下相似材料（仅供参考，不据此推定本次病因）："]
    for h in hits:
        lines.append(f"- {h['text']}")
    return "\n".join(lines)


SIMILAR_PROMPT = (
    "你是食源性疾病调查助理。根据下面检索到的历史材料片段，用不超过3句话说明："
    "哪些地方与当前事件相似、哪些不同、当时采取了什么调查措施。"
    "不要据此推断当前事件的病因或原因食品。\n当前事件：{query}\n材料：\n{context}")


class Orchestrator:
    def __init__(self, client):
        self.client = client

    def similar(self, query, hits):
        context = "\n".join(h["text"][:500] for h in hits)
        if not getattr(self.client, "enabled", False):
            return render_similar(hits)
        try:
            return self.client.complete([{"role": "user", "content":
                SIMILAR_PROMPT.format(query=query, context=context)}])
        except LLMUnavailable:
            return render_similar(hits)
