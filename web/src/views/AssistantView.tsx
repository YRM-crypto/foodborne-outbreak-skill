import { RobotOutlined, SendOutlined, UserOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Collapse,
  Empty,
  Input,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { assistantChat, listEvents } from "../api/client";

const { Text, Paragraph, Title } = Typography;

interface Source {
  doc_id: string;
  label: string;
}
interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

const TIPS = ["加载事件档案…", "检索规范依据…", "检索相似案例…", "综合分析…"];

const QUICK_WITH_EVENT = [
  "结合当前数据，最可疑的食品是什么？",
  "该查哪些规范或指南依据？",
  "当前数据有哪些关键发现？",
  "如何完善当前病例定义？",
];
const QUICK_GENERAL = [
  "食源性疾病暴发调查分哪几个阶段？",
  "金黄色葡萄球菌肠毒素的判定标准是什么？",
  "队列研究中如何判定可疑食品？",
];

export default function AssistantView() {
  const { eventId: paramEventId } = useParams();
  const [events, setEvents] = useState<any[]>([]);
  const [eventId, setEventId] = useState<string | null>(paramEventId ?? null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [tipIdx, setTipIdx] = useState(0);
  const [contextMd, setContextMd] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listEvents()
      .then(setEvents)
      .catch((e) => message.error("加载案例失败：" + (e?.message ?? e)));
  }, []);

  useEffect(() => {
    if (!loading) return;
    const t = setInterval(() => setTipIdx((i) => (i + 1) % TIPS.length), 1500);
    return () => clearInterval(t);
  }, [loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (q?: string) => {
    const question = (q ?? input).trim();
    if (!question || loading) return;
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const next: ChatMsg[] = [...messages, { role: "user", content: question }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const res = await assistantChat({ event_id: eventId, question, history });
      setMessages([
        ...next,
        { role: "assistant", content: res.answer, sources: res.sources ?? [] },
      ]);
      if (res.context_md) setContextMd(res.context_md);
    } catch (e: any) {
      const detail = e?.response?.data?.detail ?? e?.message ?? String(e);
      setMessages([...next, { role: "assistant", content: "抱歉，出错了：" + detail }]);
    } finally {
      setLoading(false);
    }
  };

  const quick = eventId ? QUICK_WITH_EVENT : QUICK_GENERAL;

  return (
    <div style={{ maxWidth: 960 }}>
      <Space style={{ width: "100%", justifyContent: "space-between", marginBottom: 12 }} wrap>
        <Title level={4} style={{ margin: 0 }}>
          <RobotOutlined style={{ marginRight: 8 }} />
          AI 调查助手
        </Title>
        <Select
          style={{ width: 380 }}
          value={eventId ?? ""}
          placeholder="选择要咨询的事件"
          onChange={(v) => {
            setEventId(v === "" ? null : v);
            setMessages([]);
            setContextMd(null);
          }}
          options={[
            { value: "", label: "无上下文（通用咨询）" },
            ...events.map((e) => ({ value: e.id, label: `${e.id} · ${e.title}` })),
          ]}
          showSearch
          optionFilterProp="label"
        />
      </Space>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
        message="AI 仅作辅助：确定性指标（罹患率、RR/OR、潜伏期等）已用工具计算，模型不口算；最终结论请由调查员在「证据与结论」中人工确认。"
      />

      {contextMd && (
        <Collapse
          size="small"
          ghost
          style={{ marginBottom: 12 }}
          items={[
            {
              key: "ctx",
              label: "AI 已知上下文（可核查）",
              children: (
                <div
                  className="markdown-body"
                  style={{ background: "#fafafa", padding: "8px 12px", borderRadius: 6 }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{contextMd}</ReactMarkdown>
                </div>
              ),
            },
          ]}
        />
      )}

      <Card bodyStyle={{ padding: 16, minHeight: 360, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, overflow: "auto" }}>
          {messages.length === 0 ? (
            <div style={{ padding: "32px 16px" }}>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <Paragraph style={{ marginBottom: 4 }}>
                      我是你的调查助手，可以帮你查依据、找相似案例、算指标、读当前事件数据。
                    </Paragraph>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      选择上方事件即可「结合本次调查」作答；不选则为通用咨询。
                    </Text>
                  </div>
                }
              />
              <div style={{ textAlign: "center", marginTop: 12 }}>
                <Space wrap>
                  {quick.map((q) => (
                    <Tag
                      key={q}
                      color="blue"
                      style={{ cursor: "pointer", padding: "4px 10px", fontSize: 13 }}
                      onClick={() => send(q)}
                    >
                      {q}
                    </Tag>
                  ))}
                </Space>
              </div>
            </div>
          ) : (
            <div>
              {messages.map((m, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                    marginBottom: 16,
                  }}
                >
                  <div style={{ maxWidth: "82%", display: "flex", gap: 8 }}>
                    {m.role === "assistant" && (
                      <RobotOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />
                    )}
                    <div
                      style={{
                        background: m.role === "user" ? "#1677ff" : "#f5f5f5",
                        color: m.role === "user" ? "#fff" : "inherit",
                        padding: "10px 14px",
                        borderRadius: 8,
                      }}
                    >
                      {m.role === "user" ? (
                        <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
                      ) : (
                        <div className="markdown-body">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                        </div>
                      )}
                      {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            循证来源：
                          </Text>
                          <Space size={4} wrap style={{ marginTop: 4 }}>
                            {m.sources.map((s) => (
                              <Tag key={s.doc_id} color="geekblue" style={{ fontSize: 12 }}>
                                {s.label}
                              </Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                    </div>
                    {m.role === "user" && (
                      <UserOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                  <Spin size="small" />
                  <Text type="secondary">{TIPS[tipIdx]}</Text>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div style={{ marginTop: 12, borderTop: "1px solid #f0f0f0", paddingTop: 12 }}>
          {messages.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <Space wrap>
                {quick.map((q) => (
                  <Tag
                    key={q}
                    color="blue"
                    style={{ cursor: "pointer", fontSize: 12 }}
                    onClick={() => send(q)}
                  >
                    {q}
                  </Tag>
                ))}
              </Space>
            </div>
          )}
          <Space.Compact style={{ width: "100%" }}>
            <Input.TextArea
              autoSize={{ minRows: 1, maxRows: 4 }}
              placeholder="输入问题，回车发送（Shift+Enter 换行）…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={loading}
              onClick={() => send()}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Card>
    </div>
  );
}
