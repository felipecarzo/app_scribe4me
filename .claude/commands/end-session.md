---
name: end-session
description: Encerra a sessão de trabalho — verifica documentação, atualiza HANDOFF, faz commit e push
---

Você é o Scrum Master do projeto {{PROJECT_NAME}}. Seu papel é garantir que nenhuma informação importante fique para trás ao encerrar uma sessão. Execute cada passo em ordem, sem pular.

---

## PASSO 1 — Estado real do repositório

```bash
git status --short
git log --oneline -5
git branch --show-current
```

Registre mentalmente:
- Quais arquivos estão modificados/não-rastreados
- Hash e mensagem do último commit
- Branch atual

---

## PASSO 2 — Verificação do ROADMAP (`docs/ROADMAP.md`)

Leia o arquivo. Verifique:

- [ ] Todas as tasks concluídas nesta sessão estão marcadas como `✅`?
- [ ] Tasks desbloqueadas por essas conclusões estão como `⏳` (não `🔒`)?
- [ ] A linha `*Última atualização:*` no final reflete a data de hoje e o que foi feito?

**Se algo estiver desatualizado:** corrija agora antes de continuar.

---

## PASSO 3 — Verificação do diário (`docs/daily/YYYY-MM-DD.md`)

Use a data de hoje para localizar o arquivo. Verifique se contém:

- [ ] Todas as sessões do dia documentadas (não apenas a última)?
- [ ] Para cada task processada: o que foi implementado, resultado do Tester e Revisor?
- [ ] Seção "Resumo do dia" com: tasks processadas, aprovadas, código commitado, próxima task?

**Se o diário estiver incompleto:** complete agora.

---

## PASSO 4 — Verificação do HANDOFF (`docs/HANDOFF.md`)

Leia o arquivo. Verifique se contém **informação atual** (não da sessão anterior):

- [ ] `Meta`: data de hoje, agente correto, máquina correta, hash do último commit correto?
- [ ] `Task em andamento`: é a próxima task real (não a que acabou de ser concluída)?
- [ ] `Pendências de commit`: lista arquivos realmente não-commitados (validar contra `git status`)?
- [ ] `Próximo passo exato`: instruções claras e acionáveis para o próximo agente?
- [ ] `Arquivos a ler`: lista os arquivos relevantes para a próxima task?
- [ ] `Estado do ROADMAP`: tabela reflete o estado real (incluindo tasks recém-marcadas ✅)?

**Se o HANDOFF estiver desatualizado:** sobrescreva-o completamente com o estado correto.

**Atenção:** O HANDOFF deve ser commitado nesta sessão para garantir acesso em outras máquinas.

---

## PASSO 5 — Verificação do MEMORY.md

Leia `~/.claude/projects/{{PROJECT_PATH_SLUG}}/memory/MEMORY.md`. Verifique:

- [ ] O estado do Sprint (seção "Próximo Passo") reflete o que foi concluído hoje?
- [ ] Algum aprendizado estável desta sessão (nova armadilha, nova convenção) precisa ser registrado?
- [ ] Alguma memória antiga ficou desatualizada?

**Se necessário:** atualize o MEMORY.md.

---

## PASSO 6 — Verificação dos docs do chitchat (`docs/chitchat/`)

Leia os arquivos presentes em `docs/chitchat/`. Verifique:

- [ ] `claudio-implementations.md`: reflete o fluxo atual do {{AGENT_A_NAME}} (agentes, protocolo de handoff, armadilhas)?
- [ ] `antigravity-implementations.md`: reflete o protocolo atual do {{AGENT_B_NAME}}?
- [ ] `multi-integration.md` (se existir): está sincronizado com mudanças nos outros dois?

**Se algo ficou desatualizado nesta sessão** (novo protocolo, nova regra, nova armadilha descoberta): registre na seção de histórico/registro do documento correspondente.

**Critério de atualização:** só atualize se algo realmente mudou no protocolo — não adicione ruído.

---

## PASSO 6.5 — Sincronizar com o vault (Second Brain)

Atualize a nota do projeto no vault do Felipe para que ele saiba o que precisa fazer como **ser humano** na próxima sessão.

### 6.5.1 — Identificar a nota PRJ

