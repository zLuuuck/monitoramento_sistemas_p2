## Contexto e missão

Faço parte de um grupo de 7 autores de um Projeto Interdisciplinar do curso de Análise e Desenvolvimento de Sistemas da Universidade Tuiuti do Paraná (2026). O documento atual em `abntex/PI-monitoramento-sistemas/trabalho.tex` cobre apenas pesquisa teórica e planejamento (Caps. 1–10) e fecha no Cap. 11 (Considerações Finais) tratando a implementação como trabalho futuro.

**Esse texto está desatualizado: o sistema foi efetivamente implementado.** Sua missão é estender o documento para refletir isso, mantendo rigor acadêmico, formatação ABNT/abnTeX2 e a voz do texto existente.

Comunique-se sempre em **português do Brasil**, em tom direto, sem rodeios, e aponte incoerências e riscos sempre que os encontrar.

---

## Fase 1 — Reconhecimento (não escreva nenhum capítulo ainda)

Leia, na ordem:

1. **Fonte LaTeX**: `abntex/PI-monitoramento-sistemas/trabalho.tex` e `abntex/PI-monitoramento-sistemas/referencias.bib`. Identifique estrutura, voz, padrão de citação, comandos abntex utilizados, e o pacote `abnt-UTP.sty` em `abntex/packages/`.
2. **Código do agente**: `Agent/src/agent/` — módulo a módulo. Atenção especial a `coleta/`, `discovery/`, `global_information/`, `utils/sender.py`, `utils/retry_queue.py`, `utils/parsers.py`.
3. **Backend**: `Web/BackEnd/app/` — `app.py`, todas as rotas em `routes/`, modelos em `models/`, e principalmente `utils/detection.py` e `utils/parsers.py`.
4. **Frontend**: `Web/FrontEnd/src/` — telas em `pages/`, componentes em `components/`, features em `features/` (alerts, logs_feat, metrics).
5. **Banco**: `Web/database/init.sql` — schema completo.
6. **Orquestração**: `Web/docker-compose.yml`, `Web/BackEnd/nginx/nginx.conf`, `Web/BackEnd/Dockerfile`, `Web/BackEnd/entrypoint.sh`.
7. **Documentação interna**: todo o conteúdo de `Context/Agent/*.md`, `Context/Backend/*.md`, `Context/Database/*.md`, `Context/Frontend/*.md`, `Context/Infra/*.md`. **Fonte autoritativa secundária** — quando houver divergência com o código, o código vence.
8. **Amostras de saída do agente**: `agent_physical_sample.json`, `agent_virtual_sample-Ubuntu.json`, `agent_virtual_sample-WSL2.json`. Mostram o que o agente realmente envia.

Ao final desta fase, **pare e me apresente**:

- Inventário do que está **efetivamente implementado**, com caminho do arquivo que sustenta cada item.
- O que está descrito em `Context/` mas **não encontra** no código.
- O que existe no código mas **não está documentado** em `Context/`.
- **Perguntas-chave que precisam de resposta explícita**:
  - Existe detecção de port scan implementada? Em qual arquivo, qual a regra exata? Se não existir, declare.
  - O envio de alertas via Teams está implementado? Onde? Webhook ou Graph API?
  - O envio de alertas por e-mail está implementado? Onde? SMTP direto ou serviço?
  - Existe alguma forma de IaC (docker-compose conta, Ansible/Terraform também) ou a infra foi configurada manualmente?
  - O DNS interno mencionado em `Context/Infra/03 - Implementação do DNS.md` está realmente em uso pelo sistema final?

Não passe para a Fase 2 sem minha confirmação.

---

## Fase 2 — Plano de redação (ainda sem escrever capítulo)

Com base na Fase 1, apresente:

- Para cada capítulo novo (11 a 15 + Apêndice A): seções, subseções, o que cada uma vai conter, e **a referência exata no repositório** (arquivo + função/seção) que sustenta o conteúdo.
- Lista de informações que **você não consegue obter sozinho** e que precisa de mim:
  - Datas reais do cronograma (~4 meses).
  - Política da Tuiuti / orientador sobre uso de IA (define se o Apêndice A entra no PDF final).
  - Resultados de testes de validação (Cap. 13) — se ainda não foram rodados, declare e gere apenas esqueleto com placeholders.
  - Decisões editoriais ambíguas.
- Lista de contradições entre o que está nos Caps. 1–10 e o que de fato foi implementado.

Espere minha aprovação antes da Fase 3.

---

## Fase 3 — Redação

Estrutura aprovada (numeração final do sumário):

