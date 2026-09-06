import { Column, Line } from "@ant-design/plots";
import { Alert, Card, Col, Empty, Row, Statistic, Table, Tag } from "antd";

function toXY(obj: Record<string, number>) {
  return Object.entries(obj).map(([label, value]) => ({ label, value }));
}

const cellStyle: React.CSSProperties = {
  border: "1px solid #d9d9d9",
  padding: "4px 12px",
  textAlign: "center",
};

export default function AnalysisPanel({ analysis }: { analysis: any }) {
  if (!analysis) return <Empty description="暂无分析结果（请先在「病例定义与数据」录入病例）" />;

  const stats = analysis.stats ?? {};
  const classified = analysis.classified ?? [];
  const counts = stats.counts ?? {};
  const ar = stats.attack_rate ?? {};

  const byDate = toXY(stats.by_date ?? {});
  const bySex = toXY(stats.by_sex ?? {});
  const byAge = toXY(stats.by_age ?? {});
  const byLocation = toXY(stats.by_location ?? {});

  const statusColor: Record<string, string> = {
    case: "red",
    noncase: "green",
    pending: "gold",
    excluded: "default",
  };

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card>
            <Statistic title="符合病例定义" value={counts.case ?? 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="明确未发病" value={counts.noncase ?? 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="待核实" value={counts.pending ?? 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="范围外/排除" value={counts.excluded ?? 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="罹患率"
              value={ar.value == null ? "—" : (ar.value * 100).toFixed(1)}
              suffix={ar.value == null ? undefined : "%"}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="潜伏期中位数(小时)"
              value={stats.incubation?.median?.toFixed?.(1) ?? "—"}
            />
          </Card>
        </Col>
      </Row>

      {stats.warnings?.length > 0 && (
        <Alert type="warning" showIcon message={stats.warnings.join("；")} style={{ marginBottom: 16 }} />
      )}

      <Card title="流行曲线（按起病日期）" style={{ marginBottom: 16 }}>
        {byDate.length ? (
          <Line data={byDate} xField="label" yField="value" height={280} />
        ) : (
          <Empty description="缺少起病日期数据" />
        )}
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card title="按性别">
            {bySex.length ? <Column data={bySex} xField="label" yField="value" height={200} /> : <Empty />}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="按年龄组">
            {byAge.length ? <Column data={byAge} xField="label" yField="value" height={200} /> : <Empty />}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="按地点">
            {byLocation.length ? (
              <Column data={byLocation} xField="label" yField="value" height={200} />
            ) : (
              <Empty />
            )}
          </Card>
        </Col>
      </Row>

      <Card title="临床症状谱" style={{ marginBottom: 16 }}>
        <Table
          rowKey="symptom"
          size="small"
          dataSource={stats.symptoms ?? []}
          pagination={false}
          columns={[
            { title: "症状/体征", dataIndex: "symptom" },
            { title: "阳性人数", dataIndex: "numerator" },
            { title: "已知状态人数", dataIndex: "denominator" },
            {
              title: "比例",
              dataIndex: "value",
              render: (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`),
            },
            { title: "未知", dataIndex: "unknown" },
          ]}
        />
      </Card>

      <Card title="餐次与食品关联（四格表 + Fisher 精确检验）" style={{ marginBottom: 16 }}>
        <Table
          rowKey={(r: any) => `${r.meal_id}-${r.food_id}`}
          size="small"
          dataSource={stats.associations ?? []}
          pagination={false}
          columns={[
            { title: "餐次", dataIndex: "meal_id" },
            { title: "食品", dataIndex: "food_id" },
            { title: "效应量", dataIndex: "measure" },
            {
              title: "效应值",
              dataIndex: "effect",
              render: (v: any) => (v == null ? "—" : typeof v === "number" ? v.toFixed(2) : String(v)),
            },
            {
              title: "Fisher P",
              dataIndex: "p_fisher_two_sided",
              render: (v: any) => (v == null ? "—" : typeof v === "number" ? v.toFixed(4) : String(v)),
            },
          ]}
          expandable={{
            expandedRowRender: (r: any) => (
              <table style={{ borderCollapse: "collapse" }}>
                <tbody>
                  <tr>
                    <th style={cellStyle}>暴露</th>
                    <th style={cellStyle}>病例</th>
                    <th style={cellStyle}>未发病</th>
                  </tr>
                  <tr>
                    <td style={cellStyle}>进食</td>
                    <td style={cellStyle}>{r.table?.[0]?.[0]}</td>
                    <td style={cellStyle}>{r.table?.[0]?.[1]}</td>
                  </tr>
                  <tr>
                    <td style={cellStyle}>未进食</td>
                    <td style={cellStyle}>{r.table?.[1]?.[0]}</td>
                    <td style={cellStyle}>{r.table?.[1]?.[1]}</td>
                  </tr>
                </tbody>
              </table>
            ),
          }}
        />
      </Card>

      <Card title={`个案判定（${classified.length} 人）`}>
        <Table
          rowKey="person_id"
          size="small"
          dataSource={classified}
          pagination={{ pageSize: 20 }}
          columns={[
            { title: "人员", dataIndex: "person_id" },
            {
              title: "判定",
              dataIndex: "status",
              render: (v: string) => <Tag color={statusColor[v] ?? "default"}>{v}</Tag>,
            },
            { title: "理由", dataIndex: "reason" },
          ]}
        />
      </Card>
    </div>
  );
}
