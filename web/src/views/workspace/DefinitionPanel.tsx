import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Switch, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { setDefinition } from "../../api/client";
import { SYMPTOMS } from "../../constants";

export default function DefinitionPanel({ state, eventId, onRefresh }: any) {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const definition = state.definition;

  useEffect(() => {
    form.setFieldsValue({
      label: definition?.label ?? "",
      text: definition?.text ?? "",
      start: definition?.start ?? "",
      end: definition?.end ?? "",
      locations: definition?.locations ?? [],
      populations: definition?.populations ?? [],
      symptoms_any: definition?.symptoms_any ?? [],
      minimum_symptoms: definition?.minimum_symptoms ?? 1,
      require_epi_link: !!definition?.probable?.require_epi_link,
      require_lab: !!definition?.confirmed?.require_lab,
    });
  }, [definition, form]);

  const onSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const payload = {
        label: values.label,
        text: values.text,
        start: values.start,
        end: values.end,
        locations: values.locations ?? [],
        populations: values.populations ?? [],
        symptoms_any: values.symptoms_any ?? [],
        minimum_symptoms: values.minimum_symptoms ?? 1,
        probable: { require_epi_link: !!values.require_epi_link },
        confirmed: { require_lab: !!values.require_lab },
      };
      await setDefinition(eventId, payload);
      message.success("病例定义已保存（新版本，个案将据此重判）");
      onRefresh();
    } catch (e: any) {
      message.error("保存失败：" + (e?.response?.data?.detail ?? e?.message ?? e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="病例定义决定个案如何判定：疑似＝时间/地区/人群范围＋症状达标；可能＝＋与确诊有共同暴露；确诊＝＋致病因子检验阳性。"
      />
      <Card
        title={
          <Space>
            病例定义
            <Tag color="blue">第 {definition?.version ?? 1} 版</Tag>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="label" label="定义名称">
            <Input placeholder="如 疑似病例" />
          </Form.Item>
          <Form.Item name="text" label="定义文本">
            <Input.TextArea
              rows={2}
              placeholder="如 6月29日12时聚餐后，24小时排便3次及以上且粪便性状异常，或腹泻伴发热、呕吐者"
            />
          </Form.Item>
          <Space size={16} style={{ display: "flex", marginBottom: 8 }} wrap>
            <Form.Item name="start" label="起病时间范围（起）" style={{ marginBottom: 0 }}>
              <Input placeholder="YYYY-MM-DDTHH:mm:ss" style={{ width: 240 }} />
            </Form.Item>
            <Form.Item name="end" label="起病时间范围（止）" style={{ marginBottom: 0 }}>
              <Input placeholder="YYYY-MM-DDTHH:mm:ss" style={{ width: 240 }} />
            </Form.Item>
          </Space>
          <Form.Item name="locations" label="地区范围（留空＝不限）">
            <Select mode="tags" placeholder="如 某食堂 / 某厂" />
          </Form.Item>
          <Form.Item name="populations" label="人群范围（留空＝不限）">
            <Select mode="tags" placeholder="如 某中学师生" />
          </Form.Item>
          <Form.Item name="symptoms_any" label="纳入症状（满足任一即可）">
            <Select mode="multiple" placeholder="选择症状" options={SYMPTOMS.map((s) => ({ value: s, label: s }))} />
          </Form.Item>
          <Form.Item name="minimum_symptoms" label="最低症状数">
            <InputNumber min={1} />
          </Form.Item>
          <Space size={32} wrap>
            <Form.Item name="require_epi_link" label="「可能」需流行病学关联" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="require_lab" label="「确诊」需实验室阳性" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
          <Button type="primary" loading={saving} onClick={onSave}>
            保存病例定义
          </Button>
        </Form>
      </Card>
    </div>
  );
}