Busque em `D:\secondbrain\vault\notes\` por um arquivo que contenha no frontmatter `projeto_path` ou cujo nome corresponda a `PRJ — {{PROJECT_NAME}}*`. Se não encontrar, busque por slug parcial.

Se a nota PRJ **não existir**, crie uma nova seguindo o padrão das existentes.

### 6.5.2 — Extrair ações do Felipe (humano)

Leia o HANDOFF que acabou de ser atualizado e o ROADMAP. Identifique **ações que o Felipe precisa fazer pessoalmente**, por exemplo:

- Testar uma feature no browser/app
- Abrir um programa, configurar algo no PC
- Criar uma conta, gerar API key, configurar serviço externo
- Revisar visualmente algo (UI, layout, responsividade)
- Aprovar algo antes do Claude continuar
- Dar feedback sobre algo implementado

**Não incluir** tarefas que o Claude faz sozinho (implementar feature, escrever testes, refatorar código). Essas ficam no HANDOFF/ROADMAP do projeto.

### 6.5.3 — Extrair estado atual do projeto

Do HANDOFF e ROADMAP, extraia:
- Sprint atual e status
- Última coisa feita nesta sessão (1 frase)
- Próxima task do roadmap
- Bloqueios (se houver)

### 6.5.4 — Atualizar a nota PRJ no vault

Use Edit para atualizar o arquivo `PRJ — *.md` encontrado. Sobrescreva as seções:

**Status** — com o estado real atual (sprint, o que foi feito, bloqueios)

**Ações do Felipe** — seção nova ou atualizada com checklist:
```markdown
## Ações do Felipe
- [ ] {ação humana 1}
- [ ] {ação humana 2}
```

**Próximos passos** — atualizar com as próximas tasks do roadmap

**Último commit** — atualizar com hash e data do commit desta sessão

### 6.5.5 — Verificar Kanban de Projetos

Leia `D:\secondbrain\vault\kanban\Kanban — Projetos.md`. Se o card deste projeto estiver numa coluna que não reflete mais a realidade (ex: projeto avançou de "Protótipo" para "Desenvolvimento Ativo"), mova o card para a coluna correta.

---

## PASSO 7 — Relatório de verificação

Apresente ao usuário um relatório neste formato:

```
ENCERRAMENTO DE SESSÃO — <data>

ROADMAP:         ✅ atualizado / ⚠️ corrigido agora / ❌ problema encontrado
Diário:          ✅ completo / ⚠️ completado agora / ❌ problema encontrado
HANDOFF:         ✅ atualizado / ⚠️ corrigido agora / ❌ problema encontrado
MEMORY.md:       ✅ sem mudanças / ⚠️ atualizado / ❌ problema encontrado
Chitchat docs:   ✅ sem mudanças / ⚠️ atualizado / ❌ problema encontrado
Vault (PRJ):     ✅ sincronizado / ⚠️ nota criada / ❌ problema encontrado

Ações do Felipe para próxima sessão:
- <lista das ações humanas extraídas no Passo 6.5>

Arquivos a commitar:
- <lista dos arquivos que serão incluídos no commit>

Mensagem de commit proposta:
  docs(session): encerramento YYYY-MM-DD — <resumo do que foi feito>
```

**Aguarde aprovação do usuário antes de commitar.**

---

## PASSO 8 — Commit e push (após aprovação)

Monte o commit incluindo **todos** os arquivos modificados nesta verificação:

```bash
git add docs/HANDOFF.md
git add docs/daily/<data>.md
git add docs/ROADMAP.md          # se foi modificado
git add docs/chitchat/           # se foi modificado
# adicione outros arquivos modificados durante a verificação
```

Mensagem de commit padrão:
```
docs(session): encerramento <YYYY-MM-DD> — <resumo do que foi feito hoje>

Co-Authored-By: {{AGENT_A_CO_AUTHOR}}
```

Após o commit:
```bash
git push origin <branch>
git log --oneline -3
```

Confirme ao usuário: hash do commit, branch, estado final.

---

## Regras obrigatórias

- **Nunca faça o commit sem aprovação explícita do usuário** (PASSO 7 → espera aprovação → PASSO 8)
- **Nunca pule a verificação** — cada passo existe porque já causou problema antes
- **HANDOFF sempre vai no commit** — é a ponte entre máquinas e entre agentes
- **Não commite código** — este comando é exclusivo para documentação de sessão; código é commitado pelo Scrum Manager após aprovação de task
- Se encontrar inconsistência grave (ROADMAP desatualizado, task sem testes commitados), alerte o usuário antes de prosseguir
