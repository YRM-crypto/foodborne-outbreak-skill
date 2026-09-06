import { FileTextOutlined, SearchOutlined } from "@ant-design/icons";
import {
  Drawer,
  Empty,
  Input,
  List,
  Segmented,
  Space,
  Spin,
  Tag,
  Tabs,
  Typography,
  message,
} from "antd";
import { useCallback, useEffect, useState } from "react";
import { kbDoc, kbDocs, kbSearch } from "../api/client";

const { Text, Paragraph } = Typography;

// 把 LightRAG chunk_id（如 standard:判定及处置技术指南-chunk-002）解析成可读来源名
function sourceLabel(chunkId: string): string {
  if (!chunkId) return "";
  const docId = chunkId.includes("-chunk-") ? chunkId.split("-chunk-")[0] : chunkId;
  const [kind, name] = docId.split(":");
  if (kind === "standard") return `规范《${name}》`;
  if (kind === "pathogen") return `致病因子·${name}`;
  if (kind === "report") return `结案报告·${name}`;
  if (kind === "monitoring") return `监测数据·第${name}批`;
  if (docId === "checklist") return "调查清单";
  return docId;
}

interface DocMeta {
  id: string;
  chars: number;
  preview: string;
}
interface KBChunk {
  content: string;
  file_path: string;
  chunk_id: string;
  reference_id: string;
}
interface KBReference {
  reference_id: string;
  file_path: string;
}

export default function KnowledgeView() {
  const [lib, setLib] = useState<string>("basis");
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docContent, setDocContent] = useState<{ id: string; content: string } | null>(null);

  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<any>(null);

  const loadDocs = useCallback(async (l: string) => {
    setDocsLoading(true);
    try {
      setDocs(await kbDocs(l));
    } catch (e: any) {
      message.error("加载文档失败：" + (e?.message ?? e));
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocs(lib);
  }, [lib, loadDocs]);

  const openDoc = async (id: string) => {
    try {
      setDocContent(await kbDoc(id, lib));
    } catch (e: any) {
      message.error("读取文档失败：" + (e?.message ?? e));
    }
  };

  const doSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      setSearchResult(await kbSearch(query.trim(), lib));
    } catch (e: any) {
      message.error("检索失败：" + (e?.message ?? e));
    } finally {
      setSearching(false);
    }
  };

  const chunks: KBChunk[] = searchResult?.result?.data?.chunks ?? [];
  const references: KBReference[] = searchResult?.result?.data?.references ?? [];

  return (
    <div>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Segmented
          options={[
            { label: "依据库（规范/病原/清单）", value: "basis" },
            { label: "案例库（报告/监测）", value: "cases" },
          ]}
          value={lib}
          onChange={(v) => {
            setLib(v as string);
            setSearchResult(null);
            setQuery("");
          }}
        />

        <Tabs
          items={[
            {
              key: "search",
              label: "检索",
              children: (
                <div>
                  <Input.Search
                    placeholder="输入问题，检索知识库并显示来源…"
                    enterButton={<SearchOutlined />}
                    loading={searching}
                    onSearch={doSearch}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    style={{ maxWidth: 640 }}
                  />
                  <div style={{ marginTop: 16 }}>
                    {searching ? (
                      <Spin />
                    ) : !searchResult ? (
                      <Empty description="输入问题开始检索" />
                    ) : (
                      <Space direction="vertical" size={12} style={{ width: "100%" }}>
                        {chunks.length === 0 && <Empty description="未检索到相关内容" />}
                        <List
                          itemLayout="vertical"
                          dataSource={chunks}
                          renderItem={(c) => (
                            <List.Item>
                              <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 8 }}>
                                {c.content}
                              </Paragraph>
                              <Space size={8} wrap>
                                <Tag color="blue">{sourceLabel(c.chunk_id)}</Tag>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  {c.chunk_id}
                                </Text>
                              </Space>
                            </List.Item>
                          )}
                        />
                        {references.length > 0 && (
                          <div>
                            <Text strong>引用来源</Text>
                            <List
                              size="small"
                              dataSource={references}
                              renderItem={(r) => (
                                <List.Item>
                                  <Space>
                                    <Text type="secondary">{r.reference_id}</Text>
                                    <Tag>{r.file_path}</Tag>
                                  </Space>
                                </List.Item>
                              )}
                            />
                          </div>
                        )}
                      </Space>
                    )}
                  </div>
                </div>
              ),
            },
            {
              key: "browse",
              label: "浏览",
              children: (
                <List
                  loading={docsLoading}
                  dataSource={docs}
                  renderItem={(d) => (
                    <List.Item actions={[<a onClick={() => openDoc(d.id)}>查看全文</a>]}>
                      <List.Item.Meta
                        avatar={<FileTextOutlined style={{ fontSize: 20 }} />}
                        title={<Text strong>{d.id}</Text>}
                        description={`${d.chars} 字 · ${d.preview}${
                          d.preview.length >= 200 ? "…" : ""
                        }`}
                      />
                    </List.Item>
                  )}
                />
              ),
            },
          ]}
        />
      </Space>

      <Drawer
        title={docContent?.id}
        open={!!docContent}
        onClose={() => setDocContent(null)}
        width={720}
      >
        <Paragraph style={{ whiteSpace: "pre-wrap" }}>{docContent?.content}</Paragraph>
      </Drawer>
    </div>
  );
}
