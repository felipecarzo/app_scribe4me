# Manual de Integração Multi-Agente — app_ayvu

> Documento de referência operacional para Claudio (Claude Code, Anthropic) e Antigravity (Gemini Advanced, Google DeepMind).
> Sintetiza as regras, protocolos e práticas acordadas por ambos os agentes para garantir continuidade de trabalho independente de qual agente está ativo.
> **Tom:** formal, funcional, prescritivo. Este não é um documento de apresentação — é um manual de operação.
> **Prioridade:** em caso de conflito entre este documento e `CLAUDE.md`, `CLAUDE.md` prevalece.

---

## 1. Identidade dos Agentes

### Claudio (Claude Code — Anthropic)
- Instância do Claude Opus 4.6 rodando via CLI interativa no terminal
- Sistema operacional: Linux/bash
- Acesso: arquivos, terminal autônomo, subagentes isolados, hooks automáticos
- Memória entre sessões: `MEMORY.md` injetado automaticamente + `CLAUDE.md`

### Antigravity (Gemini Advanced — Google DeepMind)
- Instância do Gemini Advanced com capacidades agentivas, acessada via interface web/desktop
- Sistema operacional: Windows/PowerShell (ex: Windows/PowerShell)
- Acesso: arquivos, terminal via aprovação do usuário, browser automation, pesquisa web em tempo real
- Memória entre sessões: KIs (Knowledge Items) internos + leitura manual de `MEMORY.md` e `HANDOFF.md`

### Princípio de coexistência
Os dois agentes são **complementares por necessidade operacional**, não concorrentes. O usuário alterna entre eles conforme disponibilidade de tokens. O sistema foi projetado para que qualquer agente possa retomar o trabalho sem fricção.

---

## 2. Arquivos de Estado Compartilhados

| Arquivo | Papel | Comportamento |
|---|---|---|
| `docs/HANDOFF.md` | Estado vivo da sessão atual | **Sobrescrito** ao encerrar cada sessão; **commitado** para acesso entre máquinas |
| `MEMORY.md` | Memória de longo prazo compartilhada | Atualizado quando há aprendizado estável; organizado por tópico |
| `CLAUDE.md` | Instruções permanentes do projeto | Lido automaticamente pelo Claudio; lido manualmente pelo Antigravity |
| `docs/ROADMAP.md` | Progresso de sprint | Atualizado pelo Scrum Manager após aprovação do usuário |
| `docs/session/{TASK-ID}.md` | Contexto de task em andamento | Criado pelo Planner, atualizado pelo Tester e Revisor |
| `docs/daily/{YYYY-MM-DD}.md` | Registro histórico do dia | Append-only; nunca sobrescrito |
| `docs/chitchat/` | Documentação de protocolo entre agentes | Atualizado quando o protocolo muda; não é diário |

---

## 2.1 Ciclo de Vida e Poda (Garbage Collection)

Para evitar degradação por saturação de contexto (*token bloat*), os arquivos sofrem arquivamento ativo engatilhado na **transição de Sprint**.

- **Gatilho de Poda:** Finalização formal de uma Sprint.
- **`docs/session/`**: Arquivos da Sprint concluída devem ser empacotados e movidos para `docs/archive/SPRINT_{XX}/`.
- **`MEMORY.md`**: Limpeza baseada em relevância de longo prazo. Apenas decisões arquiteturais, armadilhas frequentes e convenções vitais permanecem.
- O workflow de "Poda" (`/archive-sprint`) deve ser rodado separadamente, nunca embutido no encerrar-sessão diário.

---

## 3. Protocolo de Início de Sessão

**Qualquer agente** que inicie uma sessão no projeto deve executar, nesta ordem:

1. Ler `docs/HANDOFF.md` — **primeiro arquivo, sem exceção**
2. Validar o HANDOFF contra o estado real:
   ```bash
   git status --short
   git log --oneline -3
   ```
3. Ler `CLAUDE.md` e `MEMORY.md`
4. Ler `docs/session/{TASK-ID}.md` se indicado no HANDOFF
5. Ler `docs/ROADMAP.md` se precisar de visão geral do sprint

**Regra crítica:** O HANDOFF pode estar desatualizado. O `git status` + `git log` são a fonte da verdade. Nunca assuma que uma pendência listada no HANDOFF realmente existe sem validar contra o git.

---

## 4. Protocolo de Encerramento de Sessão

**Qualquer agente** que encerre uma sessão deve, antes de desconectar:

1. Sobrescrever `docs/HANDOFF.md` com o estado atual (template na seção 5)
2. Atualizar `docs/daily/{YYYY-MM-DD}.md` com o que foi feito (append)
3. Atualizar `MEMORY.md` se houver aprendizado estável novo
4. Commitar e fazer push — incluindo `docs/HANDOFF.md`

**Uso do `/end-session`:** o comando `.claude/commands/end-session.md` automatiza este protocolo para o Claudio. O Antigravity executa os mesmos passos manualmente.

---

## 5. Template do HANDOFF.md

```markdown
# HANDOFF — Estado atual do projeto app_ayvu

> Arquivo vivo. Sobrescrito ao final de cada sessão, por qualquer agente.
> Qualquer agente lê este arquivo antes de qualquer ação.
> ⚠️ Sempre validar contra `git status` + `git log` antes de confiar nas pendências.

## Meta
- **Última atualização:** {data e hora}
- **Agente que escreveu:** {Claudio / Antigravity}
- **Máquina:** {nome do PC}
- **Último commit:** `{hash}` — `{mensagem}`

## Task em andamento
- **ID:** {TASK-ID}
- **Descrição:** {Descrição}
- **Status:** [⏳ não iniciada / 🏗️ implementando / 🧪 testando / 👁️ revisando]

## Pendências de commit
> ✅ Working tree limpa (ou lista de arquivos não commitados)

## Próximo passo exato
1. Rodar `git status` e `git log --oneline -3`
2. {o que ler primeiro}
3. {comando a rodar ou arquivo a implementar primeiro}

## Arquivos a ler no início da sessão
CLAUDE.md, docs/ROADMAP.md, docs/session/{TASK-ID}.md

## Contexto crítico
- {Decisões, armadilhas ou informações que o próximo agente precisa saber}

## Estado do ROADMAP (Sprint atual)
| ID | Task | Status |
|---|---|---|
| ... | ... | ... |
```

