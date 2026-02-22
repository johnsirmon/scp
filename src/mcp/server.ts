import { createInterface } from 'node:readline';
import { ScpEngine } from '../core/engine.js';

interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: number | string;
  method: string;
  params?: unknown;
}

interface JsonRpcResponse {
  jsonrpc: '2.0';
  id: number | string | null;
  result?: unknown;
  error?: { code: number; message: string };
}

function send(msg: JsonRpcResponse): void {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

function listTools() {
  return {
    tools: [
      {
        name: 'scp_search',
        description: 'Search for similar support cases',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query' },
            limit: { type: 'number', description: 'Max results', default: 5 },
          },
          required: ['query'],
        },
      },
      {
        name: 'scp_get_context',
        description: 'Get formatted AI-ready context for specific cases',
        inputSchema: {
          type: 'object',
          properties: {
            case_ids: { type: 'array', items: { type: 'string' }, description: 'Case IDs' },
          },
          required: ['case_ids'],
        },
      },
      {
        name: 'scp_add_case',
        description: 'Add a new support case',
        inputSchema: {
          type: 'object',
          properties: {
            content: { type: 'string', description: 'Case content' },
            case_id: { type: 'string', description: 'Optional case ID' },
          },
          required: ['content'],
        },
      },
    ],
  };
}

function listResources() {
  return {
    resources: [
      {
        uri: 'scp://stats',
        name: 'SCP Database Statistics',
        description: 'Current database statistics',
        mimeType: 'application/json',
      },
    ],
  };
}

export async function startMcpServer(engine: ScpEngine): Promise<void> {
  // Send initialize notification
  process.stdout.write(
    JSON.stringify({
      jsonrpc: '2.0',
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {}, resources: {} },
        serverInfo: { name: 'scp-mcp-server', version: '1.0.0' },
      },
    }) + '\n',
  );

  const rl = createInterface({ input: process.stdin, terminal: false });

  for await (const line of rl) {
    if (!line.trim()) continue;
    let req: JsonRpcRequest;
    try {
      req = JSON.parse(line) as JsonRpcRequest;
    } catch {
      continue;
    }

    try {
      let result: unknown;
      switch (req.method) {
        case 'tools/list':
          result = listTools();
          break;
        case 'resources/list':
          result = listResources();
          break;
        case 'tools/call': {
          const p = req.params as { name: string; arguments: Record<string, unknown> };
          result = await handleToolCall(engine, p.name, p.arguments);
          break;
        }
        case 'resources/read': {
          const p = req.params as { uri: string };
          if (p.uri === 'scp://stats') {
            const stats = await engine.stats();
            result = { contents: [{ uri: p.uri, mimeType: 'application/json', text: JSON.stringify(stats, null, 2) }] };
          } else {
            throw new Error(`Unknown resource: ${p.uri}`);
          }
          break;
        }
        default:
          throw new Error(`Unknown method: ${req.method}`);
      }
      send({ jsonrpc: '2.0', id: req.id, result });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      send({ jsonrpc: '2.0', id: req.id, error: { code: -32603, message: msg } });
    }
  }
}

async function handleToolCall(
  engine: ScpEngine,
  name: string,
  args: Record<string, unknown>,
): Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }> {
  try {
    switch (name) {
      case 'scp_search': {
        const query = String(args['query'] ?? '');
        const limit = Number(args['limit'] ?? 5);
        const results = await engine.search(query, { limit });
        const ctx = await engine.exportContext(results.map((r) => r.caseId));
        return {
          content: [
            {
              type: 'text',
              text: `Found ${ctx.totalCases} similar cases for: "${query}"\n\n` +
                ctx.cases
                  .map((c) => `**${c.caseId}**: ${c.summary}\nTags: ${c.tags.join(', ')}\nKey symptoms: ${c.symptoms.slice(0, 2).join('; ')}\n`)
                  .join('\n'),
            },
          ],
        };
      }
      case 'scp_get_context': {
        const caseIds = (args['case_ids'] as string[]) ?? [];
        const ctx = await engine.exportContext(caseIds);
        return {
          content: [
            {
              type: 'text',
              text:
                '**Support Case Context for Analysis:**\n\n' +
                ctx.cases
                  .map(
                    (c) =>
                      `## Case ${c.caseId}\n**Summary**: ${c.summary}\n**Environment**: ${Object.entries(c.environment)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ')}\n**Key Errors**: ${c.keyErrors.join('; ')}\n**Tags**: ${c.tags.join(', ')}\n**Content Preview**: ${c.contentPreview}\n`,
                  )
                  .join('\n---\n\n'),
            },
          ],
        };
      }
      case 'scp_add_case': {
        const content = String(args['content'] ?? '');
        const caseId = args['case_id'] ? String(args['case_id']) : undefined;
        const id = await engine.addCase(content, { caseId });
        return { content: [{ type: 'text', text: `Successfully added case: ${id}` }] };
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Error: ${msg}` }], isError: true };
  }
}
