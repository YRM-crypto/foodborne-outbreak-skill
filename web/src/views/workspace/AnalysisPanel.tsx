import { Column, Line } from "@ant-design/plots";
import { Alert, Card, Col, Empty, Row, Space, Statistic, Table, Tag } from "antd";
import { CLASS_STATUSES } from "../../constants";

function toXY(obj: Record<string, number>) {
  return Object.entries(obj).map(([label, value]) => ({ label, value }));
}

const cellStyle: React.CSSProperties = {
  border: "1px solid #d9d9d9",
  padding: "4px 12px",
  textAlign: "center",
};

const STATUS_COLOR: Record<string, string> = {
  确诊: "red",
  可能: "orange",
  疑似: "gold",
  未发病: "green",
  排除: "default",
  待定: "blue",
};

export default function AnalysisPanel({ analysis }: { analysis: any }) {
  if (!analysis) return <Empty description="暂无分析结果（请先在「病例定义」与「个案调查」录入数据）" />;

  const stats = analysis.stats ?? {};
  const checks: any[] = analysis.checks ?? [];
  const classified = stats.classified ?? [];
  const counts = stats.counts ?? {};
  const ar = stats.attack_rate ?? {};

  const byDate = toXY(stats.by_date ?? {});
  const bySex = toXY(stats.by_sex ?? {});
  const byLocation = toXY(stats.by_location ?? {});
  const ageGroups = (stats.age_groups ?? []).map((g: any) => ({ label: g.label, value: g.cases }));

  const warnChecks = checks.filter((c) => c.level === "warn" || c.level === "error");
  const infoChecks = checks.filter((c) => c.level === "info");

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card><Statistic title="确诊" value={counts["确诊"] ?? 0} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="可能" value={counts["可能"] ?? 0} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="疑似" value={counts["疑似"] ?? 0} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="未发病" value={counts["未发病"] ?? 0} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="排除/待定" value={(counts["排除"] ?? 0) + (counts["待定"] ?? 0)} /></Card>
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
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="病例合计" value={stats.case_count ?? 0} /></Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="潜伏期中位数(小时)"
              value={stats.incubation?.median?.toFixed?.(1) ?? "—"}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="研究设计"
              value={stats.study_design === "case-control" ? "病例对照(OR)" : "队列(RR)"}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="暴露人数" value={stats.population?.size ?? "—"} />
          </Card>
        </Col>
      </Row>

      {(stats.warnings?.length > 0) && (
        <Alert type="warning" showIcon message={stats.warnings.join("；")} style={{ marginBottom: 16 }} />
      )}

      {warnChecks.length > 0 && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="校验发现（需处理）"
          description={
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {warnChecks.map((c) => (
                <li key={c.code}>{c.title}：{c.detail}</li>
              ))}
            </ul>
          }
        />
      )}

      {infoChecks.length > 0 && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="提示"
          description={
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {infoChecks.map((c) => (
                <li key={c.code}>{c.title}：{c.detail}</li>
              ))}
            </ul>
          }
        />
      )}

      <Card title="流行曲线（按起病日期）" style={{ marginBottom: 16 }}>
        {byDate.length ? (
          <Line data={byDate} xField="label" yField="value" height={260} />
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
          <Card title="按年龄段">
            {ageGroups.length ? <Column data={ageGroups} xField="label" yField="value" height={200} /> : <Empty />}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="按地点">
            {byLocation.length ? <Column data={byLocation} xField="label" yField="value" height={200} /> : <Empty />}
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

      <Card title="食品关联（四格表 + Fisher 精确检验）" style={{ marginBottom: 16 }}>
        <Table
          rowKey="food_id"
          size="small"
          dataSource={stats.associations ?? []}
          pagination={false}
          columns={[
            { title: "食品", dataIndex: "food_id" },
            { title: "效应量", dataIndex: "measure" },
            {
              title: "效应值",
              dataIndex: "effect",
              render: (v: any) => (v == null ? "—" : typeof v === "number" ? v.toFixed(2) : String(v)),
            },
            {
              title: "95%CI",
              dataIndex: "ci95",
              render: (v: number[] | null) =>
                v && v.length === 2 ? `${v[0].toFixed(2)}–${v[1].toFixed(2)}` : "—",
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
        <Space style={{ marginBottom: 8 }}>
          {CLASS_STATUSES.map((s) => (
            <Tag key={s} color={STATUS_COLOR[s] ?? "default"}>{s} {counts[s] ?? 0}</Tag>
          ))}
        </Space>
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
              render: (v: string) => <Tag color={STATUS_COLOR[v] ?? "default"}>{v}</Tag>,
            },
            { title: "理由", dataIndex: "reason" },
          ]}
        />
      </Card>
    </div>
  );
}
