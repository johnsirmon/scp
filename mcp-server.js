#!/usr/bin/env node
/**
 * SCP Model Context Protocol Server
 * Provides case context to VSCode/LLMs via MCP
 */

const { spawn } = require('child_process');
const path = require('path');

class SCPMCPServer {
  constructor() {
    this.scpPath = path.join(__dirname, 'scp.js');
  }

  async handleRequest(method, params) {
    switch (method) {
      case 'tools/list':
        return this.listTools();
      case 'tools/call':
        return this.callTool(params);
      case 'resources/list':
        return this.listResources();
      case 'resources/read':
        return this.readResource(params);
      default:
        throw new Error(`Unknown method: ${method}`);
    }
  }

  listTools() {
    return {
      tools: [
        {
          name: 'scp_search',
          description: 'Search for similar support cases',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query (symptoms, errors, keywords)'
              },
              limit: {
                type: 'number',
                description: 'Maximum number of results (default: 5)',
                default: 5
              }
            },
            required: ['query']
          }
        },
        {
          name: 'scp_get_context',
          description: 'Get formatted context for specific cases',
          inputSchema: {
            type: 'object',
            properties: {
              case_ids: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of case IDs to retrieve context for'
              }
            },
            required: ['case_ids']
          }
        },
        {
          name: 'scp_add_case',
          description: 'Add a new support case to the database',
          inputSchema: {
            type: 'object',
            properties: {
              content: {
                type: 'string',
                description: 'Case content (ICM, logs, etc.)'
              },
              case_id: {
                type: 'string',
                description: 'Optional case ID'
              }
            },
            required: ['content']
          }
        }
      ]
    };
  }

  async callTool(params) {
    const { name, arguments: args } = params;

    switch (name) {
      case 'scp_search':
        return this.searchCases(args.query, args.limit);
      case 'scp_get_context':
        return this.getContext(args.case_ids);
      case 'scp_add_case':
        return this.addCase(args.content, args.case_id);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  async searchCases(query, limit = 5) {
    try {
      const result = await this.runSCP(['search', query, '-l', limit.toString(), '--context']);
      const context = JSON.parse(result);
      
      return {
        content: [
          {
            type: 'text',
            text: `Found ${context.total_cases} similar cases for: "${query}"\\n\\n` +
                  context.cases.map(c => 
                    `**${c.case_id}**: ${c.summary}\\n` +
                    `Tags: ${c.tags.join(', ')}\\n` +
                    `Key symptoms: ${c.symptoms.slice(0, 2).join('; ')}\\n`
                  ).join('\\n')
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error searching cases: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async getContext(caseIds) {
    try {
      const contexts = await Promise.all(
        caseIds.map(id => this.runSCP(['get', id, '--context']))
      );
      
      const cases = contexts.map(c => JSON.parse(c));
      
      return {
        content: [
          {
            type: 'text',
            text: `**Support Case Context for Analysis:**\\n\\n` +
                  cases.map(c => 
                    `## Case ${c.case_id}\\n` +
                    `**Summary**: ${c.summary}\\n` +
                    `**Environment**: ${Object.entries(c.environment).map(([k,v]) => `${k}: ${v}`).join(', ')}\\n` +
                    `**Key Errors**: ${c.key_errors.join('; ')}\\n` +
                    `**Tags**: ${c.tags.join(', ')}\\n` +
                    `**Content Preview**: ${c.content_preview}\\n`
                  ).join('\\n---\\n\\n')
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error retrieving context: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async addCase(content, caseId) {
    try {
      const args = ['add'];
      if (caseId) {
        args.push('--case-id', caseId);
      }
      
      const result = await this.runSCP(args, content);
      
      return {
        content: [
          {
            type: 'text',
            text: `Successfully added case. Output: ${result}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error adding case: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async runSCP(args, input = null) {
    return new Promise((resolve, reject) => {
      const proc = spawn('node', [this.scpPath, ...args], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        if (code === 0) {
          resolve(stdout.trim());
        } else {
          reject(new Error(stderr || `Process exited with code ${code}`));
        }
      });

      if (input) {
        proc.stdin.write(input);
        proc.stdin.end();
      }
    });
  }

  listResources() {
    return {
      resources: [
        {
          uri: 'scp://stats',
          name: 'SCP Database Statistics',
          description: 'Current database statistics and usage info',
          mimeType: 'application/json'
        }
      ]
    };
  }

  async readResource(params) {
    if (params.uri === 'scp://stats') {
      try {
        const result = await this.runSCP(['stats']);
        return {
          contents: [
            {
              uri: params.uri,
              mimeType: 'text/plain',
              text: result
            }
          ]
        };
      } catch (error) {
        throw new Error(`Failed to read stats: ${error.message}`);
      }
    }
    
    throw new Error(`Unknown resource: ${params.uri}`);
  }
}

// MCP Transport Layer
class MCPTransport {
  constructor(server) {
    this.server = server;
    this.setupTransport();
  }

  setupTransport() {
    // Handle MCP protocol over stdin/stdout
    process.stdin.setEncoding('utf8');
    
    let buffer = '';
    process.stdin.on('data', (chunk) => {
      buffer += chunk;
      
      // Process complete JSON-RPC messages
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);
        
        if (line.trim()) {
          this.handleMessage(line);
        }
      }
    });
  }

  async handleMessage(line) {
    try {
      const message = JSON.parse(line);
      
      if (message.method) {
        // Request
        const result = await this.server.handleRequest(message.method, message.params);
        this.sendResponse(message.id, result);
      }
    } catch (error) {
      console.error('Error handling message:', error);
      if (message?.id) {
        this.sendError(message.id, error.message);
      }
    }
  }

  sendResponse(id, result) {
    const response = {
      jsonrpc: '2.0',
      id,
      result
    };
    console.log(JSON.stringify(response));
  }

  sendError(id, error) {
    const response = {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32603,
        message: error
      }
    };
    console.log(JSON.stringify(response));
  }
}

// Start MCP Server
if (require.main === module) {
  const server = new SCPMCPServer();
  new MCPTransport(server);
  
  // Send capabilities on startup
  const capabilities = {
    jsonrpc: '2.0',
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
        resources: {}
      },
      serverInfo: {
        name: 'scp-mcp-server',
        version: '1.0.0'
      }
    }
  };
  
  console.log(JSON.stringify(capabilities));
}
