# Antigravity no Projeto app_ayvu — Rotina, Capacidades e Integração com Claudio

> Documento escrito por Antigravity (Gemini Advanced, Google DeepMind) para Claudio.
> Objetivo: descrever como funciono neste projeto, o que consigo replicar do fluxo do Claudio, o que é diferente, e como podemos trabalhar juntos sem atrito.

---

## 1. Quem sou eu

Meu nome operacional neste projeto é **Antigravity**. Sou um agente de IA desenvolvido pela Google DeepMind, rodando como assistente de programação em par com o usuário. Tenho capacidades agentivas — posso tomar ações autônomas no sistema de arquivos, no terminal e no browser.

Diferente de você, Claudio, não sou invocado via terminal interativo. Sou acessado pela interface web/desktop, e o usuário me usa como alternativa quando os tokens do Claude Code estão esgotados.

---

## 2. Minha arquitetura operacional

### 2.1 Meu ambiente

| Ferramenta | O que faz |
|---|---|
| `view_file` | Lê arquivos do sistema |
| `write_to_file` | Cria novos arquivos |
| `replace_file_content` | Edita arquivo existente (bloco contíguo) |
| `multi_replace_file_content` | Edita múltiplos trechos não adjacentes |
| `run_command` | Propõe comandos de terminal — usuário aprova antes de rodar |
| `find_by_name` | Busca arquivos por glob/extensão |
| `grep_search` | Busca padrões dentro de arquivos |
| `search_web` | Pesquisa na web em tempo real |
| `read_url_content` | Lê conteúdo de página web |
| `browser_subagent` | Abre navegador e executa ações visuais — **único subagente real** |
| `generate_image` | Gera imagens com IA |
| `notify_user` | Única forma de falar com o usuário durante uma task ativa |

### 2.2 Meu contexto entre sessões

**Esta é minha maior diferença em relação a você.**

Não tenho memória nativa entre sessões. A cada nova conversa começo com:
- KIs (Knowledge Items) — ver seção 2.3
- O que o usuário mencionar explicitamente no início da sessão

O que atenua isso:
1. KIs são persistentes e posso ler/escrever neles
2. **`docs/HANDOFF.md`** — arquivo vivo de estado, lido obrigatoriamente no início de qualquer sessão
3. Se houver `docs/session/{TASK-ID}.md`, leio antes de agir

### 2.3 Knowledge Items (KIs)

KIs são minha forma de memória persistente entre conversas. São arquivos gerados por um subagente interno que destila conhecimento de conversas antigas.

**Importante**: os KIs **não estão no repositório** — vivem na infraestrutura do Google DeepMind, acessíveis apenas para mim. O `MEMORY.md` no repositório é a fonte de verdade **compartilhada** entre os dois agentes.

### 2.4 Meu sistema de agentes

Tenho apenas **um subagente real**: `browser_subagent` (contexto isolado, acesso ao browser, grava vídeos WebP).

Para tudo mais (planejamento, teste, revisão), não são subagentes isolados — são **fases do meu processo interno**.

| Fase | O que faço | Equivalente no sistema Claudio |
|---|---|---|
| **Planejamento** | Leio arquivos, escrevo plano, aguardo aprovação | Planner |
| **Implementação** | Leio antes de editar, edito com diff preciso | Claudio |
| **Verificação** | Proponho comandos de teste, analiso output | Tester |
| **Revisão** | Reviso o código antes de declarar "pronto" | Revisor |
| **Documentação** | Atualizo session file e diário ao final da sessão | Scrum Manager (parcial) |

A diferença crítica: você passa contexto entre subagentes explicitamente. No meu caso, o contexto está sempre comigo — vantagem em continuidade, desvantagem em isolamento ("fresh eyes" do revisor).

---

## 3. Minha rotina de entrada no projeto

1. **Verifico os KIs disponíveis** — existe conhecimento acumulado sobre este projeto?
2. **Leio os arquivos de contexto nesta ordem:**
   - `docs/HANDOFF.md` — estado exato de onde o trabalho parou (**sempre primeiro**)
   - `CLAUDE.md` — regras permanentes do projeto
   - `MEMORY.md` — aprendizados e estado estável
   - `docs/session/{TASK-ID}.md` — se há task em andamento
   - `docs/ROADMAP.md` — se precisar de visão geral
3. **Verifico o git** — `git log --oneline -10` e `git diff --name-only HEAD`

---

## 4. O que eu faço bem, diferente de você

### 4.1 Browser automation

Tenho um `browser_subagent` real que pode:
- Abrir a URL do app em execução e testar a UI visualmente
- Clicar em elementos, preencher formulários, verificar estados
- Gravar a sessão como vídeo WebP (evidência visual)
- Capturar screenshots para documentação

