# Repository Analysis Guide with BMasterAI

## Overview

This comprehensive guide explains how to use BMasterAI for repository analysis, including MCP (Model Context Protocol) integration and AI agent workflows. BMasterAI provides powerful capabilities for understanding codebases, analyzing project structures, and generating insights for development teams.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [BMasterAI Setup](#bmasterai-setup)
3. [Repository Connection](#repository-connection)
4. [Analysis Workflows](#analysis-workflows)
5. [MCP Integration](#mcp-integration)
6. [AI Agent Configuration](#ai-agent-configuration)
7. [Advanced Analysis Techniques](#advanced-analysis-techniques)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Node.js (v18 or higher)
- Git
- BMasterAI account and API key
- GitHub account with repository access
- Python 3.8+ (for MCP server)

### Required Knowledge
- Basic understanding of Git and GitHub
- Familiarity with command line interfaces
- Understanding of software development workflows
- Basic knowledge of AI/ML concepts

## BMasterAI Setup

### 1. Account Configuration

```bash
# Install BMasterAI CLI
npm install -g bmasterai-cli

# Configure API credentials
bmasterai config set-api-key YOUR_API_KEY
bmasterai config set-workspace YOUR_WORKSPACE_ID
```

### 2. Environment Variables

Create a `.env` file in your project root:

```env
BMASTERAI_API_KEY=your_api_key_here
BMASTERAI_WORKSPACE_ID=your_workspace_id
GITHUB_TOKEN=your_github_token
MCP_SERVER_PORT=3001
```

### 3. Project Initialization

```bash
# Initialize BMasterAI in your project
bmasterai init

# Install required dependencies
npm install @bmasterai/sdk @bmasterai/mcp-client
```

## Repository Connection

### 1. GitHub Integration

```javascript
// config/github-integration.js
const { BMasterAI } = require('@bmasterai/sdk');
const { Octokit } = require('@octokit/rest');

class GitHubIntegration {
  constructor(apiKey, githubToken) {
    this.bmasterai = new BMasterAI({ apiKey });
    this.octokit = new Octokit({ auth: githubToken });
  }

  async connectRepository(owner, repo) {
    try {
      // Fetch repository metadata
      const { data: repoData } = await this.octokit.rest.repos.get({
        owner,
        repo
      });

      // Register repository with BMasterAI
      const connection = await this.bmasterai.repositories.connect({
        provider: 'github',
        owner,
        repo,
        metadata: {
          language: repoData.language,
          size: repoData.size,
          stars: repoData.stargazers_count,
          forks: repoData.forks_count
        }
      });

      return connection;
    } catch (error) {
      throw new Error(`Failed to connect repository: ${error.message}`);
    }
  }
}

module.exports = GitHubIntegration;
```

### 2. Repository Scanning

```javascript
// utils/repository-scanner.js
class RepositoryScanner {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async scanRepository(repositoryId) {
    const scanConfig = {
      includePatterns: [
        '**/*.js',
        '**/*.ts',
        '**/*.py',
        '**/*.md',
        '**/package.json',
        '**/requirements.txt'
      ],
      excludePatterns: [
        'node_modules/**',
        '.git/**',
        'dist/**',
        'build/**'
      ],
      analysisDepth: 'comprehensive'
    };

    const scanResult = await this.bmasterai.repositories.scan(
      repositoryId,
      scanConfig
    );

    return scanResult;
  }

  async getFileStructure(repositoryId) {
    return await this.bmasterai.repositories.getStructure(repositoryId);
  }
}

module.exports = RepositoryScanner;
```

## Analysis Workflows

### 1. Code Quality Analysis

```javascript
// workflows/code-quality-analysis.js
class CodeQualityAnalysis {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzeCodeQuality(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'code_quality',
      parameters: {
        checkComplexity: true,
        checkDuplication: true,
        checkSecurity: true,
        checkPerformance: true,
        generateRecommendations: true
      }
    });

    return this.processQualityResults(analysis);
  }

  processQualityResults(analysis) {
    return {
      overallScore: analysis.metrics.overallScore,
      complexity: analysis.metrics.complexity,
      duplication: analysis.metrics.duplication,
      security: analysis.security,
      recommendations: analysis.recommendations,
      hotspots: analysis.hotspots
    };
  }
}
```

### 2. Architecture Analysis

```javascript
// workflows/architecture-analysis.js
class ArchitectureAnalysis {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzeArchitecture(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'architecture',
      parameters: {
        identifyPatterns: true,
        analyzeDependencies: true,
        detectAntiPatterns: true,
        generateDiagrams: true
      }
    });

    return {
      patterns: analysis.patterns,
      dependencies: analysis.dependencies,
      antiPatterns: analysis.antiPatterns,
      diagrams: analysis.diagrams,
      recommendations: analysis.recommendations
    };
  }

  async generateArchitectureDiagram(repositoryId) {
    return await this.bmasterai.diagrams.generate({
      repositoryId,
      type: 'architecture',
      format: 'mermaid'
    });
  }
}
```

### 3. Documentation Analysis

```javascript
// workflows/documentation-analysis.js
class DocumentationAnalysis {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzeDocumentation(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'documentation',
      parameters: {
        checkCoverage: true,
        checkQuality: true,
        identifyGaps: true,
        generateSuggestions: true
      }
    });

    return {
      coverage: analysis.coverage,
      quality: analysis.quality,
      gaps: analysis.gaps,
      suggestions: analysis.suggestions
    };
  }

  async generateMissingDocs(repositoryId, gaps) {
    const docGeneration = await this.bmasterai.documentation.generate({
      repositoryId,
      targets: gaps,
      style: 'comprehensive'
    });

    return docGeneration;
  }
}
```

## MCP Integration

### 1. MCP Server Setup

```python
# mcp-server/repository_server.py
import asyncio
import json
from typing import Dict, List, Any
from mcp import Server, types
from bmasterai import BMasterAI

class RepositoryMCPServer:
    def __init__(self, api_key: str):
        self.bmasterai = BMasterAI(api_key=api_key)
        self.server = Server("repository-analysis")
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            return [
                types.Resource(
                    uri="repository://analysis",
                    name="Repository Analysis",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="repository://structure",
                    name="Repository Structure",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if uri == "repository://analysis":
                return await self.get_analysis_data()
            elif uri == "repository://structure":
                return await self.get_structure_data()
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="analyze_repository",
                    description="Analyze repository code quality and architecture",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository_id": {"type": "string"},
                            "analysis_type": {"type": "string"}
                        },
                        "required": ["repository_id", "analysis_type"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            if name == "analyze_repository":
                result = await self.analyze_repository(
                    arguments["repository_id"],
                    arguments["analysis_type"]
                )
                return [types.TextContent(type="text", text=json.dumps(result))]

    async def analyze_repository(self, repo_id: str, analysis_type: str):
        analysis = await self.bmasterai.analysis.create({
            "repositoryId": repo_id,
            "type": analysis_type
        })
        return analysis

    async def run(self, port: int = 3001):
        await self.server.run(port=port)
```

### 2. MCP Client Integration

```javascript
// mcp-client/repository-client.js
const { MCPClient } = require('@bmasterai/mcp-client');

class RepositoryMCPClient {
  constructor(serverUrl) {
    this.client = new MCPClient(serverUrl);
  }

  async connect() {
    await this.client.connect();
  }

  async analyzeRepository(repositoryId, analysisType) {
    const result = await this.client.callTool('analyze_repository', {
      repository_id: repositoryId,
      analysis_type: analysisType
    });

    return JSON.parse(result[0].text);
  }

  async getRepositoryStructure() {
    const resource = await this.client.readResource('repository://structure');
    return JSON.parse(resource);
  }

  async getAnalysisData() {
    const resource = await this.client.readResource('repository://analysis');
    return JSON.parse(resource);
  }
}

module.exports = RepositoryMCPClient;
```

## AI Agent Configuration

### 1. Analysis Agent

```javascript
// agents/analysis-agent.js
class AnalysisAgent {
  constructor(bmasterai, mcpClient) {
    this.bmasterai = bmasterai;
    this.mcpClient = mcpClient;
    this.capabilities = [
      'code_analysis',
      'architecture_review',
      'security_scan',
      'performance_analysis'
    ];
  }

  async createAgent(repositoryId) {
    const agent = await this.bmasterai.agents.create({
      name: 'Repository Analysis Agent',
      type: 'analysis',
      capabilities: this.capabilities,
      context: {
        repositoryId,
        analysisDepth: 'comprehensive'
      },
      instructions: `
        You are a repository analysis agent. Your role is to:
        1. Analyze code quality and architecture
        2. Identify potential issues and improvements
        3. Generate actionable recommendations
        4. Provide detailed reports with evidence
      `
    });

    return agent;
  }

  async runAnalysis(agentId, analysisType) {
    const task = await this.bmasterai.agents.createTask(agentId, {
      type: 'analysis',
      parameters: {
        analysisType,
        generateReport: true,
        includeRecommendations: true
      }
    });

    return await this.bmasterai.agents.waitForTask(task.id);
  }
}
```

### 2. Recommendation Agent

```javascript
// agents/recommendation-agent.js
class RecommendationAgent {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async generateRecommendations(analysisResults) {
    const agent = await this.bmasterai.agents.create({
      name: 'Recommendation Agent',
      type: 'recommendation',
      instructions: `
        Based on the analysis results, generate specific, actionable recommendations.
        Prioritize recommendations by impact and effort required.
        Provide implementation guidance for each recommendation.
      `
    });

    const task = await this.bmasterai.agents.createTask(agent.id, {
      type: 'recommendation',
      input: analysisResults,
      parameters: {
        prioritize: true,
        includeImplementationSteps: true,
        estimateEffort: true
      }
    });

    return await this.bmasterai.agents.waitForTask(task.id);
  }
}
```

## Advanced Analysis Techniques

### 1. Dependency Analysis

```javascript
// analysis/dependency-analyzer.js
class DependencyAnalyzer {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzeDependencies(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'dependencies',
      parameters: {
        checkVulnerabilities: true,
        checkOutdated: true,
        analyzeUsage: true,
        suggestAlternatives: true
      }
    });

    return {
      vulnerabilities: analysis.vulnerabilities,
      outdated: analysis.outdated,
      unused: analysis.unused,
      alternatives: analysis.alternatives,
      dependencyGraph: analysis.graph
    };
  }

  async generateDependencyReport(dependencies) {
    return await this.bmasterai.reports.generate({
      type: 'dependency_report',
      data: dependencies,
      format: 'detailed'
    });
  }
}
```

### 2. Performance Analysis

```javascript
// analysis/performance-analyzer.js
class PerformanceAnalyzer {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzePerformance(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'performance',
      parameters: {
        identifyBottlenecks: true,
        analyzeComplexity: true,
        checkMemoryUsage: true,
        suggestOptimizations: true
      }
    });

    return {
      bottlenecks: analysis.bottlenecks,
      complexity: analysis.complexity,
      memoryIssues: analysis.memoryIssues,
      optimizations: analysis.optimizations
    };
  }
}
```

### 3. Security Analysis

```javascript
// analysis/security-analyzer.js
class SecurityAnalyzer {
  constructor(bmasterai) {
    this.bmasterai = bmasterai;
  }

  async analyzeSecurityVulnerabilities(repositoryId) {
    const analysis = await this.bmasterai.analysis.create({
      repositoryId,
      type: 'security',
      parameters: {
        scanVulnerabilities: true,
        checkSecrets: true,
        analyzePermissions: true,
        validateInputs: true
      }
    });

    return {
      vulnerabilities: analysis.vulnerabilities,
      secrets: analysis.secrets,
      permissions: analysis.permissions,
      inputValidation: analysis.inputValidation,
      recommendations: analysis.recommendations
    };
  }
}
```

## Best Practices

### 1. Analysis Configuration

```javascript
// config/analysis-best-practices.js
const ANALYSIS_BEST_PRACTICES = {
  scanning: {
    // Include essential file types
    includePatterns: [
      '**/*.{js,ts,jsx,tsx}',
      '**/*.{py,java,cpp,c}',
      '**/*.{md,rst,txt}',
      '**/package.json',
      '**/requirements.txt',
      '**/Dockerfile',
      '**/*.yml',
      '**/*.yaml'
    ],
    
    // Exclude unnecessary files
    excludePatterns: [
      'node_modules/**',
      '.git/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '**/*.log',
      '**/*.tmp'
    ],
    
    // Optimal batch size for large repositories
    batchSize: 100,
    
    // Timeout settings
    timeout: 300000 // 5 minutes
  },
  
  analysis: {
    // Progressive analysis depth
    depth: 'comprehensive',
    
    // Enable caching for repeated analyses
    enableCaching: true,
    
    // Parallel processing
    parallelProcessing: true,
    maxConcurrency: 5
  }
};

module.exports = ANALYSIS_BEST_PRACTICES;
```

### 2. Error Handling

```javascript
// utils/error-handler.js
class AnalysisErrorHandler {
  static async handleAnalysisError(error, context) {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString()
    };

    // Log error
    console.error('Analysis Error:', errorInfo);

    // Determine recovery strategy
    if (error.code === 'RATE_LIMIT_EXCEEDED') {
      return await this.handleRateLimit(context);
    } else if (error.code === 'REPOSITORY_NOT_FOUND') {
      return await this.handleRepositoryNotFound(context);
    } else if (error.code === 'ANALYSIS_TIMEOUT') {
      return await this.handleTimeout(context);
    }

    throw error;
  }

  static async handleRateLimit(context) {
    // Implement exponential backoff
    const delay = Math.min(1000 * Math.pow(2, context.retryCount || 0), 30000);
    await new Promise(resolve => setTimeout(resolve, delay));
    return { retry: true, delay };
  }

  static async handleRepositoryNotFound(context) {
    // Verify repository access and permissions
    return { 
      retry: false, 
      error: 'Repository not accessible. Check permissions.' 
    };
  }

  static async handleTimeout(context) {
    // Reduce analysis scope and retry
    return { 
      retry: true, 
      reducedScope: true 
    };
  }
}

module.exports = AnalysisErrorHandler;
```

### 3. Performance Optimization

```javascript
// utils/performance-optimizer.js
class PerformanceOptimizer {
  static optimizeAnalysisConfig(repositorySize, complexity) {
    const config = {
      batchSize: 50,
      maxConcurrency: 3,
      analysisDepth: 'standard'
    };

    // Adjust based on repository size
    if (repositorySize > 10000) { // Large repository
      config.batchSize = 25;
      config.maxConcurrency = 2;
      config.analysisDepth = 'focused';
    } else if (repositorySize < 1000) { // Small repository
      config.batchSize = 100;
      config.maxConcurrency = 5;
      config.analysisDepth = 'comprehensive';
    }

    // Adjust based on complexity
    if (complexity > 0.8) {
      config.analysisDepth = 'focused';
      config.maxConcurrency = Math.max(1, config.maxConcurrency - 1);
    }

    return config;
  }

  static async measureAnalysisPerformance(analysisFunction, ...args) {
    const startTime = Date.now();
    const startMemory = process.memoryUsage();

    try {
      const result = await analysisFunction(...args);
      const endTime = Date.now();
      const endMemory = process.memoryUsage();

      const metrics = {
        duration: endTime - startTime,
        memoryDelta: {
          rss: endMemory.rss - startMemory.rss,
          heapUsed: endMemory.heapUsed - startMemory.heapUsed
        }
      };

      return { result, metrics };
    } catch (error) {
      const endTime = Date.now();
      throw new Error(`Analysis failed after ${endTime - startTime}ms: ${error.message}`);
    }
  }
}

module.exports = PerformanceOptimizer;
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Issues

```javascript
// troubleshooting/connection-diagnostics.js
class ConnectionDiagnostics {
  static async diagnoseConnection(bmasterai) {
    const diagnostics = {
      apiConnection: false,
      authentication: false,
      permissions: false,
      networkLatency: null
    };

    try {
      // Test API connection
      const startTime = Date.now();
      await bmasterai.health.check();
      diagnostics.apiConnection = true;
      diagnostics.networkLatency = Date.now() - startTime;

      // Test authentication
      await bmasterai.user.profile();
      diagnostics.authentication = true;

      // Test permissions
      await bmasterai.repositories.list({ limit: 1 });
      diagnostics.permissions = true;

    } catch (error) {
      console.error('Connection diagnostic failed:', error.message);
    }

    return diagnostics;
  }
}
```

#### 2. Analysis Failures

```javascript
// troubleshooting/analysis-diagnostics.js
class AnalysisDiagnostics {
  static async diagnoseAnalysisFailure(repositoryId, error) {
    const diagnosis = {
      repositoryAccess: false,
      filePermissions: false,
      resourceLimits: false,
      suggestions: []
    };

    // Check repository access
    try {
      await this.checkRepositoryAccess(repositoryId);
      diagnosis.repositoryAccess = true;
    } catch (e) {
      diagnosis.suggestions.push('Verify repository permissions and access tokens');
    }

    // Check resource limits
    if (error.message.includes('timeout') || error.message.includes('limit')) {
      diagnosis.resourceLimits = true;
      diagnosis.suggestions.push('Reduce analysis scope or increase timeout limits');
    }

    return diagnosis;
  }
}
```

### Debug Mode

```javascript
// utils/debug-logger.js
class DebugLogger {
  constructor(enabled = false) {
    this.enabled = enabled;
  }

  log(level, message, data = null) {
    if (!this.enabled) return;

    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };

    console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
    if (data) {
      console.log(JSON.stringify(data, null, 2));
    }
  }

  debug(message, data) {
    this.log('debug', message, data);
  }

  info(message, data) {
    this.log('