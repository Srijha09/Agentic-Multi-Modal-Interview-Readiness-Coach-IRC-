# Integration Tests - Phase 12

## Running Tests

### Prerequisites
```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio
```

### Run All Tests
```bash
cd backend
pytest tests/test_integration.py -v
```

### Run Specific Test Classes
```bash
# Test end-to-end flows
pytest tests/test_integration.py::TestEndToEndFlow -v

# Test agent execution order
pytest tests/test_integration.py::TestAgentExecutionOrder -v

# Test no hallucination
pytest tests/test_integration.py::TestNoHallucination -v

# Test performance
pytest tests/test_integration.py::TestPerformance -v
```

### Run with Markers
```bash
# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance
```

## Test Coverage

### End-to-End Flows
- ✅ Skill Extraction → Gap Analysis → Planning
- ✅ Practice Generation → Evaluation → Mastery
- ✅ Adaptive Planning

### Agent Execution Order
- ✅ Services execute in correct sequence
- ✅ No circular dependencies

### No Hallucination
- ✅ Gaps tied to evidence
- ✅ Tasks tied to gaps

### Performance
- ✅ Plan generation benchmarks
- ✅ System metrics accuracy

## Notes

- Tests use a temporary database (created per test)
- LLM calls are not mocked (may require API keys)
- Some tests may take time due to LLM calls
- Performance thresholds can be adjusted based on your needs

