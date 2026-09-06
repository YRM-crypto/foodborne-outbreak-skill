import { PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";
import { upsertExposures, upsertPeople } from "../../api/client";
import { SYMPTOMS } from "../../constants";

function symptomText(s: any) {
  if (!s) return "—";
  const yes = Object.entries(s).filter(([, v]) => v === true).map(([k]) => k);
  return yes.length ? yes.join("、") : "—";
}

// —— 批量粘贴解析：编号\t发病状态\t起病时间\t性别\t年龄\t地点\t症状(顿号分隔) ——
function parsePeopleTsv(text: string): any[] {
  const rows = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  return rows.map((line, i) => {
    const [id, illness_status, onset, sex, age, location, symptoms] = line.split("\t").map((s) => s.trim());
    const ill = illness_status === "ill" || illness_status === "发病";
    const sym: Record<string, boolean> = {};
    (symptoms || "").split(/[、,，\s]+/).filter(Boolean).forEach((k) => (sym[k] = true));
    return {
      id: id || `P${i + 1}`,
      illness_status: ill ? "ill" : "well",
      onset: onset || (ill ? undefined : null),
      sex: sex || undefined,
      age: age ? Number(age) : undefined,
      location: location || undefined,
      symptoms: sym,
    };
  });
}

// —— 批量粘贴解析：编号\t人员\t餐次\t进食时间\t食品\t进食(1/0) ——
function parseExposureTsv(text: string): any[] {
  const rows = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  return rows.map((line, i) => {
    const [id, person_id, meal_id, meal_at, food_id, consumed] = line.split("\t").map((s) => s.trim());
    return {
      id: id || `E${i + 1}`,
      person_id,
      meal_id: meal_id || undefined,
      meal_at: meal_at || undefined,
      food_id: food_id || undefined,
      consumed: consumed === "1" || consumed === "是" ? 1 : 0,
      incubation_anchor: 1,
    };
  });
}

export default function CasesPanel({ state, eventId, onRefresh }: any) {
  const people = state.people ?? [];
  const exposures = state.exposures ?? [];

  const [personOpen, setPersonOpen] = useState(false);
  const [batchPersonOpen, setBatchPersonOpen] = useState(false);
  const [personForm] = Form.useForm();
  const [batchPerson, setBatchPerson] = useState("");

  const [expOpen, setExpOpen] = useState(false);
  const [batchExpOpen, setBatchExpOpen] = useState(false);
  const [expForm] = Form.useForm();
  const [batchExp, setBatchExp] = useState("");

  const [saving, setSaving] = useState(false);

  const savePeople = async (rows: any[]) => {
    setSaving(true);
    try {
      await upsertPeople(eventId, rows);
      message.success(`已写入 ${rows.length} 条个案`);
      onRefresh();
      return true;
    } catch (e: any) {
      message.error("写入失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const saveExposures = async (rows: any[]) => {
    setSaving(true);
    try {
      await upsertExposures(eventId, rows);
      message.success(`已写入 ${rows.length} 条暴露`);
      onRefresh();
      return true;
    } catch (e: any) {
      message.error("写入失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const peopleCols = [
    { title: "编号", dataIndex: "id", width: 90 },
    {
      title: "发病状态",
      dataIndex: "illness_status",
      render: (v: string) => <Tag color={v === "ill" ? "red" : v === "well" ? "green" : "default"}>{v ?? "—"}</Tag>,
    },
    { title: "起病时间", dataIndex: "onset", render: (v: string) => v || "—" },
    { title: "性别", dataIndex: "sex", render: (v: string) => v || "—" },
    { title: "年龄", dataIndex: "age", render: (v: any) => v ?? "—" },
    { title: "地点", dataIndex: "location", render: (v: string) => v || "—" },
    { title: "症状", dataIndex: "symptoms", render: symptomText },
  ];

  const exposureCols = [
    { title: "编号", dataIndex: "id", width: 90 },
    { title: "人员", dataIndex: "person_id" },
    { title: "餐次", dataIndex: "meal_id", render: (v: string) => v || "—" },
    { title: "进食时间", dataIndex: "meal_at", render: (v: string) => v || "—" },
    { title: "食品", dataIndex: "food_id", render: (v: string) => v || "—" },
    {
      title: "进食",
      dataIndex: "consumed",
      render: (v: number) => (v === 1 ? <Tag color="red">是</Tag> : v === 0 ? "否" : "—"),
    },
  ];

  return (
    <div>
      <Card title="个案调查与暴露史（表格批量 + 表单）" style={{ marginBottom: 16 }}>
        <Tabs
          items={[
            {
              key: "people",
              label: `个案（${people.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }} wrap>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setPersonOpen(true)}>
                      新增个案
                    </Button>
                    <Button onClick={() => setBatchPersonOpen(true)}>批量粘贴</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={people} columns={peopleCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
            {
              key: "exposures",
              label: `暴露（${exposures.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }} wrap>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setExpOpen(true)}>
                      新增暴露
                    </Button>
                    <Button onClick={() => setBatchExpOpen(true)}>批量粘贴</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={exposures} columns={exposureCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* 新增个案 */}
      <Modal
        title="新增个案"
        open={personOpen}
        onOk={async () => {
          const v = await personForm.validateFields();
          if (await savePeople([v])) {
            setPersonOpen(false);
            personForm.resetFields();
          }
        }}
        onCancel={() => setPersonOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={personForm} layout="vertical" initialValues={{ illness_status: "ill" }}>
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 P001" />
          </Form.Item>
          <Form.Item name="illness_status" label="发病状态">
            <Select options={[{ value: "ill", label: "发病" }, { value: "well", label: "未发病" }]} />
          </Form.Item>
          <Form.Item name="onset" label="起病时间">
            <Input placeholder="YYYY-MM-DDTHH:mm:ss" />
          </Form.Item>
          <Space size={16} style={{ display: "flex" }} wrap>
            <Form.Item name="sex" label="性别" style={{ marginBottom: 0 }}>
              <Select style={{ width: 100 }} options={["男", "女"].map((s) => ({ value: s, label: s }))} />
            </Form.Item>
            <Form.Item name="age" label="年龄" style={{ marginBottom: 0 }}>
              <InputNumber min={0} />
            </Form.Item>
          </Space>
          <Form.Item name="location" label="地点">
            <Input />
          </Form.Item>
          <Form.Item name="symptoms" label="症状（选中＝阳性）">
            <Select mode="multiple" options={SYMPTOMS.map((s) => ({ value: s, label: s }))} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量粘贴个案 */}
      <Modal
        title="批量粘贴个案"
        open={batchPersonOpen}
        onOk={async () => {
          if (await savePeople(parsePeopleTsv(batchPerson))) {
            setBatchPersonOpen(false);
            setBatchPerson("");
          }
        }}
        onCancel={() => setBatchPersonOpen(false)}
        okText="写入"
        confirmLoading={saving}
      >
        <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
          每行一条，Tab 分隔：编号　发病状态(ill/well)　起病时间　性别　年龄　地点　症状(顿号分隔)
        </Typography.Paragraph>
        <Input.TextArea
          rows={10}
          value={batchPerson}
          onChange={(e) => setBatchPerson(e.target.value)}
          placeholder={"P001\till\t2018-06-29T18:00\t男\t21\t某厂\t腹泻、腹痛\nP002\twell\t\t女\t20\t某厂\t"}
        />
      </Modal>

      {/* 新增暴露 */}
      <Modal
        title="新增暴露"
        open={expOpen}
        onOk={async () => {
          const v = await expForm.validateFields();
          if (await saveExposures([{ ...v, incubation_anchor: 1 }])) {
            setExpOpen(false);
            expForm.resetFields();
          }
        }}
        onCancel={() => setExpOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={expForm} layout="vertical">
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 E1" />
          </Form.Item>
          <Form.Item name="person_id" label="人员编号" rules={[{ required: true }]}>
            <Input placeholder="如 P001" />
          </Form.Item>
          <Form.Item name="meal_id" label="餐次">
            <Input placeholder="如 6月29日午餐" />
          </Form.Item>
          <Form.Item name="meal_at" label="进食时间">
            <Input placeholder="YYYY-MM-DDTHH:mm:ss" />
          </Form.Item>
          <Form.Item name="food_id" label="食品">
            <Input placeholder="如 凉拌绿豆芽" />
          </Form.Item>
          <Form.Item name="consumed" label="进食" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量粘贴暴露 */}
      <Modal
        title="批量粘贴暴露"
        open={batchExpOpen}
        onOk={async () => {
          if (await saveExposures(parseExposureTsv(batchExp))) {
            setBatchExpOpen(false);
            setBatchExp("");
          }
        }}
        onCancel={() => setBatchExpOpen(false)}
        okText="写入"
        confirmLoading={saving}
      >
        <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
          每行一条，Tab 分隔：编号　人员　餐次　进食时间　食品　进食(1/0)
        </Typography.Paragraph>
        <Input.TextArea
          rows={10}
          value={batchExp}
          onChange={(e) => setBatchExp(e.target.value)}
          placeholder={"E1\tP001\t6月29日午餐\t2018-06-29T12:00\t凉拌绿豆芽\t1\nE2\tP001\t6月29日午餐\t2018-06-29T12:00\t米饭\t1"}
        />
      </Modal>
    </div>
  );
}
