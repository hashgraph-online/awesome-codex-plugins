# Zenifra Codex Plugin

Plugin da Zenifra para usar projetos, deploys, builds, logs, metricas, envs e organizacoes pelo Codex.

Este plugin e uma camada fina sobre o CLI publico da Zenifra. Instale o CLI antes de instalar o plugin:

```bash
npm install -g @zenifra/cli
```

## Instalar no Codex

```bash
codex plugin marketplace add https://github.com/zenifra/zenifra-codex-plugin --ref main
codex plugin add zenifra@zenifra
```

Depois de instalar, abra uma nova sessao do Codex para que a skill `zenifra` seja carregada.

## Desenvolvimento local

Dentro do monorepo da Zenifra, voce pode usar o CLI local:

```bash
cd ../../../../zenifra-cli
npm link
```

Depois disso, use:

```bash
zenifra auth login --oauth
zenifra whoami --json
zenifra help project logs
zenifra auth login
zenifra auth api-key
zenifra auth logout --revoke
zenifra orgs
zenifra org set
zenifra projects --type http --page 1 --limit 15
zenifra plans --type jobs --json
zenifra create project --name app-http-autoscaling --plan premium --payment-mode hourly --config @examples/http-autoscaling-project.json
zenifra create project --name nightly-report --plan job-basic --payment-mode per_minute --config @job-config.json --idempotency-key <key>
zenifra project info --project <project-id>
zenifra project url --project <project-id>
zenifra project stop --project <project-id>
zenifra project resume --project <project-id>
zenifra project delete --project <project-id> --yes
zenifra project logs --project <project-id>
zenifra project metrics --project <project-id>
zenifra project network --project <project-id> --view summary
zenifra project image set --project <project-id> --image <image>
zenifra project envs --project <project-id>
zenifra project env add --project <project-id> --name <name> --value <value>
zenifra project env update --project <project-id> --name <name> --value <value>
zenifra project env remove --project <project-id> --name <name>
zenifra project autoscaling --project <project-id>
zenifra project autoscaling set --project <project-id> --min 2 --max 8 --cpu 70 --memory 80
zenifra project autoscaling disable --project <project-id>
zenifra project autoscaling events --project <project-id> --direction scale_up --page 1 --limit 10
zenifra project billing usage --project <project-id> --from 2026-06-01T00:00:00Z --to 2026-06-02T00:00:00Z --page 1 --limit 20 --json
zenifra project runs --project <project-id> --page 1 --limit 20 --json
zenifra project runs logs --project <project-id> --run <run-id>
zenifra project runs cancel --project <project-id> --run <run-id>
zenifra project instances --project <project-id>
zenifra project instances set --project <project-id> --count <n>
zenifra project github --project <project-id>
zenifra project github deploy-settings set --project <project-id> --mode tag --tag-pattern 'v*'
zenifra builds --project <project-id>
zenifra builds logs --project <project-id> --build <build-id>
zenifra builds logs --project <project-id> --build <build-id> --follow
zenifra deploy --project <project-id> --branch main
zenifra deploy watch --project <project-id> --build <build-id>
zenifra deployments --project <project-id>
```

Use `zenifra project logs` para logs da aplicacao rodando e `zenifra builds logs` para logs do build GitHub. `zenifra deploy` retorna um `build_id`, e `zenifra deploy watch` usa esse `build_id` para acompanhar status e logs incrementais em tempo real ate o fim do build. Nos logs de build, `event` identifica um evento detalhado e `summary` identifica o resumo terminal de compatibilidade, que pode ter apenas uma linha.

## Deploys GitHub por branch, tag ou release

As configuracoes de deploy automatico por versao exigem uma versao publicada de `@zenifra/cli` 0.4.0 ou superior. Instalar este plugin nao instala nem atualiza o CLI. Antes de configurar, confirme que o CLI instalado oferece `zenifra project github` com `zenifra help project github`.

Leia primeiro o repositorio, a branch e o modo atuais com `zenifra project github --project <project-id>`. A criacao do projeto sempre inicia o build inicial a partir da branch selecionada; o modo escolhido controla os gatilhos dos eventos futuros. O wizard oferece os mesmos quatro modos exclusivos que a configuracao de um projeto existente:

- `manual`: nao inicia builds automaticamente por pushes de branch, tags ou releases. O deploy manual com `zenifra deploy --project <project-id> --branch <branch>` continua disponivel.
- `branch`: inicia builds automaticamente para pushes na branch configurada; tags e releases nao iniciam builds.
- `tag`: inicia builds quando uma tag e criada e o nome dela corresponde a `--tag-pattern`.
- `release`: inicia builds quando uma release e publicada e sua tag corresponde a `--tag-pattern`. Pre-releases ficam excluidas por padrao; incluir pre-releases requer a opcao `--include-prereleases true` e autorizacao explicita do usuario.

