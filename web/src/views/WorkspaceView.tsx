import { ArrowLeftOutlined, CheckCircleFilled, RobotOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Descriptions,
  Space,
  Spin,
  Steps,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
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

// 阶段化流程强引导：每个节点的下一步提示 + 对应处理位置（工作区标签页）
const NODE_GUIDANCE: Record<string, { hint: string; tab: string }> = {
  intake: { hint: "登记事件基本信息（负责人、接报时间、地点、涉及人数）", tab: "data" },
  definition: { hint: "确定病例定义：时间 / 地点 / 人群范围 + 纳入症状", tab: "data" },
  plan: { hint: "明确调查计划与任务分工，确认「调查计划」节点", tab: "evidence" },
  analysis: { hint: "查看流行曲线、三间分布与食品关联分析", tab: "analysis" },
  evidence: { hint: "录入证据材料（留样、检验报告、就餐名单）", tab: "evidence" },
  conclusion: { hint: "综合研判事件性质、原因食品等结论", tab: "evidence" },
  closure: { hint: "确认结案节点，随后到「报告」页生成结案报告", tab: "evidence" },
};

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
  const nextNode = FLOW_NODES.find((n) => confirmations[n.key]?.disposition !== "confirmed");

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
        style={{ marginBottom: 12 }}
      />

      {nextNode ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message={
            <Space wrap>
              <span>
                建议下一步：完善「{nextNode.title}」——{NODE_GUIDANCE[nextNode.key]?.hint}。
              </span>
              <Button
                size="small"
                type="primary"
                onClick={() => setTab(NODE_GUIDANCE[nextNode.key]?.tab ?? "analysis")}
              >
                前往处理
              </Button>
            </Space>
          }
        />
      ) : (
        <Alert
          type="success"
          showIcon
          icon={<CheckCircleFilled />}
          style={{ marginBottom: 16 }}
          message="全部流程节点已确认，可前往「报告」页生成结案报告。"
        />
      )}

      <Tabs
        activeKey={tab}
        onChange={setTab}
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
