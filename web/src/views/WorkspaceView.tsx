import { Empty, Typography } from "antd";

export default function WorkspaceView() {
  return (
    <div>
      <Typography.Title level={4}>调查工作区</Typography.Title>
      <Empty description="Phase 3 实现：调查流程视图 + 流行曲线 + 三间分布 + 四格表 + 证据" />
    </div>
  );
}
