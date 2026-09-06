import {
  DatabaseOutlined,
  DashboardOutlined,
  FileTextOutlined,
  ReadOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import { Layout, Menu } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

const { Sider, Header, Content } = Layout;

const items = [
  { key: "/cases", icon: <DatabaseOutlined />, label: "案例总览" },
  { key: "/knowledge", icon: <ReadOutlined />, label: "知识库" },
  { key: "/workspace", icon: <DashboardOutlined />, label: "调查工作区" },
  { key: "/report", icon: <FileTextOutlined />, label: "报告" },
  { key: "/assistant", icon: <RobotOutlined />, label: "AI 助手" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const selected =
    items.map((i) => i.key).find((k) => location.pathname.startsWith(k)) ?? "/cases";

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider theme="dark" width={200}>
        <div style={{ color: "#fff", padding: 16, fontSize: 15, fontWeight: 600 }}>
          暴发调查工作台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selected]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{ background: "#fff", paddingInline: 24, borderBottom: "1px solid #f0f0f0" }}
        >
          <span style={{ fontSize: 16, fontWeight: 600 }}>食源性疾病暴发调查助手</span>
        </Header>
        <Content style={{ padding: 24, overflow: "auto" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