Escolha uma unica opcao. `--tag-pattern` e obrigatorio para `tag` e `release` e nao se aplica a `manual` ou `branch`. Ele compara o nome da tag, aceita um nome exato ou os curingas `*` e `?`, e nao e uma regex nem compara o titulo da release. `--include-prereleases` so se aplica a `release` e assume `false` quando omitido. Use o modo e o padrao explicitamente informados pelo usuario sem pedir confirmacao redundante; esclareca somente entradas ausentes ou ambiguas. Incluir pre-releases exige pedido explicito. Antes de alterar um projeto de producao, confirme que o escopo do usuario identifica o perfil, a API efetiva, a organizacao e o projeto. Uma mudanca de modo altera quais eventos futuros do repositorio iniciarao builds.

```bash
zenifra project github deploy-settings set --project <project-id> --mode manual
zenifra project github deploy-settings set --project <project-id> --mode branch
zenifra project github deploy-settings set --project <project-id> --mode tag --tag-pattern 'v*'
zenifra project github deploy-settings set --project <project-id> --mode release --tag-pattern 'v*' --include-prereleases false
```

Depois da alteracao, leia `zenifra project github --project <project-id>` para conferir o modo efetivo. A configuracao de um gatilho nao prova que um build ou deploy futuro concluiu; quando um evento correspondente ocorrer, acompanhe o build e confirme o estado final do projeto.

Antes de uma mutacao, use `zenifra whoami --json` para conferir o perfil efetivo, a API, o modo de autenticacao e a organizacao ativa sem exibir credenciais. Em seguida, confirme o plano, o pagamento, o tipo de projeto, o dominio e o metodo de deploy. Depois da chamada, leia o estado final, a URL e o build/deployment; uma resposta aceita nao prova que o projeto esta pronto.

O catalogo humano de planos mostra as capacidades anunciadas. Para automacao, `zenifra plans --json` preserva a resposta publica; confira campos como `capabilities.logs`, `capabilities.metrics` e `capabilities.healthcheck` em vez de deduzir acesso pelo preco ou pela descricao do plano.

Use `zenifra project stop --project <project-id>` e `zenifra project resume --project <project-id>` para controlar o estado do projeto. Para excluir, leia primeiro o projeto e, imediatamente antes da remocao, mostre expressamente ao usuario o nome, ID, tipo, organizacao selecionada, API efetiva e URL publica quando existir. Informe que a exclusao do projeto e destrutiva e solicite uma resposta afirmativa, explicita e inequivoca para aquele alvo. Uma autorizacao generica anterior nao vale como confirmacao. Somente depois dessa resposta use `zenifra project delete --project <project-id> --yes`; sem `--yes`, a CLI nao envia a solicitacao de remocao. Valide o estado final depois.

Projetos criados por imagem OCI passam a ter um historico inicial de deployment. Consulte-o com `zenifra deployments --project <project-id>` e continue distinguindo projeto criado, build concluido, deployment concluido e aplicacao pronta.

Jobs agendados usam planos `job-*`, cobranca `per_minute`, uma imagem OCI pronta e cron de cinco campos em UTC. Eles nao possuem URL publica, porta, exposicao ou instancias. No CLI V1, use somente `zenifra plans --type jobs [--json]`, `zenifra create project ... --plan <job-plan> --payment-mode per_minute --config @<job-config.json> --idempotency-key <key>`, `zenifra project info --project <project-id>`, `zenifra project runs --project <project-id>`, `zenifra project runs logs --project <project-id> --run <run-id>` e `zenifra project runs cancel --project <project-id> --run <run-id>`. Esse fluxo aceita apenas `config.image`; `config.envs` e obrigatorio: use `envs: []` quando nao houver variaveis ou um array de objetos `{name, value}`, sem omitir o campo. Nao use `config.github`, `job.command` ou `job.args` no CLI V1. Para GitHub ou comandos/argumentos explicitos, use a API avancada documentada, sem inventar flags ou comandos do CLI.

`billed_minutes` e a duracao arredondada para cima, com minimo de 1 e maximo de 60 minutos. `price_per_minute`, `amount` e `total_amount` sao numeros em centavos de BRL e podem ser fracionarios; preserve o JSON para manter a precisao; apresentacoes humanas podem usar ate seis casas decimais para o preco por minuto e ate quatro para valores e totais. O valor terminal e calculado pelos minutos faturados vezes a tarifa vigente e armazenado exato, sem arredondamento para cima (uma execucao de R$ 0,0005 e guardada como `amount: 0.05`), com a tarifa aplicada. A duracao conta do inicio ao fim reais do container: agendamento e download da imagem nao sao cobrados. O custo do ciclo soma os valores persistidos, nao recalcula pelo catalogo atual.

