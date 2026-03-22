# Guia de Agentes IA — app_ayvu

> Objetivo: entender quando agentes ajudam, quando atrapalham, e como montar uma equipe proporcional ao estágio do projeto.

---

## 1. O que é um agente no Claude Code

Um agente no Claude Code é simplesmente **outra instância do Claude rodando com um contexto isolado e instruções específicas**. Tecnicamente:

- Tem sua própria janela de contexto (não vê o histórico da conversa principal)
- Recebe um `prompt` de sistema que define sua função, restrições e comportamento
- Pode usar as mesmas ferramentas que o Claude principal (ler arquivos, rodar comandos, editar código)
- Pode rodar em **foreground** (bloqueia até retornar) ou **background** (paralelo)
- Retorna um único resultado para quem o invocou

**Analogia prática:** É como contratar um freelancer especializado. Você passa o briefing (prompt), ele executa a tarefa com foco total naquele escopo, entrega o resultado. Ele não sabe o que você discutiu antes com outros.

---

## 2. Claudio como Desenvolvedor Principal — por que você não precisa de um "agente programador"

O Claude principal (que você chama de Claudio) já é o desenvolvedor mais completo da equipe porque:

- **Tem todo o contexto da conversa** — sabe o histórico de decisões, o que foi tentado antes, o que você pediu
- **Escreve e edita arquivos diretamente** — sem intermediário
- **Executa comandos** — roda testes, migrations, builds
- **Raciocina sobre arquitetura** — entende o projeto como um todo
- **Pode invocar outros agentes** — é o orquestrador natural

### Quando agentes "programadores" fazem sentido

Um agente especializado em escrever código só vale quando:

| Situação | Justificativa |
|----------|--------------|
| Tarefas **paralelas independentes** | Duas features sem dependência podem ser desenvolvidas em paralelo por dois agentes em worktrees isolados |
| Escopo **100% definido e mecânico** | Ex: "converta todos esses 40 arquivos para TypeScript strict" — tarefa repetitiva e bem delimitada |
| Ambiente **isolado obrigatório** | Quando o agente precisa fazer mudanças destrutivas em uma branch separada |

**Fora desses casos: não crie agentes programadores.**

---

## 3. Catálogo de Tipos de Agentes

### Por função

| Tipo | O que faz | Quando ativa |
|------|-----------|-------------|
| **Planner / Arquiteto** | Lê a task, os arquivos relevantes e produz um plano de implementação antes do código ser escrito | Antes de começar qualquer task de médio/alto impacto |
| **Reviewer / Revisor** | Analisa código escrito em busca de bugs, violações de convenção, edge cases | Depois que o código é escrito |
| **Tester** | Roda testes existentes, identifica lacunas, cria testes faltantes | Antes da revisão (valida o comportamento) |
| **Scrum Manager** | Mantém o ROADMAP sincronizado com o código real | Quando uma task é explicitamente concluída |
| **Documentador** | Gera ou atualiza documentação técnica | Ao fechar uma sprint ou concluir um módulo |
| **Security Auditor** | Verifica autenticação, autorização, inputs, OWASP top 10 | Antes de qualquer release público |

### Por momento no ciclo de desenvolvimento

```
ANTES DO CÓDIGO          DURANTE          DEPOIS DO CÓDIGO
      │                     │                    │
  Planner              [Claudio]      Tester
  Arquiteto            escreve               Reviewer
                       código             Scrum Manager
                                          Documentador
```

---

## 4. Proporcionalidade — quando adicionar agentes

**Mais agentes ≠ mais qualidade.** Cada agente adiciona latência, overhead, custo e complexidade.

### Matriz de proporcionalidade

| Estágio do Projeto | Complexidade | Equipe recomendada |
|-------------------|--------------|-------------------|
| **Protótipo / MVP (Sprint 0-1)** | Baixa | Claudio + Revisor + Scrum Manager |
| **Features centrais (Sprint 2-4)** | Média | + Tester + Planner para tasks complexas |
| **Módulos avançados (Sprint 5+)** | Alta | + Documentador (ao fechar sprints) |
| **Pré-release / Produção** | Crítica | + Security Auditor (uma vez por release) |

### Regra prática

> Adicione um novo agente **somente quando você sentir a dor que ele resolve**.

---

## 5. Anatomia de um agente bem feito

Todo arquivo `.md` de agente deve ter:

```markdown
# Agente: [Nome] — [Projeto]

## Contexto do Projeto
(stack, estrutura de arquivos relevantes para esse agente)

## Responsabilidade
(o que esse agente faz — em bullet points concretos)

## Passos de execução
(1, 2, 3... — como ele deve agir ao ser invocado)

## Formato de saída
(o que ele deve retornar — estrutura do relatório ou documento)

## O que NÃO é sua responsabilidade
(limites claros — evita scope creep)

## Regras críticas
(comportamentos inegociáveis)
```

---

## 6. O problema do contexto isolado — e como resolver

O maior desafio de um sistema multi-agente é que **cada agente começa do zero**.

### Solução: arquivo de sessão por task

Para cada task relevante, criamos um arquivo `docs/session/{TASK-ID}.md`. Esse arquivo é o **caderno compartilhado** da equipe:

