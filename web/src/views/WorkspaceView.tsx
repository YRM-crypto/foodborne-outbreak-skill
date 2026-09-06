import { ArrowLeftOutlined, RobotOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Descriptions, Progress, Space, Spin, Tabs, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { analyzeEvent, loadEvent, timeline } from "../api/client";
import { STAGES, STUDY_DESIGNS } from "../constants";
import AnalysisPanel from "./workspace/AnalysisPanel";
import CasesPanel from "./workspace/CasesPanel";
import DefinitionPanel from "./workspace/DefinitionPanel";
import EvidencePanel from "./workspace/EvidencePanel";
import FieldPanel from "./workspace/FieldPanel";
import StagesPanel from "./workspace/StagesPanel";
import TracePanel from "./workspace/TracePanel";

export default function WorkspaceView() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [audit, setAudit] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("analysis");

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
        action={<Button onClick={() => navigate("/cases")}>返回案例总览</Button>}
      />
    );
  }

  const event = state.event;
  const stages = state.stages ?? {};
  const doneCount = STAGES.filter((s) => stages[s.id]?.status === "done").length;

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/cases")}>
          返回
        </Button>
        <Button icon={<RobotOutlined />} onClick={() => navigate(`/assistant/${event.id}`)}>
          问 AI
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {event.title}
        </Typography.Title>
        <Tag color="blue">{event.id}</Tag>
        <Tag color="green">修订 {event.revision}</Tag>
      </Space>

      <Descriptions size="small" column={4} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="负责人">{event.lead || "—"}</Descriptions.Item>
        <Descriptions.Item label="场所类型">{event.place_type || "—"}</Descriptions.Item>
        <Descriptions.Item label="地区">{event.region || "—"}</Descriptions.Item>
        <Descriptions.Item label="接报时间">{event.received_at || "—"}</Descriptions.Item>
        <Descriptions.Item label="发生时间">{event.occurred_at || "—"}</Descriptions.Item>
        <Descriptions.Item label="暴露时间">{event.exposure_at || "—"}</Descriptions.Item>
        <Descriptions.Item label="研究设计">
          {event.study_design ? STUDY_DESIGNS[event.study_design] ?? event.study_design : "—"}
        </Descriptions.Item>
        <Descriptions.Item label="暴露人数">
          {event.population_size != null ? event.population_size : "—"}
        </Descriptions.Item>
      </Descriptions>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Space wrap>
            <span>调查阶段完成度：</span>
            <Progress
              style={{ width: 260 }}
              percent={Math.round((doneCount / STAGES.length) * 100)}
              size="small"
            />
            <Typography.Text type="secondary">
              {doneCount}/{STAGES.length} 阶段已完成
            </Typography.Text>
          </Space>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            13 个阶段为「引导清单」而非强制门禁：工作流并非单向，任何环节均可补充新调查材料并随时重算。
          </Typography.Text>
        </Space>
      </Card>

      <Tabs
        activeKey={tab}
        onChange={setTab}
        items={[
          { key: "analysis", label: "分析", children: <AnalysisPanel analysis={analysis} /> },
          { key: "definition", label: "病例定义", children: <DefinitionPanel state={state} eventId={eventId} onRefresh={load} /> },
          { key: "cases", label: "个案与暴露", children: <CasesPanel state={state} eventId={eventId} onRefresh={load} /> },
          { key: "field", label: "现场调查", children: <FieldPanel state={state} eventId={eventId} onRefresh={load} /> },
          { key: "evidence", label: "证据与结论", children: <EvidencePanel state={state} eventId={eventId} onRefresh={load} /> },
          { key: "stages", label: "调查阶段", children: <StagesPanel state={state} eventId={eventId} onRefresh={load} /> },
          { key: "trace", label: "溯源（审计）", children: <TracePanel audit={audit} /> },
        ]}
      />
    </div>
  );
}
