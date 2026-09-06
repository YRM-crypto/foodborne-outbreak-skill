import { Card, Select, Space, Tag, Typography, message } from "antd";
import { setStage } from "../../api/client";
import { STAGES, STAGE_GROUPS, STAGE_STATUS_LABEL } from "../../constants";

const STATUS_COLOR: Record<string, string> = {
  pending: "default",
  in_progress: "blue",
  done: "green",
  na: "default",
};

export default function StagesPanel({ state, eventId, onRefresh }: any) {
  const stages = state.stages ?? {};

  const change = async (stageId: string, status: string) => {
    try {
      await setStage(eventId, { stage: stageId, status, note: "" });
      message.success(`阶段已更新为「${STAGE_STATUS_LABEL[status]}」`);
      onRefresh();
    } catch (e: any) {
      message.error("更新失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    }
  };

  return (
    <div>
      <Typography.Paragraph type="secondary">
        13 个调查阶段为「引导清单」而非强制门禁：工作流并非单向，任何环节均可补充新调查材料并随时重算。
        阶段状态仅用于记录完成度，不影响数据录入。
      </Typography.Paragraph>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        {STAGE_GROUPS.map((group) => (
          <Card key={group} title={group} size="small">
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              {STAGES.filter((s) => s.group === group).map((s) => {
                const cur = stages[s.id];
                const status = cur?.status ?? "pending";
                return (
                  <div
                    key={s.id}
                    style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}
                  >
                    <div style={{ minWidth: 150 }}>
                      <Space>
                        <Tag color={STATUS_COLOR[status]}>{STAGE_STATUS_LABEL[status]}</Tag>
                        <span>{s.name}</span>
                      </Space>
                    </div>
                    <Typography.Text type="secondary" style={{ fontSize: 12, flex: 1 }}>
                      {s.table}
                    </Typography.Text>
                    <Select
                      size="small"
                      style={{ width: 110 }}
                      value={status}
                      onChange={(v) => change(s.id, v)}
                      options={Object.entries(STAGE_STATUS_LABEL).map(([value, label]) => ({
                        value,
                        label,
                      }))}
                    />
                  </div>
                );
              })}
            </Space>
          </Card>
        ))}
      </Space>
    </div>
  );
}
