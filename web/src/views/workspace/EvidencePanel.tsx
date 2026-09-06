import { PlusOutlined } from "@ant-design/icons";
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
import { addEvidence, setConclusion } from "../../api/client";
import { CONCLUSION_STATUS, CONCLUSION_TOPICS, CONTAMINATION_FACTORS, CONTAMINATION_LINKS } from "../../constants";

const STATUS_COLOR: Record<string, string> = {
  confirmed: "green",
  probable: "orange",
  unknown: "default",
  excluded: "red",
};

export default function EvidencePanel({ state, eventId, onRefresh }: any) {
  const evidence = state.evidence ?? [];
  const conclusions = state.conclusions ?? [];

  const [evOpen, setEvOpen] = useState(false);
  const [evForm] = Form.useForm();

  const [conclTopic, setConclTopic] = useState<string | null>(null);
  const [conclForm] = Form.useForm();

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
      status: cur?.status ?? "unknown",
      statement: cur?.statement ?? "",
      reason: cur?.reason ?? "",
      limitations: cur?.limitations ?? "",
      link: cur?.link ?? undefined,
      factor: cur?.factor ?? undefined,
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
      <Card
        title={`证据材料（${evidence.length}）`}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setEvOpen(true)}>
            新增材料
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Typography.Paragraph type="secondary">
          原始材料（访谈记录、留样、检验报告、就餐名单等）为「证据底座」；派生指标与结论均据此重算。
        </Typography.Paragraph>
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
          dataSource={CONCLUSION_TOPICS}
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
                        <Tag color={STATUS_COLOR[cur.status] ?? "default"}>
                          {CONCLUSION_STATUS[cur.status] ?? cur.status}
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
            <Select options={Object.entries(CONCLUSION_STATUS).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="statement" label="结论陈述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="reason" label="依据与理由">
            <Input.TextArea rows={2} />
          </Form.Item>
          {conclTopic === "contamination" && (
            <Space size={16} style={{ display: "flex" }} wrap>
              <Form.Item name="link" label="污染环节" style={{ marginBottom: 0 }}>
                <Select
                  allowClear
                  style={{ width: 220 }}
                  options={CONTAMINATION_LINKS.map((l) => ({ value: l, label: l }))}
                />
              </Form.Item>
              <Form.Item name="factor" label="污染原因" style={{ marginBottom: 0 }}>
                <Select
                  allowClear
                  style={{ width: 260 }}
                  options={CONTAMINATION_FACTORS.map((f) => ({ value: f, label: f }))}
                />
              </Form.Item>
            </Space>
          )}
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