- **Cap. 11 — Metodologia de Desenvolvimento**: tipo e natureza da pesquisa, modelo de desenvolvimento adotado, organização do grupo, cronograma com fases, stack/ambiente com versões justificadas.
- **Cap. 12 — Implementação do Sistema**: 12.1 visão geral; 12.2 infraestrutura; 12.3 agente coletor (discovery, métricas, conexões, logs — módulo a módulo); 12.4 backend (endpoints, normalização); 12.5 detecção de eventos e alertas (força bruta, port scan **se existir**, alertas Teams/email **se existirem**); 12.6 frontend e dashboard; 12.7 banco de dados (conceitual, lógico, queries, retenção).
- **Cap. 13 — Resultados e Validação**: se eu não tiver fornecido dados de teste reais nesta conversa, **gere apenas o esqueleto** com placeholders explicitamente marcados (`% TODO: inserir resultado de hydra contra SSH — N tentativas, tempo de detecção, latência do alerta`). **Não invente números, gráficos ou tabelas de resultado sob nenhuma circunstância.**
- **Cap. 14 — Limitações e Trabalhos Futuros**: absorva o antigo 10.7, atualize com limitações descobertas em código real e (quando houver) nos testes do Cap. 13.
- **Cap. 15 — Considerações Finais**: reescreva o antigo Cap. 11 refletindo que a implementação aconteceu; responda ao problema de pesquisa do Cap. 1 e ateste explicitamente cada objetivo específico (i, ii, iii, iv) como atendido, parcialmente atendido ou não atendido, indicando onde no texto está a evidência.
- **Apêndice A — Uso de IA no projeto**: gere comentado com `% CONDICIONAL` no LaTeX. Não inclua no PDF final sem minha confirmação sobre a política da Tuiuti.

Ajustes obrigatórios no texto existente:

- **Resumo**: remova a frase "não há implementação completa nem validação em ambiente real" e reescreva para descrever o trabalho como um todo (pesquisa + implementação).
- **Introdução (Cap. 1)**: se houver frase que prometa apenas especificação ou que limite o escopo, atualize.
- **Cap. 10.7 (último parágrafo)**: remova a promessa de "os próximos capítulos detalharão a implementação prática..." — ela contradizia o resumo e a antiga conclusão; agora esses capítulos existem.
- **Sumário, lista de figuras, lista de códigos**: regenere via recompilação.

---

## Regras absolutas

1. **Não invente.** Se o código não faz algo, o texto não pode afirmar que faz. Em caso de ambiguidade, marque com `% VERIFICAR` ou pergunte.
2. **Não invente referências bibliográficas.** Use apenas entradas existentes em `referencias.bib`. Se precisar adicionar uma nova, preencha todos os campos com dados de fonte real (documentação oficial, RFC, paper publicado) e me avise.
3. **Voz e tom**: releia os Caps. 1–10 e imite. Terceira pessoa, formal, parágrafos densos. Não use bullets onde o texto atual usa prosa corrida. Sem palavras de marketing ("robusto", "escalável", "moderno", "eficiente") sem dado que sustente.
4. **Citações no estilo já usado** pelo `abnt-UTP.sty`. Cada afirmação técnica relevante precisa de citação OU referência ao próprio sistema implementado (arquivo do código, seção anterior).
5. **Numeração e referências cruzadas**: renumere o sumário corretamente, atualize `\ref{}` e `\label{}`, e verifique que não há referências quebradas após a compilação.
6. **Trechos de código** no texto: snippets curtos e dirigidos, usando o mesmo ambiente do Cap. 7 (lstlisting). Código completo só em apêndice, se realmente necessário.
7. **Figuras**: para diagramas ainda inexistentes (fluxo de dados agente → Nginx → Flask → Postgres → dashboard; sequência do pipeline de alerta; modelo ER do banco), gere o código-fonte (TikZ inline, ou Mermaid/Graphviz em arquivo separado) e salve em `abntex/img/`. Cite no texto com `\ref{}` mesmo se o PNG ainda precisar ser regerado manualmente.
8. **Idioma e ortografia**: português do Brasil, ortografia atual. Termos técnicos consagrados em inglês podem ficar em inglês, em itálico na primeira ocorrência.

---

## Entregáveis ao final da Fase 3

1. `abntex/PI-monitoramento-sistemas/trabalho.tex` atualizado. Se preferir quebrar em arquivos separados via `\input{}`, justifique e documente.
2. `abntex/PI-monitoramento-sistemas/referencias.bib` atualizado se houver entradas novas.
3. Novos arquivos de figura em `abntex/img/` (com extensão e formato compatíveis com o que já existe no template).
4. Arquivo `CHANGES.md` na raiz do projeto contendo:
   - Resumo do que foi alterado, capítulo a capítulo.
   - Lista de **todas** as marcações `% TODO`, `% VERIFICAR`, `% CONDICIONAL` deixadas no texto, com path e linha.
   - Premissas que você assumiu sem confirmação minha.
   - Informações que ainda preciso fornecer (datas, dados de teste, política de IA, etc.).
5. **Compilação**: rode `make` em `abntex/PI-monitoramento-sistemas/` (ou o pipeline equivalente: `pdflatex` → `bibtex` → `pdflatex` × 2) e me mostre o resultado. Erros de compilação têm prioridade absoluta sobre qualquer outro entregável.

---

## O que NÃO fazer

- Não reescreva os Caps. 1–10. Aplique apenas os ajustes pontuais listados.
- Não gere conteúdo do Cap. 13 (Resultados) sem dados reais.
- Não inclua o Apêndice A no PDF final sem confirmação.
- Não execute `git commit` nem `git push` automaticamente. Apenas edite os arquivos.
- Não tente alterar a configuração de rede, DHCP, DNS ou nada fora do diretório do projeto.

---

## Começa pela Fase 1. Espera minha confirmação entre cada fase.