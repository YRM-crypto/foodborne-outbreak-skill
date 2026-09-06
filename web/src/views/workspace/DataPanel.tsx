import { Button, Card, Form, Input, InputNumber, Select, Switch, Table, Tag, Tabs, message } from "antd";
import { useEffect, useState } from "react";
import { setDefinition } from "../../api/client";

function symptomText(s: any) {
  if (!s) return "—";
  const yes = Object.entries(s)
    .filter(([, v]) => v === true)
    .map(([k]) => k);
  return yes.length ? yes.join("、") : "—";
}

export default function DataPanel({ state, eventId, onRefresh }: any) {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const definition = state.definition;

  useEffect(() => {
    form.setFieldsValue({
      label: definition?.label ?? "",
      text: definition?.text ?? "",
      start: definition?.start ?? "",
      end: definition?.end ?? "",
      symptoms_any: definition?.symptoms_any ?? [],
      minimum_symptoms: definition?.minimum_symptoms ?? 1,
      require_lab: !!definition?.require_lab,
    });
  }, [definition, form]);

  const onSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const payload = {
        ...(definition ?? {}),
        ...values,
        require_lab: values.require_lab ? 1 : 0,
      };
      await setDefinition(eventId, payload);
      message.success("病例定义已保存");
      onRefresh();
    } catch (e: any) {
      message.error("保存失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    } finally {
      setSaving(false);
    }
  };

  const people = state.people ?? [];
  const exposures = state.exposures ?? [];
  const samples = state.samples ?? [];

  const peopleCols = [
    { title: "编号", dataIndex: "id" },
    { title: "发病状态", dataIndex: "illness_status", render: (v: string) => <Tag>{v ?? "—"}</Tag> },
    { title: "起病时间", dataIndex: "onset" },
    { title: "性别", dataIndex: "sex" },
    { title: "年龄", dataIndex: "age" },
    { title: "地点", dataIndex: "location" },
    { title: "症状", dataIndex: "symptoms", render: symptomText },
  ];
  const exposureCols = [
    { title: "编号", dataIndex: "id" },
    { title: "人员", dataIndex: "person_id" },
    { title: "餐次", dataIndex: "meal_id" },
    { title: "食品", dataIndex: "food_id" },
    { title: "进食", dataIndex: "consumed", render: (v: number) => (v === 1 ? "是" : v === 0 ? "否" : "—") },
  ];
  const sampleCols = [
    { title: "编号", dataIndex: "id" },
    { title: "类型", dataIndex: "kind" },
    { title: "人员", dataIndex: "person_id" },
    { title: "来源", dataIndex: "source" },
    { title: "实验室", dataIndex: "laboratory" },
  ];

  return (
    <div>
      <Card title="病例定义" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Form.Item name="label" label="定义名称">
            <Input placeholder="如 餐后呕吐者" />
          </Form.Item>
          <Form.Item name="text" label="定义文本">
            <Input placeholder="如 2024-01-01 起在某食堂就餐后出现呕吐者" />
          </Form.Item>
          <Form.Item name="start" label="起病时间范围（起）">
            <Input placeholder="YYYY-MM-DDTHH:mm:ss" />
          </Form.Item>
          <Form.Item name="end" label="起病时间范围（止）">
            <Input placeholder="YYYY-MM-DDTHH:mm:ss" />
          </Form.Item>
          <Form.Item name="symptoms_any" label="纳入症状（满足任一）">
            <Select mode="tags" placeholder="输入症状后回车，如：呕吐、腹泻" />
          </Form.Item>
          <Form.Item name="minimum_symptoms" label="最低症状数">
            <InputNumber min={1} />
          </Form.Item>
          <Form.Item name="require_lab" label="需实验室确认" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Button type="primary" loading={saving} onClick={onSave}>
            保存病例定义
          </Button>
        </Form>
      </Card>

      <Tabs
        items={[
          {
            key: "people",
            label: `人员（${people.length}）`,
            children: <Table rowKey="id" size="small" dataSource={people} columns={peopleCols} pagination={{ pageSize: 20 }} />,
          },
          {
            key: "exposures",
            label: `暴露（${exposures.length}）`,
            children: <Table rowKey="id" size="small" dataSource={exposures} columns={exposureCols} pagination={{ pageSize: 20 }} />,
          },
          {
            key: "samples",
            label: `样本（${samples.length}）`,
            children: <Table rowKey="id" size="small" dataSource={samples} columns={sampleCols} pagination={{ pageSize: 20 }} />,
          },
        ]}
      />
    </div>
  );
}