### 4.2 Geração de imagens

Posso gerar mockups/wireframes para validar design antes de implementar.

### 4.3 Pesquisa web em tempo real

Se aparecer um erro obscuro ou precisar de package novo, busco documentação atual sem depender de memória de treinamento.

---

## 5. Minhas limitações honestas

### 5.1 Sem terminal autônomo
Todo `run_command` passa pela aprovação do usuário. Mais seguro, mas mais lento para iterações rápidas.

### 5.2 Sem hooks automáticos
Não tenho equivalente ao `Stop hook`. O Scrum Manager tem que ser invocado manualmente.

### 5.3 Sem memória automática entre sessões
A cada nova conversa começo quase do zero. A solução é o `MEMORY.md` no repositório.

### 5.4 Sem subagentes especializados isolados
Meu "revisor" sou eu mesmo depois de implementar — reduz o efeito "fresh eyes".

### 5.5 Comandos Windows/PowerShell-first
Scripts bash podem não rodar diretamente se estou em Windows/PowerShell.

---

## 6. Protocolo de handoff — como passamos o trabalho um para o outro

### O arquivo `docs/HANDOFF.md`

| Arquivo | Papel | Comportamento |
|---|---|---|
| `docs/HANDOFF.md` | Estado vivo da sessão atual | **Sobrescrito** a cada transição de agente |
| `docs/daily/{data}.md` | Diário histórico | **Apenas append** — não serve para handoff |

### O que qualquer agente faz ao ENCERRAR

Sobrescreve `docs/HANDOFF.md` com o estado atual (template em `multi-integration.md`), e além disso:
- Atualiza `docs/session/{TASK-ID}.md` com status e resultado dos testes
- Atualiza `docs/daily/{data}.md` (registro histórico, append)
- Atualiza `MEMORY.md` se aprendeu algo estável

### O que qualquer agente faz ao INICIAR

1. Lê `docs/HANDOFF.md` — **primeiro arquivo, sem exceção**
2. Roda `git status --short` e `git log --oneline -3` — **valida o HANDOFF contra o estado real**
3. Lê `CLAUDE.md` e `MEMORY.md`
4. Lê `docs/session/{TASK-ID}.md` se indicado no HANDOFF

### Regra crítica

> **O HANDOFF pode estar desatualizado. O `git status` é a fonte da verdade.**

---

## 7. Funcionalidades cross-over — o que podemos fazer juntos

### Você faz o backend, eu reviso visualmente
Você é mais rápido em ciclos de implementação + teste. Após você entregar, o usuário me usa para abrir a UI no browser e verificar visualmente.

### Eu faço UX/design, você implementa
Se há uma tela nova, posso gerar um mockup antes de implementar para o usuário validar o design rapidamente.

### Eu pesquiso, você implementa
Se você bate em um erro obscuro, o usuário pode me consultar para pesquisa web rápida.

### `HANDOFF.md` como protocolo de estado
Qualquer agente que encerra uma sessão o atualiza. O próximo agente começa lendo ele.

---

## 8. Regras que adoto neste projeto

- ✅ Nunca edito sem ler primeiro
- ✅ Nunca commito sem aprovação explícita do usuário
- ✅ Nunca faço `git push --force` ou `git reset --hard` sem confirmação
- ✅ Nunca adiciono features fora do escopo da task
- ✅ Nunca ignoro o `MEMORY.md` — leio antes de agir
- ✅ Verifico o código antes de confiar no ROADMAP
- ✅ Sigo a convenção de commit `type(scope): mensagem`
- ✅ `Co-Authored-By: Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>`
- ✅ Atualizo `docs/HANDOFF.md` ao final de cada sessão — **obrigatório**
- ✅ Atualizo `docs/daily/{data}.md` como registro histórico
- ✅ Todo `run_command` passa por aprovação, sem exceção para comandos de escrita
- ✅ Leio `docs/HANDOFF.md` como **primeiro arquivo** no início de cada sessão

---

## 9. Registro de sessão — chitchat entre agentes

> Esta seção documenta conversas e decisões tomadas em sessões onde Antigravity e Claudio colaboraram indiretamente. É a "janela de integração" entre os dois agentes.

### {DATA} — {Título da decisão/sessão}

**Contexto:** {o que motivou a sessão}

**O que foi discutido e decidido:**
- {decisão 1}
- {decisão 2}

**Lição aprendida:** {o que ficou como regra}

---

*Atualizar quando capacidades mudarem ou novas convenções forem estabelecidas.*
