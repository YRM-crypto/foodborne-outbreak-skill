import { ExperimentOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Steps,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createEvent, listEvents, seedDemo, updateEvent } from "../api/client";
import { PLACE_TYPES } from "../constants";

export default function CasesView() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      setEvents(await listEvents());
    } catch (e: any) {
      message.error("加载案例失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onCreate = async () => {
    const values = await form.validateFields();
    try {
      await createEvent(values);
      const patch: any = {};
      if (values.place_type) patch.place_type = values.place_type;
      if (values.region) patch.region = values.region;
      if (Object.keys(patch).length) await updateEvent(values.event_id, patch);
      message.success("已创建事件");
      setOpen(false);
      form.resetFields();
      await load();
      navigate(`/workspace/${values.event_id}`);
    } catch (e: any) {
      message.error("创建失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  const onSeed = async () => {
    setSeeding(true);
    try {
      await seedDemo();
      message.success("已生成演示事件，正在打开…");
      await load();
      navigate("/workspace/EV-DEMO-001");
    } catch (e: any) {
      message.error("生成失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    } finally {
      setSeeding(false);
    }
  };

  const columns = [
    { title: "事件编号", dataIndex: "id", key: "id" },
    { title: "标题", dataIndex: "title", key: "title" },
    {
      title: "场所类型",
      dataIndex: "place_type",
      key: "place_type",
      render: (v: string) => (v ? <Tag color="blue">{v}</Tag> : "—"),
    },
    { title: "地区", dataIndex: "region", key: "region", render: (v: string) => v || "—" },
    { title: "负责人", dataIndex: "lead", key: "lead" },
    { title: "修订", dataIndex: "revision", key: "revision" },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (v: string) => (v ? v.replace("T", " ").slice(0, 16) : "—"),
    },
  ];

  return (
    <div>
      <Space style={{ width: "100%", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          案例总览
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新建事件
        </Button>
      </Space>

      {!loading && events.length === 0 && (
        <Card style={{ marginBottom: 16, textAlign: "center" }}>
          <Typography.Title level={5}>开始你的第一次暴发调查</Typography.Title>
          <Steps
            size="small"
            direction="vertical"
            style={{ maxWidth: 440, margin: "16px auto", textAlign: "left" }}
            items={[
              { title: "新建事件", description: "登记事件编号、标题、场所类型与负责人" },
              { title: "录入数据", description: "病例定义、个案与暴露、食品/样本/卫生学" },
              { title: "分析与报告", description: "查看流行曲线与食品关联，生成调查报告" },
            ]}
          />
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
              新建事件
            </Button>
            <Button icon={<ExperimentOutlined />} loading={seeding} onClick={onSeed}>
              生成演示数据
            </Button>
          </Space>
        </Card>
      )}

      <Table
        rowKey="id"
        loading={loading}
        dataSource={events}
        columns={columns}
        onRow={(r) => ({
          onClick: () => navigate(`/workspace/${r.id}`),
          style: { cursor: "pointer" },
        })}
      />

      <Modal
        title="新建暴发事件"
        open={open}
        onOk={onCreate}
        onCancel={() => setOpen(false)}
        okText="创建"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="event_id"
            label="事件编号"
            rules={[{ required: true, message: "请输入事件编号" }]}
          >
            <Input placeholder="如 EV-2024-001" />
          </Form.Item>
          <Form.Item
            name="title"
            label="事件标题"
            rules={[{ required: true, message: "请输入标题" }]}
          >
            <Input placeholder="如 某学校聚集性呕吐" />
          </Form.Item>
          <Form.Item name="place_type" label="场所类型">
            <Select allowClear options={PLACE_TYPES.map((p) => ({ value: p, label: p }))} />
          </Form.Item>
          <Form.Item name="region" label="地区">
            <Input placeholder="如 XX 省 XX 市" />
          </Form.Item>
          <Form.Item name="lead" label="负责人">
            <Input placeholder="调查组" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
