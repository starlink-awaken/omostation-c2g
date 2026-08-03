"""
test_parser_robust.py — narrative markdown 鲁棒提取测试

覆盖场景：
1. markdown ```json 块提取 (优先级 1)
2. 纯 narrative 失败处理 (回退到 mock)
3. 直接 JSON 数组/对象 (老路径，优先级 2)
"""

from c2g.llm import _mock_extract, _parse_json_result


class TestParseJsonResult:
    """_parse_json_result 单元测试"""

    def test_markdown_json_block(self):
        """优先级 1: markdown ```json 块提取"""
        content = """
        这里是 narrative 内容。

        ```json
        [
          {
            "title": "任务A",
            "description": "描述A",
            "task_type": "feature",
            "risk_level": "L0",
            "cognitive_cartridge": "GSD-V1",
            "deliverables": ["文件1.md"],
            "evidence_required": ["通过校验"],
            "test_plan": ["跑通流程"]
          }
        ]
        ```
        """
        result = _parse_json_result(content)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "任务A"

    def test_markdown_json_block_non_greedy(self):
        """优先级 1: 非贪婪匹配，多个块只取第一个"""
        content = """
        ```json
        [{"title": "第一个", "task_type": "feature", "risk_level": "L0", "cognitive_cartridge": "", "deliverables": [], "evidence_required": [], "test_plan": []}]
        ```
        其他内容
        ```json
        [{"title": "第二个"}]
        ```
        """
        result = _parse_json_result(content)
        assert result is not None
        assert result[0]["title"] == "第一个"

    def test_narrative_only_fallback(self):
        """纯 narrative 无 JSON → 回退到 _mock_extract"""
        content = """
        这是一个点子提案，我们想要做一个新的功能。
        需要支持认知卡带挂载机制。
        """
        result = _parse_json_result(content)
        # _parse_json_result 对纯 narrative 返回 None
        assert result is None

    def test_direct_json_array(self):
        """优先级 2: 直接 JSON 数组 (老路径)"""
        content = '[{"title": "任务B", "task_type": "bugfix", "risk_level": "L1", "cognitive_cartridge": "", "deliverables": [], "evidence_required": [], "test_plan": []}]'
        result = _parse_json_result(content)
        assert result is not None
        assert isinstance(result, list)
        assert result[0]["title"] == "任务B"

    def test_direct_json_object(self):
        """优先级 2: 直接 JSON 对象 (包装为单元素列表)"""
        content = '{"title": "任务C", "task_type": "refactor", "risk_level": "L0", "cognitive_cartridge": "", "deliverables": [], "evidence_required": [], "test_plan": []}'
        result = _parse_json_result(content)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "任务C"

    def test_json_with_trailing_garbage_truncated(self):
        """优先级 2: JSON 末尾有噪音，尝试裁切"""
        content = '[{"title": "任务D", "task_type": "feature", "risk_level": "L0", "cognitive_cartridge": "", "deliverables": [], "evidence_required": [], "test_plan": []}]```'
        result = _parse_json_result(content)
        assert result is not None
        assert result[0]["title"] == "任务D"

    def test_whitespace_only(self):
        """空白内容 → None"""
        assert _parse_json_result("   \n\n  ") is None

    def test_invalid_json_returns_none(self):
        """完全无效 JSON → None"""
        assert _parse_json_result("```json\nnot json at all\n```") is None


class TestMockExtract:
    """_mock_extract 兜底测试"""

    def test_mock_returns_list(self):
        """mock 回退返回列表"""
        result = _mock_extract("随便什么内容")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "title" in result[0]
        assert "deliverables" in result[0]
