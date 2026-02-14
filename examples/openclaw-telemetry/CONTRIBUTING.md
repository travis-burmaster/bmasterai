# Contributing to OpenClaw Telemetry Integration

Thank you for your interest in improving the OpenClaw telemetry integration!

## Development Setup

### Prerequisites

- Python 3.8+
- OpenClaw installed ([openclaw.ai](https://openclaw.ai))
- Git

### Local Development

1. Fork and clone the repo:
```bash
git clone https://github.com/YOUR_USERNAME/bmasterai.git
cd bmasterai/examples/openclaw-telemetry
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install black flake8 pytest  # Development tools
```

4. Make your changes

5. Test locally:
```bash
# Parse test sessions
python session_parser.py

# Run dashboard
streamlit run dashboard.py

# Verify data looks correct
```

## Code Style

We follow PEP 8 with Black formatting:

```bash
# Format code
black *.py

# Check style
flake8 *.py
```

## Testing

### Manual Testing Checklist

- [ ] Parser handles missing/incomplete session files gracefully
- [ ] Dashboard loads without errors
- [ ] All time filters work correctly (all/today/week/month)
- [ ] Charts render properly
- [ ] Tool usage tracks correctly
- [ ] Cost calculations are accurate
- [ ] Auto-refresh works
- [ ] Database schema handles edge cases

### Test with Various OpenClaw Scenarios

- [ ] Main conversation sessions
- [ ] Cron job sessions
- [ ] Sub-agent sessions
- [ ] Mixed model usage (if applicable)
- [ ] Sessions with many tool calls
- [ ] Sessions with high token counts

## Pull Request Process

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "feat: descriptive message about your change"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

3. Push to your fork:
```bash
git push origin feature/your-feature-name
```

4. Open a Pull Request on GitHub

5. Describe your changes:
   - What problem does this solve?
   - How did you test it?
   - Screenshots if UI changes
   - Breaking changes (if any)

## Enhancement Ideas

### High Priority

- [ ] Add webhook support for real-time session ingestion
- [ ] Implement cost alert thresholds with notifications
- [ ] Add session replay/debugging mode
- [ ] Export reports (PDF, CSV, JSON)

### Dashboard Improvements

- [ ] More chart types (heatmaps, scatter plots)
- [ ] Comparative analysis (compare time periods)
- [ ] Custom date ranges
- [ ] Session search and filtering
- [ ] Drill-down into individual sessions

### Parser Enhancements

- [ ] Incremental parsing (only new sessions)
- [ ] Background parsing (file watcher)
- [ ] Multi-directory support
- [ ] Compressed session support
- [ ] Error recovery and logging

### Integration Features

- [ ] Prometheus exporter
- [ ] Grafana dashboard templates
- [ ] Slack/Discord webhooks for alerts
- [ ] OpenTelemetry tracing
- [ ] BMasterAI reasoning log integration

## Documentation

When adding features, update:

1. **README.md** - Main documentation
2. **QUICKSTART.md** - If it affects quick start
3. **Code comments** - Docstrings for functions/classes
4. **Examples** - Add usage examples if applicable

## Questions?

- Open a GitHub Discussion
- Ask in OpenClaw Discord: [discord.gg/clawd](https://discord.gg/clawd)
- Email: travis@burmaster.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