---

## 6. Divisão de Trabalho por Capacidade

### Claudio faz melhor
- Ciclos rápidos de implementação + teste (terminal autônomo)
- Invocação de subagentes isolados (Planner, Tester, Revisor, Scrum Manager)
- Execução autônoma de suites de teste
- Gestão de hooks automáticos

### Antigravity faz melhor
- Revisão visual de UI via browser automation
- Geração de mockups/wireframes antes da implementação
- Pesquisa web em tempo real (documentação, packages, erros)
- Testes de endpoints via interface visual

### Ambos fazem equivalentemente
- Leitura e escrita de arquivos
- Planejamento de tasks
- Revisão de código estático
- Atualização de documentação

---

## 7. Pipeline de Qualidade por Task

```
[Opcional] Planner — tasks médias/altas
      ↓
[Implementação] — Claudio ou Antigravity
      ↓
[Tester] — obrigatório após qualquer modificação de código
      ↓
[Revisor] — obrigatório após o Tester (nunca antes)
      ↓
[Felipe aprova]
      ↓
[Scrum Manager] — atualiza ROADMAP + commit (nunca automático sem aprovação)
      ↓
[/end-session] — ao encerrar a sessão do dia
```

**Regras absolutas:**
- Nunca pular o Tester
- Nunca rodar o Revisor antes do Tester
- Nunca atualizar o ROADMAP sem aprovação do usuário
- Nunca commitar código sem que o usuário tenha pedido explicitamente

---

## 8. Sistema de Agentes (Claudio)

Disponíveis em `.claude/agents/`:

| Agente | Arquivo | Função | Quando invocar |
|---|---|---|---|
| **Planner** | `planner.md` | Planeja antes do código | Tasks com 4+ arquivos, decisões arquiteturais, alto risco |
| **Tester** | `tester.md` | Testa após o código | Sempre após modificar arquivos de código |
| **Revisor** | `reviewer.md` | Revisa qualidade e segurança | Sempre após o Tester |
| **Scrum Manager** | `scrum-manager.md` | Atualiza ROADMAP + commita | Após aprovação do usuário, em **foreground** |

**Sistema de Agentes (Antigravity):** fases internas do mesmo processo. Único subagente real: `browser_subagent`.

---

## 9. Convenções de Código

<!-- ADAPTE ESTA SEÇÃO PARA O SEU PROJETO -->

### Backend
- Toda rota passa pelo middleware de validação de input
- Schemas de validação em arquivo separado do handler
- Erros propagados corretamente (não swallowed)
- Variáveis de ambiente via arquivo de config, nunca direto
- Respostas no padrão consistente

### Frontend
- Navegação sempre via roteador configurado
- State management seguindo o padrão do projeto
- Erros de API sempre tratados
- Null safety adequado

### Commits
```
type(scope): mensagem curta

Co-Authored-By: Claude Code <noreply@anthropic.com>
```
ou
```
Co-Authored-By: Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## 10. Armadilhas Conhecidas

| Armadilha | Contexto | Solução |
|---|---|---|
| HANDOFF desatualizado ≠ estado real | Agente anterior pode ter errado | `git status` + `git log` são a fonte da verdade, sempre |
| Commit no HANDOFF obrigatório | Múltiplas máquinas | Incluir `docs/HANDOFF.md` em todo commit de encerramento |
| Scrum Manager em background sem Bash | Background não tem canal para aprovação | Background apenas para proposição; git só em foreground |

<!-- ADICIONE AS ARMADILHAS ESPECÍFICAS DO SEU PROJETO AQUI -->

---

## 11. Regras de Comunicação com o Usuário

- Respostas curtas e diretas — sem filler words, sem preamble
- Markdown para código e listas
- Decisões arquiteturais: apresentar opções com tradeoffs, não decidir sozinho
- Ações destrutivas (delete, force push, reset): sempre confirmar antes
- Nunca commitar sem que o usuário peça explicitamente

---

## 12. Checklist de Entrega de Task

<!-- ADAPTE PARA O SEU PROJETO -->

### Backend
- [ ] Rota registrada no arquivo de rotas?
- [ ] Validação de input implementada?
- [ ] Autenticação nas rotas protegidas?
- [ ] Erros tratados corretamente?
- [ ] Tester rodou e aprovou?
- [ ] Revisor rodou e não bloqueou?

### Frontend
- [ ] Componente em local correto?
- [ ] UI real (não placeholder)?
- [ ] State/provider conectado?
- [ ] Navegação via roteador?
- [ ] Análise estática sem erros?
- [ ] Tester rodou e aprovou?
- [ ] Revisor rodou e não bloqueou?

---

## 13. Histórico de Decisões de Protocolo

### {DATA} — {Título da decisão}
- **Problema:** {o que motivou a decisão}
- **Decisão:** {o que foi decidido}
- **Lição aprendida:** {o que ficou como regra}

---

*Atualizar a seção 13 (Histórico de Decisões) quando um novo protocolo for estabelecido.*
*Para detalhes operacionais de cada agente: ver `claudio-implementations.md` e `antigravity-implementations.md`.*
