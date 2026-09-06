import { CheckCircleOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  List,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";
import { addEvidence, confirm, setConclusion } from "../../api/client";

const NODES = [
  { key: "intake", title: "接报" },
  { key: "definition", title: "病例定义" },
  { key: "plan", title: "调查计划" },
  { key: "analysis", title: "分析" },
  { key: "evidence", title: "证据" },
  { key: "conclusion", title: "结论" },
  { key: "closure", title: "结案" },
];

const TOPICS = [
  { key: "event_nature", name: "事件性质" },
  { key: "scope", name: "范围与病例数" },
  { key: "agent", name: "致病因素" },
  { key: "food", name: "原因食品" },
  { key: "contamination", name: "污染环节与原因" },
];

const STATUS_OPTS = [
  { value: "hypothesis", label: "待验证假设" },
  { value: "supported", label: "有证据支持的意见" },
  { value: "undetermined", label: "尚不能判定" },
  { value: "excluded", label: "排除意见" },
];

export default function EvidencePanel({ state, eventId, onRefresh }: any) {
  const confirmations = state.confirmations ?? {};
  const evidence = state.evidence ?? [];
  const conclusions = state.conclusions ?? [];

  const [confirmNote, setConfirmNote] = useState("");
  const [evOpen, setEvOpen] = useState(false);
  const [evForm] = Form.useForm();
  const [conclTopic, setConclTopic] = useState<string | null>(null);
  const [conclForm] = Form.useForm();

  const doConfirm = async (node: string) => {
    try {
      await confirm(eventId, {
        node,
        role: "调查员",
        note: confirmNote || "工作台确认",
        evidence_ids: [],
        disposition: "confirmed",
      });
      message.success(`已确认「${NODES.find((n) => n.key === node)?.title}」`);
      onRefresh();
    } catch (e: any) {
      message.error("确认失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  const onAddEvidence = async () => {
    const values = await evForm.validateFields();
    try {
      await addEvidence(eventId, values);
      message.success("已录入材料");
      setEvOpen(false);
      evForm.resetFields();
      onRefresh();
    } catch (e: any) {
      message.error("录入失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  const openConclusion = (topic: string) => {
    const cur = conclusions.find((c: any) => c.topic === topic);
    conclForm.setFieldsValue({
      status: cur?.status ?? "hypothesis",
      statement: cur?.statement ?? "",
      reason: cur?.reason ?? "",
      limitations: cur?.limitations ?? "",
      evidence_ids: cur?.evidence_ids ?? [],
    });
    setConclTopic(topic);
  };

  const onSaveConclusion = async () => {
    const values = await conclForm.validateFields();
    try {
      await setConclusion(eventId, { topic: conclTopic, ...values });
      message.success("结论已保存");
      setConclTopic(null);
      onRefresh();
    } catch (e: any) {
      message.error("保存失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  return (
    <div>
      <Card title="调查流程节点确认" style={{ marginBottom: 16 }}>
        <Typography.Paragraph type="secondary">
          按调查流程逐步确认节点，确认后在前端流程图中体现，并写入审计日志。
        </Typography.Paragraph>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Input
            placeholder="确认备注（可选）"
            value={confirmNote}
            onChange={(e) => setConfirmNote(e.target.value)}
            style={{ maxWidth: 420 }}
          />
          <Space wrap>
            {NODES.map((n) => {
              const done = confirmations[n.key]?.disposition === "confirmed";
              return (
                <Button
                  key={n.key}
                  type={done ? "primary" : "default"}
                  icon={done ? <CheckCircleOutlined /> : undefined}
                  onClick={() => doConfirm(n.key)}
                >
                  {n.title}
                </Button>
              );
            })}
          </Space>
        </Space>
      </Card>

      <Card
        title={`证据材料（${evidence.length}）`}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setEvOpen(true)}>
            新增材料
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          rowKey="id"
          size="small"
          dataSource={evidence}
          pagination={false}
          columns={[
            { title: "编号", dataIndex: "id" },
            { title: "名称", dataIndex: "title" },
            { title: "状态", dataIndex: "status", render: (v: string) => <Tag>{v || "—"}</Tag> },
            { title: "定位", dataIndex: "locator", render: (v: string) => v || "—" },
          ]}
        />
      </Card>

      <Card title="调查结论">
        <List
          dataSource={TOPICS}
          renderItem={(t) => {
            const cur = conclusions.find((c: any) => c.topic === t.key);
            return (
              <List.Item
                actions={[<Button key="e" onClick={() => openConclusion(t.key)}>编辑</Button>]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{t.name}</span>
                      {cur && (
                        <Tag color="blue">
                          {STATUS_OPTS.find((s) => s.value === cur.status)?.label ?? cur.status}
                        </Tag>
                      )}
                    </Space>
                  }
                  description={cur?.statement || "尚未综合研判"}
                />
              </List.Item>
            );
          }}
        />
      </Card>

      <Modal title="新增证据材料" open={evOpen} onOk={onAddEvidence} onCancel={() => setEvOpen(false)} okText="录入">
        <Form form={evForm} layout="vertical">
          <Form.Item name="id" label="材料编号" rules={[{ required: true }]}>
            <Input placeholder="如 EVID-001" />
          </Form.Item>
          <Form.Item name="title" label="名称">
            <Input placeholder="如 食堂留样检验报告" />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select options={["待取得", "已取得", "已核验"].map((s) => ({ value: s, label: s }))} />
          </Form.Item>
          <Form.Item name="locator" label="定位（档案号/链接）">
            <Input />
          </Form.Item>
          <Form.Item name="text" label="内容摘要">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑结论" open={!!conclTopic} onOk={onSaveConclusion} onCancel={() => setConclTopic(null)} okText="保存">
        <Form form={conclForm} layout="vertical">
          <Form.Item name="status" label="结论状态">
            <Select options={STATUS_OPTS} />
          </Form.Item>
          <Form.Item name="statement" label="结论陈述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="reason" label="依据与理由">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="limitations" label="局限">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="evidence_ids" label="关联材料编号">
            <Select mode="tags" options={evidence.map((e: any) => ({ value: e.id, label: e.id }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