`project runs` e os logs/metricas publicos mostram somente o ciclo de cobranca atual. Leia logs com a permissao `project.logs.read` e metricas com `project.metrics.read`. Se a capacidade estiver indisponivel no catalogo ou na resposta, trate-a como indisponivel e nao invente uma rota; quando uma rota existente responder `403`, a capacidade existe, mas o principal nao tem a permissao correspondente. A API `GET /v1/project/:id/job-runs/cost-summary` (permissao `project.billing.read`) expoe `total_amount`, `executed_runs`, `billed_minutes`, `cycle_started_at` e `next_reset_at`; o CLI nao tem um comando equivalente. A reinicializacao ocorre na data agendada, independentemente da liquidacao financeira; uma execucao que atravessa a virada continua no ciclo em que comecou. Registros internos de execucao e metricas antigas permanecem retidos, enquanto o uso persistido e os registros financeiros permanecem disponiveis para auditoria e nao sao apagados pelo reinicio do ciclo publico. Depois que o uso terminal e materializado, o custo terminal aparece antes da liquidacao financeira. Nao ha execucoes paralelas nem retry automatico; codigo de saida `0` significa sucesso e qualquer codigo nao zero, inclusive `1`, significa falha. O cancelamento permite ate 30 segundos para encerramento gracioso e somente depois solicita limpeza forcada. O CLI nao oferece comando de cost-summary nem de alteracao do cron; use a API/Console documentada para esses dados.

Para dominios personalizados, mantenha o dominio principal separado e aguarde DNS/TLS antes de concluir. Para MCP, use a URL completa terminada em `/mcp`, confira a descoberta do recurso e aceite `401` como o desafio esperado antes do OAuth.

O servidor MCP publica tools como `get_context`, `list_projects`, `get_project_logs`, `get_build_logs`, `get_project_network`, `get_project_health`, `get_project_autoscaling`, `get_valkey_status` e `list_ai_keys`. Alguns clientes exibem o nome do servidor como prefixo; com o servidor `zenifra`, `get_context` pode aparecer como `zenifra_get_context`. Nao adicione novamente o namespace do servidor a uma tool que ja o contenha. Consulte primeiro o contexto e o tipo do projeto; liste instancias antes de filtrar metricas ou logs, e liste builds antes de pedir os logs de um build.

Use `zenifra database status`, `zenifra database connection` e `zenifra database credentials rotate` para PostgreSQL, MariaDB, ClickHouse, Key Value, Cache e Queue. As conexoes permanecem mascaradas. Ao renovar a credencial, use `--connection-file <path>` em um destino privado; o arquivo e criado com modo 600 e, em Key Value, Cache e Queue, preserva exatamente a string retornada pelo backend. Nao inclua a conexao em mensagens, logs ou commits.

Se voce rodar comandos incompletos como `zenifra deploy`, `zenifra deploy watch` ou `zenifra builds` sem os argumentos obrigatorios, a CLI agora mostra a ajuda especifica do comando em vez de apenas um erro curto.

Ao criar projetos HTTP via `zenifra create project`, configs nao interativas devem declarar `exposure`: `public` cria rota/dominio publico e `private` cria a aplicacao sem exposicao na internet.

Para criar um projeto HTTP pago com auto-scaling, use `config.instances` como o minimo inicial e `config.autoscaling.max_instances` como o limite maximo. Os alvos opcionais de CPU e memoria devem ficar entre 1 e 100, e `enabled` deve ser `true`. O recurso nao se aplica a planos `free` nem a projetos que nao sejam HTTP; o wizard so o oferece quando o plano permite auto-scaling.

Use `zenifra project billing usage` para consultar, sem alterar o projeto, o consumo horario consolidado de computacao e armazenamento. Os filtros `--from` e `--to` aceitam datas ISO; `--page` e `--limit` controlam a paginacao, com limite maximo de 50; `--json` preserva a resposta estruturada para automacao. Essa consulta financeira e distinta das operacoes de configuracao e historico de auto-scaling.

## Login OAuth e organizacoes

Enderecos em `example.test` sao ficticios; substitua pela API autorizada do seu ambiente.

O login OAuth e da conta do usuario, nao de uma organizacao especifica. Selecione a organizacao uma vez; a escolha fica salva no perfil:

```bash
zenifra auth login --oauth --profile staging --api-base https://api.example.test/v1
zenifra orgs
zenifra org set --org <organization-id>
zenifra projects
zenifra create project
```

Com apenas uma organizacao disponivel, o CLI a seleciona automaticamente quando necessario. Para usar outra apenas em um comando, passe `--org <organization-id>`. Um novo login OAuth limpa a selecao anterior desse perfil.

