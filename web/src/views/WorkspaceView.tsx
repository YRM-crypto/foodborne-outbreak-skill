import { ArrowLeftOutlined } from "@ant-design/icons";
import { Alert, Button, Descriptions, Space, Spin, Steps, Tabs, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { analyzeEvent, loadEvent, timeline } from "../api/client";
import AnalysisPanel from "./workspace/AnalysisPanel";
import DataPanel from "./workspace/DataPanel";
import EvidencePanel from "./workspace/EvidencePanel";
import TracePanel from "./workspace/TracePanel";

const FLOW_NODES = [
  { key: "intake", title: "接报" },
  { key: "definition", title: "病例定义" },
  { key: "plan", title: "调查计划" },
  { key: "analysis", title: "分析" },
  { key: "evidence", title: "证据" },
  { key: "conclusion", title: "结论" },
  { key: "closure", title: "结案" },
];

export default function WorkspaceView() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [audit, setAudit] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [st, an, tl] = await Promise.all([
        loadEvent(eventId),
        analyzeEvent(eventId),
        timeline(eventId),
      ]);
      setState(st);
      setAnalysis(an);
      setAudit(tl);
    } catch (e: any) {
      message.error("加载事件失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [eventId]);

  if (loading && !state) {
    return <Spin style={{ display: "block", margin: "80px auto" }} />;
  }
  if (!state) {
    return (
      <Alert
        type="error"
        message="未找到事件"
        action={
          <Button onClick={() => navigate("/cases")}>返回案例总览</Button>
        }
      />
    );
  }

  const event = state.event;
  const confirmations = state.confirmations ?? {};
  const confirmedCount = FLOW_NODES.filter(
    (n) => confirmations[n.key]?.disposition === "confirmed"
  ).length;

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/cases")}>
          返回
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {event.title}
        </Typography.Title>
        <Tag color="blue">{event.id}</Tag>
        <Tag>{event.scenario === "closed-cohort" ? "封闭队列" : "散发性零售"}</Tag>
        <Tag color="green">修订 {event.revision}</Tag>
      </Space>

      <Descriptions size="small" column={4} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="负责人">{event.lead || "—"}</Descriptions.Item>
        <Descriptions.Item label="接报时间">{event.received_at || "—"}</Descriptions.Item>
        <Descriptions.Item label="地点">{event.location || "—"}</Descriptions.Item>
        <Descriptions.Item label="资料截止">{event.data_cutoff || "—"}</Descriptions.Item>
      </Descriptions>

      <Steps
        size="small"
        current={confirmedCount}
        items={FLOW_NODES.map((n) => ({ title: n.title }))}
        style={{ marginBottom: 16 }}
      />

      <Tabs
        items={[
          {
            key: "analysis",
            label: "分析",
            children: <AnalysisPanel analysis={analysis} />,
          },
          {
            key: "data",
            label: "病例定义与数据",
            children: <DataPanel state={state} eventId={eventId} onRefresh={load} />,
          },
          {
            key: "evidence",
            label: "证据与结论",
            children: <EvidencePanel state={state} eventId={eventId} onRefresh={load} />,
          },
          {
            key: "trace",
            label: "溯源（审计）",
            children: <TracePanel audit={audit} />,
          },
        ]}
      />
    </div>
  );
}
