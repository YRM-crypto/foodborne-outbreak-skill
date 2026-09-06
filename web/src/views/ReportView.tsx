import { Card, Empty, Segmented, Select, Space, Spin, Typography, message } from "antd";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listEvents, reportEvent } from "../api/client";

const KINDS = [
  { label: "初步报告", value: "initial" },
  { label: "阶段报告", value: "progress" },
  { label: "结案报告", value: "final" },
];

export default function ReportView() {
  const [events, setEvents] = useState<any[]>([]);
  const [eventId, setEventId] = useState<string>();
  const [kind, setKind] = useState<string>("progress");
  const [md, setMd] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listEvents()
      .then(setEvents)
      .catch((e) => message.error("加载案例失败：" + (e?.message ?? e)));
  }, []);

  useEffect(() => {
    if (!eventId) {
      setMd("");
      return;
    }
    setLoading(true);
    reportEvent(eventId, kind)
      .then((r) => setMd(r.markdown))
      .catch((e: any) =>
        message.error("生成报告失败：" + (e?.response?.data?.detail ?? e?.message ?? e))
      )
      .finally(() => setLoading(false));
  }, [eventId, kind]);

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>
          报告
        </Typography.Title>
        <Select
          style={{ width: 380 }}
          placeholder="选择事件"
          value={eventId}
          onChange={setEventId}
          options={events.map((e) => ({ value: e.id, label: `${e.id} · ${e.title}` }))}
          showSearch
          optionFilterProp="label"
        />
        <Segmented options={KINDS} value={kind} onChange={(v) => setKind(v as string)} />
      </Space>

      {!eventId ? (
        <Empty description="请先选择事件" />
      ) : loading ? (
        <Spin style={{ display: "block", margin: "60px auto" }} />
      ) : (
        <Card>
          <div className="markdown-body" style={{ maxWidth: 920 }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
          </div>
        </Card>
      )}
    </div>
  );
}
