import { Empty, Typography } from "antd";

export default function CasesView() {
  return (
    <div>
      <Typography.Title level={4}>案例总览</Typography.Title>
      <Empty description="Phase 3 实现：案例列表、新建事件、调查状态流转" />
    </div>
  );
}
