import { PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
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
import { upsertControls, upsertFoods, upsertHygiene, upsertSamples } from "../../api/client";
import { CONTROL_MEASURES, FOOD_CATEGORIES, HYGIENE_ASPECTS, SAMPLE_CATEGORIES } from "../../constants";

const sampleCatLabel = (v: string) => SAMPLE_CATEGORIES[v] ?? v;

// —— 批量粘贴：编号\t类别\t餐次\t来源\t加工方式\t包装\t备注 ——
function parseFoodsTsv(text: string): any[] {
  return text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean).map((line, i) => {
    const [id, category, meal_id, source, process_method, package_, notes] = line.split("\t").map((s) => s.trim());
    return {
      id: id || `F${i + 1}`,
      category: category || undefined,
      meal_id: meal_id || undefined,
      source: source || undefined,
      process_method: process_method || undefined,
      package: package_ || undefined,
      notes: notes || undefined,
    };
  });
}

// —— 批量粘贴：编号\t类别\t来源\t人员\t实验室\t采样时间\t检验(顿号分隔)\t备注 ——
function parseSamplesTsv(text: string): any[] {
  return text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean).map((line, i) => {
    const [id, category, source, person_id, laboratory, collected_at, tests, notes] = line.split("\t").map((s) => s.trim());
    return {
      id: id || `S${i + 1}`,
      category: category || undefined,
      source: source || undefined,
      person_id: person_id || undefined,
      laboratory: laboratory || undefined,
      collected_at: collected_at || undefined,
      tests: (tests || "").split(/[、,，\s]+/).filter(Boolean),
      notes: notes || undefined,
    };
  });
}