O consentimento exige leitura e permite aprovar escrita explicitamente. Use `--read-only` para solicitar somente leitura. `--no-browser` imprime o endereco, mas o navegador precisa estar na mesma maquina da CLI ou conseguir alcancar o callback temporario de loopback dessa maquina. Em um servidor remoto onde isso nao e possivel, use uma API key da organizacao ou conclua o login em uma maquina onde o callback seja alcancavel. As permissoes atuais do usuario em cada organizacao continuam valendo; OAuth nao concede novos cargos ou acessos.

A renovacao da sessao e automatica. Cada perfil OAuth pertence a uma API: use perfis separados para ambientes diferentes. `ZENIFRA_API_KEY` continua tendo prioridade e o CLI avisa quando ela substitui a autenticacao OAuth. A confirmacao final de login aparece no terminal.

## Configuracao

- API padrao: `https://api.zenifra.com/v1`
- Override: `ZENIFRA_API_URL=https://api.example.test/v1`
- Timeout padrao de cada request HTTP: cinco minutos (`ZENIFRA_HTTP_TIMEOUT_MS=300000`)
- Perfis locais: `~/.config/zenifra-cli/profiles.json`
- Override de sessao: `ZENIFRA_CONFIG_DIR=/path/custom`

Todos os comandos de listagem aceitam `--json`. `zenifra projects` e paginado; use `--page <n>` e `--limit <n>` para navegar sem carregar todos os projetos.
Cada comando aceita `--help` e tambem pode ser consultado com `zenifra help <command>`.
Valores de envs sao mascarados por padrao; use `--show-values` somente quando o valor completo for necessario.
`zenifra auth logout` remove apenas a autenticacao local. Em um perfil OAuth, `--revoke` revoga somente aquela conexao. Em um perfil de login por senha, `--revoke` invalida as sessoes do usuario no servidor. API keys sao revogadas pela organizacao.

## Uso pelo Codex

O plugin contem a skill `zenifra`, que orienta o Codex a usar:

```bash
zenifra <command>
```

ou, como fallback dentro deste workspace:

```bash
node ../../../../zenifra-cli/bin/zenifra.mjs <command>
```

## Deploys a partir do Forgejo

Para uso normal, o fluxo Forgejo exige `@zenifra/cli` 0.5.0 ou posterior; instalar o plugin nao instala nem atualiza o CLI. Confira a ajuda dos comandos instalados antes de usa-los. Mantenha projetos GitHub no fluxo `zenifra project github` e use `project source` apenas quando a origem retornada identificar `provider_id` como `forgejo`.

Conecte ou gerencie a credencial Forgejo pelo Console com uma sessao interativa do owner. A CLI nao cria, rotaciona ou revoga esses tokens, e uma API key da organizacao ou sessao delegada nao substitui o owner. Nunca passe o token em argumentos, arquivos de configuracao, variaveis de ambiente, logs ou mensagens. Para deploy manual, o token precisa ler o repositorio. Para triggers automaticos, a conta precisa administrar hooks e o token precisa de `write:repository`; no Forgejo 16, tokens **Specific repositories** nao administram hooks. Use uma identidade dedicada com acesso somente aos repositorios necessarios e sem permissao de administrador da instancia. O [guia Forgejo completo](skills/zenifra/references/forgejo.md) explica os escopos e verificacoes.

Use uma conexao ativa e resolva um caminho `owner/repository` explicitamente. Reaproveite os IDs opacos retornados em `source.connection_id` e `source.repository_id` no JSON de criacao. O wizard interativo cobre OCI e GitHub; para Forgejo, crie a aplicacao HTTP com `--config` e os campos de origem/build documentados. Os quatro modos sao `manual`, `branch`, `tag` e `release`; pre-releases ficam desabilitadas por padrao e exigem pedido explicito.

```bash
zenifra git providers --json
zenifra git runtimes --json
zenifra git connections --json
zenifra git repositories resolve --connection <connection-id> --path <owner/repository> --json
zenifra git branches --connection <connection-id> --repository <opaque-repository-id> --json
zenifra project source deploy-settings set --project <project-id> --mode release --tag-pattern 'v*' --include-prereleases false --json
zenifra deploy --project <project-id> --commit-sha <full-commit-sha>
zenifra deploy watch --project <project-id> --build <build-id>
```

Compare o SHA reportado pela build com o commit pretendido, depois confira a URL e o comportamento esperado da aplicacao. Uma conexao validada ou uma build bem-sucedida, sozinha, nao comprova a entrega do webhook nem a disponibilidade da aplicacao.

## Marketplace do Codex

Este repositorio ja inclui `.agents/plugins/marketplace.json`, entao pode ser usado diretamente como marketplace Git pelo `codex plugin marketplace add`.