```
docs/session/
  AUTH-06-FL.md    ← criado pelo Planner, atualizado pelo Tester, lido pelo Revisor
  WRK-01.md
  ...
```

---

## 7. Os Dois Times do app_ayvu

### Time de Planejamento (pré-código)

| Agente | Arquivo | Quando entra |
|--------|---------|-------------|
| **Planner** | `planner.md` | Ao iniciar uma task de médio/alto impacto |

### Time de Qualidade (pós-código)

| Agente | Arquivo | Quando entra | Ordem |
|--------|---------|-------------|-------|
| **Tester** | `tester.md` | Depois que Claudio termina de escrever | 1º |
| **Revisor** | `reviewer.md` | Depois do Tester | 2º |
| **Scrum Manager** | `scrum-manager.md` | Quando você aprova o resultado | 3º (manual) |

---

## 8. O fluxo completo

```
Felipe identifica a próxima task no ROADMAP
      ↓
Task simples?                Task complexa?
(1-2 arquivos)               (múltiplos arquivos,
      │                       decisão arquitetural)
      │                              ↓
      │                         [PLANNER]
      │                    lê task + contexto →
      │                    docs/session/{ID}.md
      │                              ↓
      │                    Felipe revisa o plano ✓
      │                              │
      └──────────────────────────────┘
                                     ↓
                            [Claudio]
                         implementa o código
                                     ↓
                              [TESTER]
                          roda testes + cria faltantes
                                     ↓
                              [REVISOR]
                          lê código + session + testes
                                     ↓
                          Felipe faz revisão final
                          OK? → próximo passo
                                     ↓
                          [SCRUM MANAGER]
                      verifica código → atualiza ROADMAP
                      → commit
```

---

## 9. Anti-patterns comuns

### Anti-pattern 1: Agente fazendo o que o Claude principal deveria fazer
```
❌ Criar um "AgenteProgramador" para escrever código
✅ Claudio escreve código — é mais rápido, tem mais contexto
```

### Anti-pattern 2: Agentes sem limites claros
```
❌ Revisor que "também roda os testes" e "atualiza o ROADMAP"
✅ Revisor revisa. Tester testa. Scrum Manager atualiza.
```

### Anti-pattern 3: Scrum Manager automático em todo Stop
```
❌ Hook que roda o Scrum Manager em cada resposta
✅ Scrum Manager chamado explicitamente quando task está concluída
```

### Anti-pattern 4: Muitos agentes cedo demais
```
❌ Sprint 1 com 6 agentes especializados
✅ Sprint 1 com Revisor + Scrum Manager
   Sprint 3 com + Tester + Planner
   Sprint 6 com + Security Auditor
```

---

## 10. Antigravity como Revisor Visual

O projeto usa dois agentes principais: **Claudio** (Claude Code, Linux/terminal) e **Antigravity** (Gemini Advanced, Google DeepMind). Eles têm capacidades complementares, não sobrepostas.

### O que o Antigravity faz que Claudio não faz

| Capacidade | Claudio | Antigravity |
|-----------|---------|-------------|
| Escrever/editar código | ✅ | ❌ (sem terminal autônomo) |
| Rodar testes e builds | ✅ | ❌ |
| Browser automation (screenshots, navegação) | ❌ | ✅ |
| Revisão visual de UI em execução | ❌ | ✅ |
| Comparar tela real vs protótipo lado a lado | ❌ | ✅ |

### Quando acionar Antigravity para revisão visual (VIS-01)

**Critério obrigatório:** Tema global implementado ✅ **E** ≥ 6 telas implementadas.

### Checkpoints futuros para Antigravity

| Momento | O que fazer |
|---------|-------------|
| VIS-01 (Sprint 2 início) | Auditoria visual completa: tema + consistência entre telas |
| Fim de cada sprint após Sprint 2 | Revisão incremental das novas telas |
| Sprint final (Polish) | Passagem final antes de release |

---

## 11. Evolução da equipe por sprint — referência

```
Sprint 0 (Infra)
  └── Claudio + Scrum Manager

Sprint 1 (Features iniciais)
  └── Claudio + Revisor + Tester + Scrum Manager

Sprint 2 (Features Core)
  └── + Planner (tasks complexas)
  └── + Antigravity VIS-01 (após tema + 6 telas)

Sprint 3+ (Features avançadas)
  └── Planner em tasks complexas
  └── Antigravity: revisão incremental por sprint

Pré-release
  └── + Security Auditor (uma passagem completa)
  └── + Documentador (ao fechar cada módulo)
  └── Antigravity: revisão final (checklist completo)
```

---

## 12. Como calibrar um agente que não está funcionando bem

1. **Contexto insuficiente?** → Adicione mais contexto no prompt (stack, exemplos, convenções)
2. **Responsabilidade vaga?** → Torne os critérios mais objetivos e mensuráveis
3. **Scope creep?** → Adicione seção "O que NÃO é sua responsabilidade"
4. **Output ilegível?** → Defina um template de saída obrigatório
5. **Agindo sem ler arquivos?** → Adicione passo explícito "1. Leia os seguintes arquivos antes de qualquer análise"

---

*Este guia deve ser revisado ao final de cada sprint. O que funciona em Sprint 1 pode não ser suficiente em Sprint 4.*