export default function FieldPanel({ state, eventId, onRefresh }: any) {
  const foods = state.foods ?? [];
  const samples = state.samples ?? [];
  const hygiene = state.hygiene ?? [];
  const controls = state.controls ?? [];

  const [saving, setSaving] = useState(false);

  const [foodOpen, setFoodOpen] = useState(false);
  const [batchFoodOpen, setBatchFoodOpen] = useState(false);
  const [foodForm] = Form.useForm();
  const [batchFood, setBatchFood] = useState("");

  const [sampleOpen, setSampleOpen] = useState(false);
  const [batchSampleOpen, setBatchSampleOpen] = useState(false);
  const [sampleForm] = Form.useForm();
  const [batchSample, setBatchSample] = useState("");

  const [hygOpen, setHygOpen] = useState(false);
  const [hygForm] = Form.useForm();

  const [ctrlOpen, setCtrlOpen] = useState(false);
  const [ctrlForm] = Form.useForm();

  const save = async (fn: (id: string, rows: any[]) => Promise<any>, rows: any[], label: string) => {
    setSaving(true);
    try {
      await fn(eventId, rows);
      message.success(`已写入 ${rows.length} 条${label}`);
      onRefresh();
      return true;
    } catch (e: any) {
      message.error("写入失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const foodCols = [
    { title: "编号", dataIndex: "id", width: 100 },
    { title: "类别", dataIndex: "category", render: (v: string) => v || "—" },
    { title: "餐次", dataIndex: "meal_id", render: (v: string) => v || "—" },
    { title: "来源", dataIndex: "source", render: (v: string) => v || "—" },
    { title: "加工方式", dataIndex: "process_method", render: (v: string) => v || "—" },
    { title: "包装", dataIndex: "package", render: (v: string) => v || "—" },
    { title: "备注", dataIndex: "notes", render: (v: string) => v || "—" },
  ];

  const sampleCols = [
    { title: "编号", dataIndex: "id", width: 100 },
    { title: "类别", dataIndex: "category", render: (v: string) => <Tag>{sampleCatLabel(v)}</Tag> },
    { title: "来源", dataIndex: "source", render: (v: string) => v || "—" },
    { title: "人员", dataIndex: "person_id", render: (v: string) => v || "—" },
    { title: "实验室", dataIndex: "laboratory", render: (v: string) => v || "—" },
    { title: "采样时间", dataIndex: "collected_at", render: (v: string) => v || "—" },
    { title: "检验", dataIndex: "tests", render: (v: string[]) => (v?.length ? v.join("、") : "—") },
  ];

  const hygCols = [
    { title: "编号", dataIndex: "id", width: 100 },
    { title: "方面", dataIndex: "aspect", render: (v: string) => v || "—" },
    { title: "项目", dataIndex: "item", render: (v: string) => v || "—" },
    { title: "发现", dataIndex: "finding", render: (v: string) => v || "—" },
    { title: "问题", dataIndex: "problem", render: (v: number) => (v === 1 ? <Tag color="red">是</Tag> : v === 0 ? "否" : "—") },
    { title: "备注", dataIndex: "notes", render: (v: string) => v || "—" },
  ];

  const ctrlCols = [
    { title: "编号", dataIndex: "id", width: 100 },
    { title: "措施", dataIndex: "measure", render: (v: string) => v || "—" },
    { title: "对象", dataIndex: "target", render: (v: string) => v || "—" },
    { title: "落实情况", dataIndex: "implemented", render: (v: string) => v || "—" },
    { title: "日期", dataIndex: "date", render: (v: string) => v || "—" },
    { title: "备注", dataIndex: "notes", render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Card title="现场调查（食品 / 样本 / 卫生学 / 控制措施）" style={{ marginBottom: 16 }}>
        <Tabs
          items={[
            {
              key: "foods",
              label: `食品清单（${foods.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }} wrap>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setFoodOpen(true)}>新增食品</Button>
                    <Button onClick={() => setBatchFoodOpen(true)}>批量粘贴</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={foods} columns={foodCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
            {
              key: "samples",
              label: `样本（${samples.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }} wrap>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setSampleOpen(true)}>新增样本</Button>
                    <Button onClick={() => setBatchSampleOpen(true)}>批量粘贴</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={samples} columns={sampleCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
            {
              key: "hygiene",
              label: `卫生学（${hygiene.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }}>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setHygOpen(true)}>新增卫生学记录</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={hygiene} columns={hygCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
            {
              key: "controls",
              label: `控制措施（${controls.length}）`,
              children: (
                <div>
                  <Space style={{ marginBottom: 12 }}>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setCtrlOpen(true)}>新增控制措施</Button>
                  </Space>
                  <Table rowKey="id" size="small" dataSource={controls} columns={ctrlCols} pagination={{ pageSize: 20 }} />
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* 新增食品 */}
      <Modal
        title="新增食品"
        open={foodOpen}
        onOk={async () => {
          const v = await foodForm.validateFields();
          if (await save(upsertFoods, [v], "食品")) { setFoodOpen(false); foodForm.resetFields(); }
        }}
        onCancel={() => setFoodOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={foodForm} layout="vertical">
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 F1" />
          </Form.Item>
          <Form.Item name="category" label="类别">
            <Select allowClear options={FOOD_CATEGORIES.map((c) => ({ value: c, label: c }))} />
          </Form.Item>
          <Form.Item name="meal_id" label="餐次"><Input placeholder="如 6月29日午餐" /></Form.Item>
          <Form.Item name="source" label="来源"><Input /></Form.Item>
          <Form.Item name="process_method" label="加工方式"><Input /></Form.Item>
          <Form.Item name="package" label="包装"><Input /></Form.Item>
          <Form.Item name="notes" label="备注"><Input /></Form.Item>
        </Form>
      </Modal>

      {/* 批量粘贴食品 */}
      <Modal
        title="批量粘贴食品"
        open={batchFoodOpen}
        onOk={async () => {
          if (await save(upsertFoods, parseFoodsTsv(batchFood), "食品")) { setBatchFoodOpen(false); setBatchFood(""); }
        }}
        onCancel={() => setBatchFoodOpen(false)}
        okText="写入"
        confirmLoading={saving}
      >
        <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
          每行一条，Tab 分隔：编号　类别　餐次　来源　加工方式　包装　备注
        </Typography.Paragraph>
        <Input.TextArea rows={10} value={batchFood} onChange={(e) => setBatchFood(e.target.value)} />
      </Modal>

      {/* 新增样本 */}
      <Modal
        title="新增样本"
        open={sampleOpen}
        onOk={async () => {
          const v = await sampleForm.validateFields();
          if (await save(upsertSamples, [v], "样本")) { setSampleOpen(false); sampleForm.resetFields(); }
        }}
        onCancel={() => setSampleOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={sampleForm} layout="vertical">
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 S1" />
          </Form.Item>
          <Form.Item name="category" label="类别">
            <Select allowClear options={Object.entries(SAMPLE_CATEGORIES).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="source" label="来源"><Input /></Form.Item>
          <Form.Item name="person_id" label="人员"><Input placeholder="生物标本时填，如 P001" /></Form.Item>
          <Form.Item name="laboratory" label="实验室"><Input /></Form.Item>
          <Form.Item name="collected_at" label="采样时间"><Input placeholder="YYYY-MM-DDTHH:mm:ss" /></Form.Item>
          <Form.Item name="tests" label="检验结果">
            <Select mode="tags" placeholder="如 副溶血性弧菌阳性" />
          </Form.Item>
          <Form.Item name="notes" label="备注"><Input /></Form.Item>
        </Form>
      </Modal>

      {/* 批量粘贴样本 */}
      <Modal
        title="批量粘贴样本"
        open={batchSampleOpen}
        onOk={async () => {
          if (await save(upsertSamples, parseSamplesTsv(batchSample), "样本")) { setBatchSampleOpen(false); setBatchSample(""); }
        }}
        onCancel={() => setBatchSampleOpen(false)}
        okText="写入"
        confirmLoading={saving}
      >
        <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
          每行一条，Tab 分隔：编号　类别　来源　人员　实验室　采样时间　检验(顿号分隔)　备注
        </Typography.Paragraph>
        <Input.TextArea rows={10} value={batchSample} onChange={(e) => setBatchSample(e.target.value)} />
      </Modal>

      {/* 新增卫生学 */}
      <Modal
        title="新增卫生学记录"
        open={hygOpen}
        onOk={async () => {
          const v = await hygForm.validateFields();
          if (await save(upsertHygiene, [v], "卫生学")) { setHygOpen(false); hygForm.resetFields(); }
        }}
        onCancel={() => setHygOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={hygForm} layout="vertical" initialValues={{ problem: false }}>
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 H1" />
          </Form.Item>
          <Form.Item name="aspect" label="方面">
            <Select allowClear options={HYGIENE_ASPECTS.map((a) => ({ value: a, label: a }))} />
          </Form.Item>
          <Form.Item name="item" label="项目"><Input /></Form.Item>
          <Form.Item name="finding" label="发现"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="problem" label="存在问题" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item name="notes" label="备注"><Input /></Form.Item>
        </Form>
      </Modal>

      {/* 新增控制措施 */}
      <Modal
        title="新增控制措施"
        open={ctrlOpen}
        onOk={async () => {
          const v = await ctrlForm.validateFields();
          if (await save(upsertControls, [v], "控制措施")) { setCtrlOpen(false); ctrlForm.resetFields(); }
        }}
        onCancel={() => setCtrlOpen(false)}
        okText="保存"
        confirmLoading={saving}
      >
        <Form form={ctrlForm} layout="vertical">
          <Form.Item name="id" label="编号" rules={[{ required: true }]}>
            <Input placeholder="如 C1" />
          </Form.Item>
          <Form.Item name="measure" label="措施">
            <Select allowClear options={CONTROL_MEASURES.map((m) => ({ value: m, label: m }))} />
          </Form.Item>
          <Form.Item name="target" label="对象"><Input /></Form.Item>
          <Form.Item name="implemented" label="落实情况"><Input /></Form.Item>
          <Form.Item name="date" label="日期"><Input placeholder="YYYY-MM-DD" /></Form.Item>
          <Form.Item name="notes" label="备注"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
