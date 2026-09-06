import { Table, Tag, Typography } from "antd";

export default function TracePanel({ audit }: { audit: any[] }) {
  return (
    <div>
      <Typography.Paragraph type="secondary">
        审计日志为追加式记录：每次对事件档案的修改均登记操作人、操作与说明，支撑调查过程可追溯、可核查。
      </Typography.Paragraph>
      <Table
        rowKey="seq"
        size="small"
        dataSource={audit}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: "序号", dataIndex: "seq" },
          { title: "修订", dataIndex: "revision" },
          { title: "操作人", dataIndex: "actor" },
          { title: "操作", dataIndex: "action", render: (v: string) => <Tag>{v}</Tag> },
          { title: "说明", dataIndex: "reason" },
          {
            title: "时间",
            dataIndex: "recorded_at",
            render: (v: string) => (v ? v.replace("T", " ").slice(0, 19) : "—"),
          },
        ]}
      />
    </div>
  );
}
