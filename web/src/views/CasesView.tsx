import { PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createEvent, listEvents } from "../api/client";

const scenarioLabels: Record<string, string> = {
  "closed-cohort": "封闭队列",
  "distributed-retail": "散发性零售",
};

export default function CasesView() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
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
      message.success("已创建事件");
      setOpen(false);
      form.resetFields();
      await load();
      navigate(`/workspace/${values.event_id}`);
    } catch (e: any) {
      message.error("创建失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  const columns = [
    { title: "事件编号", dataIndex: "id", key: "id" },
    { title: "标题", dataIndex: "title", key: "title" },
    {
      title: "类型",
      dataIndex: "scenario",
      key: "scenario",
      render: (v: string) => <Tag color="blue">{scenarioLabels[v] ?? v}</Tag>,
    },
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
        <Form form={form} layout="vertical" initialValues={{ scenario: "closed-cohort" }}>
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
          <Form.Item name="scenario" label="调查类型">
            <Select
              options={[
                { value: "closed-cohort", label: "封闭队列（聚餐/食堂）" },
                { value: "distributed-retail", label: "散发性零售（食品溯源）" },
              ]}
            />
          </Form.Item>
          <Form.Item name="lead" label="负责人">
            <Input placeholder="调查组" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
